<!-- specs/F-028-rechazo-manual/design.md -->
# F-028 · Rechazar un parte aprobado a mano, y quitar los espacios de los códigos — Diseño

> Los requisitos están en `requirements.md`. Aquí van las decisiones, con su
> alternativa descartada al lado. Rigor `estandar`.
>
> **Dos asuntos independientes en una feature.** Se diseñan por separado —§2 a
> §8 el rechazo, §9 los espacios— y se implementan en bloques que no se cruzan.
> Lo único que los une es §10: comprobar que el arreglo de los espacios **no
> mueve la huella de F-026**.

---

## 1 · Lo que ya está hecho, y por eso esta feature es pequeña

F-026 dejó la revocación **modelada y funcionando**, solo que sin gesto humano:

| Pieza | Estado | Qué falta |
|---|---|---|
| `Aprobacion.revocada_at_utc` / `revocada_motivo` | **Existe** | dos columnas más: quién y su nota |
| `esta_vigente()`, `admite_circuito()` | **Existe** | nada |
| `puede_archivarse` / las tres puertas del backend | **Existe** | nada |
| `MotivoRevocacion` | **Existe**, con un solo valor automático | un valor nuevo: la retirada humana |
| `revocar_aprobacion_si_cambio` (automática) | **Existe** | una sentencia hermana para la retirada |
| Endpoint y botón | **No existen** | esta feature |
| Histórico de decisiones | **No existe**, y volver a aprobar borra el rechazo | esta feature (§5) |

**La consecuencia de diseño**: el rechazo **no inventa un mecanismo nuevo**.
Escribe la misma revocación que ya existe, con otro motivo y con autor.

---

## 2 · D-A · El rechazo se registra al lado, como la aprobación

Misma regla que gobierna F-026 (su R11): **al lado, nunca encima**. El rechazo
no toca `postventa.validaciones` ni `ResultadoValidacion`; marca revocada la
fila de `postventa.aprobaciones` y **conserva** `aprobado_por` y
`aprobado_at_utc`. Un parte rechazado vuelve a ser exactamente lo que era —no
apto, con sus motivos— porque nunca dejó de serlo: lo único que se retira es el
permiso que una persona había dado.

**Alternativa descartada**: borrar la fila. Sería más corto y perdería el dato
que la feature existe para registrar (F-026 R33).

---

## 3 · D-B · Un motivo nuevo, cerrado, y la nota en columna aparte

```python
class MotivoRevocacion(str, Enum):
    VEREDICTO_CAMBIADO = "veredicto_cambiado"   # automático, F-026 R30
    RETIRADA_HUMANA = "retirada_humana"          # F-028: lo retiró una persona
```

El motivo sigue siendo **etiqueta corta y cerrada** (F-026 R34): es lo que la
pantalla traduce y lo que se puede agrupar en una consulta. El texto que
escriba quien rechaza va en **otra columna**, `revocada_nota`, y por tres
razones:

1. mezclarlo con el motivo convertiría un enumerado en un campo libre, y con él
   se acabaría el «agrupar por motivo»;
2. la nota es **opcional** (P2) y el motivo no puede serlo;
3. son dos cosas con distinto riesgo de contenido: el motivo lo escribe el
   código, la nota la escribe una persona.

**La nota se acota**: 500 caracteres, recortada por los extremos, y el vacío
equivale a ausente. No entra en ningún log (R39, R40). En la pantalla se
advierte —en el propio campo— que ahí no van datos del cliente: es texto de
quien revisa, no del papel.

---

## 4 · D-C · La puerta del cierre: qué es «ya no se puede rechazar»

**La puerta se pone en el cierre, no en el archivo** (P1, R9/R10):

| Estado del parte | ¿Se puede rechazar? | Por qué |
|---|---|---|
| Aprobado, sin archivar | **Sí** | no se ha escrito nada fuera |
| Archivado, sin cerrar | **Sí**, con aviso | el PDF sigue en SharePoint y el rechazo no lo borra; lo que impide es que se cierre |
| Cerrado (`cerrado` o `ya_cerrada`) | **No** | la reclamación ya está cerrada en producción y eso no se deshace desde aquí |
| Cierre en `error` o `dry_run_ok` | **Sí** | no hay nada escrito en el ERP |

Para saberlo hace falta **una lectura que hoy no existe** (§0.6 de
`requirements.md`): el puerto solo sabe leer el gráfico. Se añade **la lectura
más estrecha posible**, no una traza entera:

```python
# domain/ports/persistencia.py  (application ← domain)
def consultar_estado_cierre(self, *, hash_parte: str) -> str | None: ...
```

Devuelve el literal de `postventa.cierres.estado` o `None` si no consta cierre.
**Alternativa descartada**: `consultar_cierre() -> TrazaCierre | None`, simétrica
a `consultar_grafico`. Se descarta porque obliga a mapear once columnas para
mirar una, y el mapeo es código que nadie más usa. Si mañana hiciera falta la
traza entera, se amplía entonces.

El dominio aporta el predicado, para que el borde no compare cadenas a mano:

```python
# domain/models/aprobacion.py — dominio puro
ESTADOS_DE_CIERRE_EN_FIRME: tuple[str, ...] = ("cerrado", "ya_cerrada")

def puede_retirarse(aprobacion: Aprobacion | None, estado_cierre: str | None) -> bool
```

> Va en `aprobacion.py` y **no** en `cierre.py` a propósito: `cierre.py` es el
> módulo del ERP y F-026 lo dejó declarado como intocable (su R42 y §9.3). Lo
> que se necesita aquí no es lógica de cierre, es «¿esta decisión humana se
> puede retirar todavía?», que es de la aprobación. Los dos literales se
> comparan en un test contra el `CHECK` de `sql/06_cierres.sql`, con el patrón
> de `test_f026_ddl_aprobaciones.py`: si mañana el `CHECK` gana un estado y
> este dominio no se entera, rompe la suite y no producción.

---

## 5 · D-D · La bitácora: por qué hace falta una tabla más (P4)

El criterio de aceptación de la ficha dice: *«Un parte rechazado se puede
volver a aprobar, y la traza conserva las dos decisiones en orden»*. **Hoy eso
es imposible**: `upsert_aprobacion` pone las dos columnas de revocación a `NULL`
al volver a aprobar, y la clave primaria es `hash_parte`, así que solo hay una
fila (§0.4 de `requirements.md`).

Se añade **una tabla append-only** que no sustituye a nada:

- `postventa.aprobaciones` sigue siendo **el estado presente** —una fila por
  parte, F-026 R17 intacto—, que es lo que leen el endpoint y las tres puertas;
- `postventa.decisiones_aprobacion` es **el histórico**: una fila por decisión,
  que nadie actualiza ni borra.

Es el mismo reparto que ya usan `archivos`, `cierres` y `graficos` —estado
presente en su tabla— y no se parece a ninguno de ellos en una cosa: aquí el
histórico importa porque lo que se registra es **quién decidió qué y cuándo**,
que es el motivo entero de F-026.

Se escribe una fila en **tres** momentos, y los tres pasan por el repositorio:

| Momento | `decision` | `autor_oid` |
|---|---|---|
| `POST /api/aprobar` | `aprobada` | quien aprueba |
| `POST /api/rechazar` | `retirada` | quien rechaza |
| Revocación automática (`guardar_validacion`, F-026 R30) | `revocada_automatica` | `NULL` — no la decidió nadie |

> **La tercera es la que más cuesta y la que más vale.** La revocación
> automática ocurre dentro de una operación que hoy escribe dos sentencias
> (`upsert_validacion` + `revocar_aprobacion_si_cambio`) y pasa a escribir
> tres. Sin ella, el histórico contaría una película falsa: «aprobada,
> aprobada, aprobada» sin explicar por qué hubo que aprobar tres veces.
>
> **Coste que hay que declarar**: esa tercera fila se escribiría **en cada
> revalidación que cambie el veredicto**, y con el autoguardado de F-026 (R50)
> las revalidaciones son frecuentes. Por eso la sentencia se escribe
> **condicionada a que haya algo que revocar** —el mismo `WHERE` que ya lleva
> `revocar_aprobacion_si_cambio`: `huella_aprobada <> %s AND revocada_at_utc IS
> NULL`—, con `INSERT … SELECT … WHERE EXISTS`, de modo que un reproceso que no
> revoca **no escribe ninguna fila**.

**Alternativa descartada**: hacer `postventa.aprobaciones` append-only con
clave subrogada. Tocaría la clave primaria de una tabla ya desplegada, el
`ON CONFLICT` de F-026, `select_aprobacion`, la revocación automática y sus
tests, y dejaría a las tres puertas del backend teniendo que elegir fila. Es
una reescritura de F-026 para conseguir lo que una tabla nueva da sin tocarla.

---

## 6 · D-E · El endpoint: `POST /api/rechazar`

**Endpoint propio** (R18), como `/api/aprobar`: una petición, una decisión, una
fila de auditoría.

### Cuerpo

**Mucho más pequeño que el de aprobar**, y es deliberado:

```
hash_parte:  str    (obligatorio)
usuario_oid: str    (obligatorio; el oid opaco de Entra ID)
confirmado:  true   (obligatorio; el booleano de JSON, no la cadena)
nota:        str    (opcional, <= 500 caracteres)
```

`/api/aprobar` necesita el parte entero porque **recalcula el veredicto** y lo
guarda antes de aprobar (F-026 R5). Rechazar no recalcula nada: solo retira un
permiso que ya consta. Mandar la extracción entera sería mandar el DNI y las
observaciones del cliente para nada, y R19 lo prohíbe.

### Respuesta

```
{
  "hash_parte": "...",
  "resultado": "retirada|sin_cambios",
  "aprobacion": { "estado": "revocado", ... },
  "avisos": ["el parte ya consta archivado: el PDF sigue en SharePoint y el rechazo no lo retira"]
}
```

El bloque `aprobacion` es **el mismo** `bloque_de_aprobacion` que ya emiten
`/api/parte` y `/api/aprobar` (R22), ampliado con dos claves —`revocada_at_utc`
y `revocada_motivo`— para que la pantalla pueda distinguir quién la retiró de
por qué dejó de valer (R30). **Ni el `oid`, ni el correo, ni el nombre** (R28).
La `nota` **no sale** en la respuesta: quien la escribió ya la tiene delante y
la pantalla no la necesita para decidir nada; quien audite la lee en la base.

### Códigos (R20)

| Código | Cuándo |
|---|---|
| **200** | Retirada registrada, **o** ya estaba retirada (`sin_cambios`, R8) |
| **400** | Cuerpo mal formado, `hash_parte` o `usuario_oid` vacíos, `confirmado` ausente, nota demasiado larga |
| **409** | El parte **no consta aprobado** por nadie (`ParteNoRechazable`), o consta **cerrado** (R9) |
| **503** | `ConfiguracionPgIncompleta` o `PersistenciaNoDisponible` |

> **Por qué «ya estaba retirada» es 200 y no 409** (R8): dos pulsaciones
> seguidas son un dedo, no un error, y el estado final es exactamente el que se
> pedía. El `resultado` lo distingue, y no se escribe una segunda fila en la
> bitácora.
>
> **Por qué «no la aprobó nadie» sí es 409**: ahí no hay nada que retirar, y
> devolver 200 haría creer a quien llama que existía una aprobación.

`function_app.py` solo traduce, como los demás handlers, y el log lleva
`hash_parte` y resultado, y nada más (R40).

---

## 7 · D-F · La pantalla: el botón simétrico al de aprobar

Todo ocurre **en el detalle del parte** (R26), donde ya vive el botón de
aprobar, y con el PDF delante:

- **botón «Rechazar este parte»**, visible solo cuando `estaAprobado(parte)`;
- **campo de nota**, opcional, con su aviso de no escribir datos del cliente;
- **sin segunda confirmación** (R5, F-026 R29), igual que aprobar;
- **al volver**, `parte.aprobacion` pasa a `estado: "revocado"` y
  `semaforoDe(validacion, aprobacion)` devuelve el ámbar o el rojo de antes
  **sin tocar `pipeline.js`**: `aprobacionVale` ya exige `estado === "aprobado"`
  (§0.5 de `requirements.md`). La única puerta que se abrió, se cierra sola;
- **texto del estado** (R27, R30), dos redacciones distintas:
  - retirada humana → «Aprobación retirada por una persona · <fecha>»;
  - `veredicto_cambiado` → «La aprobación dejó de valer porque el veredicto
    cambió»;
- **si el parte consta cerrado** (R29), no se pinta el botón y en su lugar va la
  frase que lo explica. Y si aun así llegara la petición, el 409 se enseña tal
  cual: la puerta de verdad está en el backend, la pantalla solo evita el gesto
  inútil.

**Cómo sabe la pantalla que el parte está cerrado.** No hace falta ninguna
petición nueva: el front ya conoce el resultado de la tanda por parte (F-025
R16/R37, `parte.cerrado`). Se usa eso. **Alternativa descartada**: añadir el
estado de cierre a la respuesta de `/api/parte`; sería una lectura más por
parte —22 en una remesa real— para un caso que la pantalla ya sabe.

---

## 8 · Ficheros · asunto 1 (el rechazo)

### 8.1 · Ficheros a crear

| Ruta | Qué es | Capa |
|---|---|---|
| `services/postventa-api/infrastructure/persistencia/sql/11_decisiones_aprobacion.sql` | La bitácora append-only y su índice por parte y fecha | **infrastructure** · esquema propio |
| `services/postventa-api/infrastructure/persistencia/sql/12_aprobaciones_revocada_por.sql` | `ALTER TABLE … ADD COLUMN IF NOT EXISTS revocada_por, revocada_nota` sobre `postventa.aprobaciones` | **infrastructure** · esquema propio |
| `services/postventa-api/interface_adapters/api/rechazar.py` | Handler de `POST /api/rechazar` | **interface_adapters** |
| `services/postventa-api/tests/test_f028_rechazo_dominio.py` | `puede_retirarse`, el motivo nuevo, la nota acotada | tests |
| `services/postventa-api/tests/test_f028_rechazar_http.py` | El borde: cuerpo, códigos, idempotencia, log | tests |
| `services/postventa-api/tests/test_f028_persistencia.py` | Sentencias, mapeo y bitácora, con dobles | tests |
| `services/postventa-api/tests/test_f028_ddl_rechazo.py` | El **texto** del SQL: idempotente, cualificado, `ADD COLUMN IF NOT EXISTS`, `CHECK` contra los `Enum` | tests |
| `services/postventa-api/tests/test_f028_puertas.py` | Control negativo: un parte con la aprobación retirada no archiva, no adjunta y no cierra | tests |
| `services/postventa-front/tests_js/rechazo.test.js` | `cuerpoDeRechazo`, el semáforo tras la retirada | tests |
| `services/postventa-front/tests/test_f028_front.py` | Que la pantalla trae el botón, el campo de nota y los dos textos, y que **no** pinta ningún `oid` | tests |

### 8.2 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `domain/models/aprobacion.py` | `MotivoRevocacion.RETIRADA_HUMANA`, `ESTADOS_DE_CIERRE_EN_FIRME`, `puede_retirarse()`, `LIMITE_NOTA_REVOCACION`; `Aprobacion` gana `revocada_por` y `revocada_nota` (los dos `None` por omisión) |
| `domain/models/errores.py` | `ParteNoRechazable` (→ 409) |
| `domain/ports/persistencia.py` | `retirar_aprobacion`, `consultar_estado_cierre`, `registrar_decision`; la docstring de `guardar_validacion` recoge la fila de bitácora |
| `infrastructure/persistencia/sentencias.py` | `retirar_aprobacion`, `select_estado_cierre`, `insert_decision_aprobacion`; `_COLUMNAS_REVOCACION` y `_COLUMNAS_APROBACION` ganan las dos nuevas; `upsert_aprobacion` sigue poniendo la revocación a `NULL` y ahora también sus dos columnas nuevas |
| `infrastructure/persistencia/mapeo.py` | `fila_a_aprobacion` desempaqueta dos columnas más |
| `infrastructure/persistencia/repositorio_pg.py` | Implementa las tres operaciones nuevas; `guardar_validacion` añade la fila de bitácora condicionada |
| `interface_adapters/api/aprobacion_serializada.py` | El bloque gana `revocada_at_utc` y `revocada_motivo` (R30). **Sin `oid` y sin nota** |
| `interface_adapters/api/aprobar.py` | Escribe su fila de bitácora (`aprobada`) |
| `function_app.py` | Ruta `rechazar` (`POST`, `ANONYMOUS`, como las demás) y su traducción de errores |
| `services/postventa-front/js/api.js` | `rechazar(cuerpo, hash)` |
| `services/postventa-front/js/pipeline.js` | `cuerpoDeRechazo(parte, opciones)` y la lectura del motivo de revocación. **`aprobacionVale` no se toca** |
| `services/postventa-front/js/app.js` | `rechazarParte()`, `estaRetirada()`, `motivoDeRevocacion()`, `notaDeRechazo` en el estado |
| `services/postventa-front/index.html` | El botón, el campo de nota y los dos textos de R27/R30 |
| `docs/ARCHITECTURE.md` | R45 |
| `docs/INTEGRACION.md` y `azure-apps/postventa_incidencias.md` | R44 — **otro repositorio**, commit aparte y sin `push` |
| `specs/F-006-sharepoint/requirements.md` | El recuadro de enmienda de R8 (R42) |
| `specs/F-026-aprobacion-humana/requirements.md` | El recuadro de precisión de R34 (R43) |
| `harness/features.json` | Solo el estado de la feature, y lo mueve el líder |

### 8.3 · Ficheros que NO se tocan (los colindantes que tientan)

- **`domain/models/validacion.py`** y **`sql/04_validaciones.sql`** — ni una
  regla, ni una columna. El veredicto no se toca (F-026 R11, R48).
- **`domain/models/aprobacion.py::MOTIVOS_APROBABLES`** — qué es aprobable no
  cambia. F-028 retira aprobaciones, no amplía la puerta.
- **`huella_de_veredicto` y `_normalizar`** — §10 y P5.
- **`domain/models/cierre.py`** salvo `a_codigo_de_sigrid` (§9), e
  **`infrastructure/sigrid/escrituras.py`** — lo que se escribe en el ERP no
  cambia (F-026 R42).
- **`infrastructure/sharepoint/`** — rechazar no borra, no mueve y no renombra
  nada (R11).
- **`interface_adapters/api/archivar.py`, `adjuntar.py`, `cerrar.py`** — su
  contrato no cambia ni una clave; la puerta que ya miran se cierra sola.
- **`js/confirmacion.js`** — no hay confirmación nueva (R5).

### 8.4 · El SQL

**`sql/11_decisiones_aprobacion.sql`** (tabla nueva; `ficheros_ddl()` aplica los
`NN_nombre.sql` en orden lexicográfico, y `11` va después de `10`):

```sql
CREATE TABLE IF NOT EXISTS postventa.decisiones_aprobacion (
    decision_id  bigserial PRIMARY KEY,
    hash_parte   text        NOT NULL
                 REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    decision     text        NOT NULL
                 CHECK (decision IN ('aprobada', 'retirada', 'revocada_automatica')),
    autor_oid    text,
    decidida_at_utc timestamptz NOT NULL,
    motivo       text,
    nota         text
);

CREATE INDEX IF NOT EXISTS ix_decisiones_aprobacion_parte
    ON postventa.decisiones_aprobacion (hash_parte, decidida_at_utc);
```

- **`bigserial` y no `hash_parte` como clave**: el histórico acumula, ese es su
  oficio. Es la primera tabla del esquema que no va por parte, y la cabecera lo
  dice.
- **`autor_oid` admite `NULL`**: la revocación automática no la decidió nadie, y
  escribir ahí un `"sistema"` inventado sería un autor falso.
- **Ni una copia del texto manuscrito** (F-026 R15): `nota` es texto de quien
  revisa, y la cabecera lo advierte.
- **Ni una columna binaria**, como en las once anteriores.

**`sql/12_aprobaciones_revocada_por.sql`** (columnas sobre tabla existente):

```sql
ALTER TABLE postventa.aprobaciones
    ADD COLUMN IF NOT EXISTS revocada_por  text;
ALTER TABLE postventa.aprobaciones
    ADD COLUMN IF NOT EXISTS revocada_nota text;
```

Fichero aparte del `10_` a propósito: el `10_` describe la tabla tal y como
**ya está creada en la base real**, y reescribirlo dejaría un `CREATE TABLE`
que no coincide con lo que se ejecutó el día que nació. El patrón de este
proyecto es DDL idempotente **acumulativo**, no reescrito. Un test comprueba
que `10_aprobaciones.sql` **no cambia** en este trabajo.

> **Regla dura de `CLAUDE.md`**: las cuatro sentencias están cualificadas con
> `postventa.`, no hay una sola de ámbito de servidor y el `psql-albaranes-rs9k2`
> lo comparten otros proyectos. El test de texto lo vigila, con el patrón de
> `test_f005_ddl_idempotente_texto.py`.

---

## 9 · D-G · El arreglo de los espacios (asunto 2)

### 9.1 · Dónde va y por qué ahí

En **`domain/models/nombrado.py::normalizar_codigo`**, que es de quien heredan
las dos conversiones (§0.9 de `requirements.md`). Arreglarlo en
`a_codigo_de_sigrid` dejaría el nombre del fichero mal en el caso del guion con
espacio detrás, y haría exactamente lo que la docstring de esa función dice que
no se haga: dos criterios del mismo concepto.

### 9.2 · Las firmas

```python
# domain/models/nombrado.py — DOMINIO PURO (sin reloj, sin red, sin config)

#: Los dos caracteres que separan los tramos de un código.
SEPARADORES_DE_CODIGO = "/-"

def normalizar_codigo(bruto: str | None) -> str:
    """Guiones al normal, espacios colapsados, extremos recortados **y los
    espacios que flanquean a un separador, eliminados**."""

def tramos_de_codigo(codigo: str) -> tuple[str, ...]:
    """Los tramos de un código ya normalizado, sin los separadores y sin
    tramos vacíos: `RS26.09/0149` y `RS26.09-0149` dan los mismos dos."""
```

Implementación: tras la traducción de guiones y el colapso actual, una
sustitución con `re` —biblioteca estándar, ya usada en el dominio por
`pie_de_pagina.py`, así que **ninguna dependencia nueva** (R41)— que quita los
espacios pegados a `/` o `-`.

Y las dos conversiones pasan a expresarse **con los tramos**, que es lo que las
hace inversas exactas la una de la otra (R34):

| Función | Módulo | Pasa a ser |
|---|---|---|
| `nombre_de_archivo` | `domain/models/nombrado.py` | los tramos de la incidencia unidos por `SEPARADOR` (` - `) |
| `a_codigo_de_sigrid` | `domain/models/cierre.py` | los tramos del código unidos por `/` |

> **`a_codigo_de_sigrid` gana algo que hoy no hacía**: un código leído como
> `RS26.09-0149` —guion pegado, sin espacios— hoy sale **tal cual** y tampoco
> encuentra la reclamación; con los tramos sale `RS26.09/0149`. Es el mismo
> defecto de la misma familia, y se arregla gratis.
>
> **Lo que sigue igual**: el **código de obra no pasa por los tramos**. Solo se
> normaliza. Convertir sus guiones en separadores partiría `06-77` en una
> subcarpeta, y ahí sí se archivaría mal de verdad.

### 9.3 · La tabla de equivalencias que la feature promete

Después del arreglo, las seis formas producen **lo mismo** (y es el test que
fija R32 y R33):

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
  esperar `"RS26.08-0123"`, con su comentario y la cita de la enmienda (R42).
  **Es el único test existente que cambia de expectativa**, y el implementer
  tiene que decirlo en su informe: un test que cambia sin justificación escrita
  es un test aflojado.
- **No cambian** —y se comprueba que siguen en verde sin tocarlos—:
  `test_f006_r2_varias_barras_se_sustituyen_todas` (`A/B/C` sigue dando
  `0677 - A - B - C`), los siete guiones raros,
  `test_f006_r3_el_guion_raro_del_codigo_de_obra_tambien_se_normaliza`
  (`06–77` → `06-77`, la obra no pasa por los tramos), los ceros a la
  izquierda, el sufijo literal, `nombre_admisible`, y los dos de F-009
  (`RS26.08 - 0123` → `RS26.08/0123` y la idempotencia de la barra).

---

## 10 · D-H · La huella de F-026 no se mueve, y se prueba

Es un criterio de aceptación de la ficha, así que no basta con razonarlo: se
**fija con tests** (R37, R38).

1. **Control negativo del valor**: un juego de veredictos —incluidos los que
   traen el número con espacios alrededor de la barra— produce, después del
   cambio, **exactamente** las mismas huellas que antes. Las huellas esperadas
   se escriben en el test **literales** (el `sha256` en hexadecimal), no
   calculadas con la función que se está probando: una huella comparada consigo
   misma no prueba nada.
2. **Control negativo del acoplamiento**: `domain/models/aprobacion.py` **no
   importa** `domain.models.nombrado`, con el patrón del test de pureza de
   F-006 (`inspect.getsource`).
3. **Control negativo del efecto**: guardar dos veces la misma validación con el
   código escrito de dos formas distintas —`RS26.09/0149` y `RS26.09 / 0149`—
   hoy **sí** revoca, y después del cambio **sigue revocando igual**: el
   comportamiento no empeora ni mejora, que es justo lo que P5 propone.

> El punto 3 documenta un defecto latente de F-026 que **esta feature no
> arregla**: alinear las dos normalizaciones cambiaría las huellas ya escritas
> y revocaría aprobaciones vigentes (P5). Queda escrito para que la decisión se
> tome mirándolo, no por olvido.

---

## 11 · Riesgos

### 11.1 · La carpeta de archivo de un código de obra con guion espaciado

Si un código de obra se leyera como `06 - 77`, hoy la carpeta sería
`<base>/06 - 77` y después del cambio `<base>/06-77`: **dos carpetas
distintas**. El riesgo es teórico —los códigos de obra reales son cuatro
dígitos (`0626`, `0677`)— y el efecto sería un archivo en una carpeta nueva, no
un fichero perdido ni un cierre equivocado. Se acepta y se declara; si el
humano quiere cero riesgo, la alternativa es aplicar el arreglo **solo al número
de incidencia**, a costa de tener dos normalizaciones otra vez, que es la
divergencia que este arreglo existe para evitar.

### 11.2 · La bitácora crece con cada revalidación

Mitigado en §5: la fila de la revocación automática se escribe **solo si hay
algo que revocar**. Aun así, un parte que se apruebe y se rechace varias veces
acumula filas: es lo que se pide. Sin purga y sin retención declarada, porque
es auditoría de decisiones humanas y no dato de proceso.

### 11.3 · Rechazar un parte ya archivado deja el PDF en SharePoint

Declarado y avisado (R10). El PDF no se borra: la biblioteca de Posventa es un
archivo que se consulta a mano y borrar desde aquí es una escritura destructiva
en un sistema ajeno que nadie ha autorizado. El aviso de la respuesta y de la
pantalla lo dice con esas palabras.

### 11.4 · Dos asuntos en una rama

Si el humano decide partirla, el corte natural es: bloques 1–5 (rechazo) y
bloques 6–7 (espacios), que no comparten ni un fichero salvo la suite. El
segundo es el que **desbloquea un cierre que hoy falla en real**, así que si hay
que elegir por dónde empezar, se empieza por él.

---

## 12 · Encaje en la arquitectura y límite de microservicio

- **Dominio** (`domain/models/`): el motivo nuevo, `puede_retirarse`, la
  normalización y los tramos. Sin red, sin SQL, sin reloj. Es donde está el
  criterio, y por eso se prueba entero sin BBDD.
- **Puertos** (`domain/ports/`): tres operaciones más, expresadas en lenguaje de
  dominio; el handler nunca ve SQL.
- **Infraestructura** (`infrastructure/persistencia/`): las sentencias, el DDL
  acumulativo y el mapeo. Ni una sentencia fuera del esquema propio.
- **Borde** (`interface_adapters/api/`, `function_app.py`): traduce cuerpo,
  errores y códigos. No decide nada.
- **Front**: pinta y pide; toda regla que se pueda equivocar vive en
  `pipeline.js`, que tiene tests.

**Límite de microservicio**: la feature entera cabe en `postventa-api` y
`postventa-front`. **No toca Sigrid** —ni el estado, ni `dbo.log`, ni el
gráfico— y **no toca SharePoint**. Lo que se registra es una decisión humana
sobre un parte, que es exactamente el dominio de este servicio. Si en algún
momento apareciera la necesidad de **deshacer** un cierre en el ERP, eso **no
se implementa aquí**: es escritura de reversión en producción, la decide el
dueño del proceso y se marcaría `blocked` según `CLAUDE.md`.
