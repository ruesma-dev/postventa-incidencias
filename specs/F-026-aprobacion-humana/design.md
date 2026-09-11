<!-- specs/F-026-aprobacion-humana/design.md -->
# F-026 · Aprobación humana de los partes que van a revisión — Diseño

> Diseña contra `docs/ARCHITECTURE.md` (normativo) y `docs/CONVENTIONS.md`.
> Cada afirmación sobre el comportamiento actual va marcada **[MEDIDO]** con su
> fuente o **[INFERIDO]**. Las medidas están recogidas en `requirements.md` §0 y
> no se repiten aquí más que cuando deciden algo.

---

## 1 · Lo que pidió el responsable, y qué parte de eso decide el diseño

Literal, el 2026-09-11:

> «Los partes no aptos no se archivan hasta que no se aprueban por revisor
> humano. En ese momento pasan a aprobados y entrarían en el proceso normal.»

Y, preguntado por dónde debía vivir ese estado, frente a la alternativa de
tenerlo solo en el navegador:

> «hay que guardarlo»

El **motivo** de guardarlo, que es lo que da el rigor de la feature: un parte
llega a revisión porque la firma no parecía humana, o porque trae observaciones
manuscritas del cliente diciendo que la reparación no está bien
(`docs/referencia/02_parte_de_trabajo.md`: *«Se aprecia que se han hecho
parcheados. No se reparó la totalidad»*, sobre un parte **firmado**). Aprobarlo
es la decisión de una persona que **sobrescribe al sistema** en una incidencia
que acabará cerrada en el ERP de producción. Una decisión así no puede vivir en
una pestaña que se cierra.

Lo que la petición **no** decide, y decide esta spec con su justificación: qué
cuenta como «aprobar» (§12.3 y P1), qué motivos son aprobables (§4 y P2), y
cuándo una aprobación deja de valer (§7 y P4/P5).

---

## 2 · D-A · La aprobación se registra **al lado** del veredicto, nunca encima

La tentación evidente es que aprobar reescriba `postventa.validaciones`:
`veredicto = 'apto'`, `destino = 'archivo_y_cierre'`, y todo lo demás del
sistema sigue funcionando sin tocar una línea. **Se descarta**, por tres
motivos, y dos de ellos son medidos:

1. **No sobreviviría.** `upsert_validacion` hace `ON CONFLICT (hash_parte) DO
   UPDATE SET` sobre todas las columnas menos la clave
   (`infrastructure/persistencia/sentencias.py`, `_asignaciones(columnas,
   excluidas={'hash_parte'})`) **[MEDIDO]**, y `POST /api/parte` **recalcula
   siempre** el veredicto y lo vuelve a guardar (R8 de F-019, docstring de
   `interface_adapters/api/parte.py`) **[MEDIDO]**. La aprobación duraría hasta
   la siguiente revalidación.
2. **Mentiría.** El veredicto es lo que dicen las reglas de F-004 sobre los
   datos leídos. Escribir `apto` donde la máquina dijo `no_apto` borra el hecho
   —que hubo un motivo— y con él la razón por la que alguien tuvo que decidir.
3. **Haría indistinguibles** el verde de origen y el aprobado, que es justo lo
   que R36 prohíbe.

Por eso: **tabla propia**, y el veredicto de F-004 intacto. La consecuencia es
que las puertas que hoy miran sólo el veredicto pasan a mirar **dos cosas**, y
eso es §5.

---

## 3 · D-B · Qué es «el veredicto que se aprobó»: una huella

Para poder revocar (R30) hace falta comparar el veredicto de hoy con el que se
aprobó, y hacerlo **sin copiar la transcripción de las observaciones** (R15).

La pieza es una función pura del dominio que produce una **huella** del
veredicto:

```
huella_de_veredicto(validacion: ResultadoValidacion) -> str
```

Sobre una cadena canónica de cuatro cosas, en este orden fijo:

1. `destino.value`
2. los `codigo.value` de los motivos, **ordenados**
3. `clasificacion_firma.value`
4. las observaciones **normalizadas** (recortadas, espacios colapsados,
   minúsculas) o la cadena vacía

y se devuelve su `sha256` en hexadecimal. `ResultadoValidacion` transporta las
cuatro (`domain/models/validacion.py`) **[MEDIDO]**, así que la huella se puede
calcular en cualquier punto donde exista un veredicto y **sin ninguna consulta**.

Por qué entra el texto de las observaciones: F-004 no lo interpreta —cualquier
texto no vacío produce el mismo `CodigoMotivo.OBSERVACIONES_MANUSCRITAS`, y
juzgarlo es F-016— **[MEDIDO]**, así que sin él dos observaciones opuestas
darían la misma huella. Está razonado en **P4**.

Por qué **no** entran los valores de los campos: el nombrado cambia si cambia
el código de obra, pero eso no es lo que se aprobó; y los campos decisivos
ilegibles no son aprobables (§4), así que su cambio ya sale reflejado en los
motivos.

`sha256` sale de `hashlib`, de la biblioteca estándar: **cero dependencias
nuevas** (R45).

---

## 4 · D-C · Qué es aprobable: se decide por **motivo**, no por destino

`domain/models/aprobacion.py` declara:

```
MOTIVOS_APROBABLES = (
    CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
    CodigoMotivo.FIRMA_NO_HUMANA,
)

es_aprobable(validacion: ResultadoValidacion) -> bool
```

Verdadero si y solo si el parte **no** es apto, tiene al menos un motivo, y
**todos** sus motivos están en `MOTIVOS_APROBABLES`.

La justificación con F-004 delante:

| Motivo | ¿Aprobable? | Por qué |
|---|---|---|
| `observaciones_manuscritas` | **Sí** | Es literalmente el destino «hay algo que **decidir**»: la cola existe para que una persona lea la transcripción y resuelva. Aprobar **es** el acto que esa cola espera, y hoy no existe |
| `firma_no_humana` | **Sí** | F-004 clasifica `ilegible` ante cualquier duda a propósito, y degrada a `ilegible` una `humana` que no llega al umbral **[MEDIDO]**. Una persona con el PDF delante puede ver que sí es una firma: eso es **corregir a la máquina**, no saltarse la regla de que la firma debe ser humana |
| `codigo_obra_no_legible` | **No** | Sin código de obra no hay carpeta de archivo (`ARCHITECTURE.md`, semántica 8). No hay nada que decidir: hay algo que teclear |
| `numero_incidencia_no_legible` | **No** | Sin nº de incidencia no hay reclamación que cerrar ni fichero que nombrar (semántica 5), y `componer_destino` levanta `NombradoImposible` **[MEDIDO]**. Aprobarlo sería aprobar algo que va a fallar |

Consecuencia práctica de trazar la línea por motivo y no por destino: se pueden
aprobar partes de **los dos** destinos no aptos, pero **nunca** uno al que le
falte un dato decisivo. Un ámbar siempre es aprobable (su único motivo es el de
las observaciones, por construcción de `_destino()`) **[MEDIDO]**; un rojo lo es
sólo si todo lo que le pasa es la firma, las observaciones, o las dos.

---

## 5 · D-D · Las tres puertas del backend pasan a mirar dos cosas

Hoy, los tres pasos comprueban lo mismo **[MEDIDO]**:

```
ctx.validacion.veredicto != Veredicto.APTO or ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE
    -> ParteNoApto
```

en `paso_archivo.py::_exigir_apto`, `paso_grafico.py::_exigir_apto` y
`paso_cierre.py::_exigir_apto`. Pasan a ser:

```
admite_circuito(validacion, aprobacion) -> bool
```

una función **pura** del dominio, verdadera si:

- el parte es apto con destino `archivo_y_cierre` (lo de siempre), **o**
- hay aprobación, **no está revocada**, y su `destino_aprobado` coincide con el
  `destino` que declara la validación de esa petición.

Y **la aprobación se lee del repositorio dentro del paso**, nunca del cuerpo
(R24). El precedente exacto es `ContextoParte.traza_grafico`, cuya docstring ya
explica por qué: *«Viene de la base y **nunca del cuerpo de la petición**: si
viniera del cuerpo, quien llama podría afirmar que adjuntó algo que no
adjuntó»* **[MEDIDO]**. Aquí es idéntico cambiando «adjuntó» por «aprobó».

Los tres pasos ya reciben `repositorio: RepositorioPartesPort`
**[MEDIDO]**, así que **no cambia ninguna firma**: se añade una lectura y un
campo al contexto.

> **Por qué la puerta del paso compara el destino y no la huella.** El cuerpo de
> `POST /api/archivar` trae cinco campos y ninguno es personal (R29 de F-007)
> **[MEDIDO]**: `hash`, `codigo_obra`, `numero_incidencia`, `veredicto` y
> `destino`. No trae ni los motivos ni las observaciones, así que el paso **no
> puede** recomputar la huella, y ensancharle el cuerpo sería hacer viajar texto
> manuscrito que R45 de F-025 prohíbe.
>
> No hace falta: la vigencia **no se comprueba al leer, se resuelve al escribir**
> (§7). Cuando el paso lee la fila, ya está revocada si tenía que estarlo. La
> puerta del paso comprueba lo que sí puede: que exista una aprobación viva
> **para ese destino**.

---

## 6 · D-E · El endpoint: `POST /api/aprobar`

**Endpoint propio** (R18). No se extiende `POST /api/parte` porque guardar
ocurre en cada revalidación y aprobar es una decisión de una persona: una
petición, una decisión, una fila de auditoría. Es además el patrón del servicio
—un endpoint por escritura con consecuencias— y el que deja el log limpio.

### Cuerpo

El **mismo** que `POST /api/parte` —`remesa_id`, `parte`, `extraccion`,
`firma`, parseados por `interface_adapters/api/cuerpos.py`, que ya existen y no
se tocan— más dos claves propias:

```
usuario_oid: str   (obligatorio; el oid opaco de Entra ID)
confirmado: true   (obligatorio; el booleano de JSON, no la cadena)
```

Y **hace las dos cosas en una sola llamada**: guarda el parte y su validación
(reutilizando `paso_persistencia`, idempotente) y escribe la aprobación con la
huella de **ese mismo veredicto**.

> Por qué las dos juntas y no un endpoint fino que solo escriba la aprobación:
> entre «guardar la validación» y «aprobar» habría una ventana en la que lo
> aprobado y lo guardado pueden no ser lo mismo, y lo que se guardaría entonces
> es una aprobación de un veredicto que no está en la base. Haciéndolo junto, la
> huella aprobada es por construcción la del veredicto que acaba de escribirse.
> El veredicto **se recalcula aquí** con `validar_parte` (R5), igual que en
> `/api/parte`: nunca llega hecho desde fuera.

### Respuesta

```
{
  "hash_parte": "...",
  "resultado_parte": "creado|actualizado",
  "resultado_validacion": "creado|actualizado",
  "aprobacion": {
    "estado": "aprobado",
    "destino_aprobado": "cola_validacion_humana|revision_manual",
    "motivos_aprobados": ["observaciones_manuscritas"],
    "aprobado_at_utc": "2026-09-11T10:12:00+00:00"
  },
  "avisos": []
}
```

**Ni el `oid`, ni el correo, ni el nombre de quien aprobó salen en la
respuesta** (R38, R43): la pantalla no los necesita y quien audite los lee en la
base.

### Códigos (R20)

| Código | Cuándo |
|---|---|
| **200** | Aprobado |
| **400** | Cuerpo mal formado, `usuario_oid` vacío (R4), `confirmado` ausente |
| **409** | La remesa no consta (`ReferenciaNoConsta`, como `/api/parte`), o el veredicto **no es aprobable** (`ParteNoAprobable`, R9) — incluido el caso «ya es apto» (R10) |
| **503** | `ConfiguracionPgIncompleta` o `PersistenciaNoDisponible` |

`function_app.py` solo traduce, como los demás handlers **[MEDIDO]**, y el log
lleva `hash_parte`, destino y resultado, y nada más (R44).

### Y una clave más en `POST /api/parte`

`guardar_parte_http` añade a su respuesta el bloque `aprobacion` (o `null`),
leído del repositorio después de guardar (R22). Es lo que permite que, al volver
a subir la remesa, la pantalla sepa qué partes constan aprobados **sin una
petición por parte** (22 llamadas de más en una remesa real).

---

## 7 · D-F · La revocación ocurre **en la escritura**, no en la lectura

R30 dice que una aprobación deja de valer cuando el veredicto cambia. Hay dos
formas de conseguirlo, y la elección importa:

- **al leer**: cada vez que alguien consulta la aprobación, se compara con la
  validación vigente. Obliga a tener las dos delante en todos los sitios que
  miran —incluidos los tres pasos, que no pueden (§5)—, y deja filas «caducadas»
  que parecen vivas hasta que alguien las mira;
- **al escribir**: `guardar_validacion` recibe el `ResultadoValidacion` completo
  y, en la misma operación, **revoca la aprobación si su huella ya no es la de
  este veredicto**. Quien lee después ve la verdad sin tener que calcularla.

Se elige **al escribir**. Es una sentencia más en una operación que ya se
ejecuta en todos los caminos que cambian el veredicto —`POST /api/parte` y
`POST /api/aprobar`, los dos únicos— **[MEDIDO]**, y deja la puerta del paso
reducida a leer una fila.

La sentencia es un `UPDATE` condicionado por parámetros, sin nada interpolado:

```sql
UPDATE postventa.aprobaciones
   SET revocada_at_utc = %s, revocada_motivo = %s
 WHERE hash_parte = %s
   AND revocada_at_utc IS NULL
   AND huella_aprobada <> %s
```

**No borra** (R33): la decisión se tomó y quién la tomó sigue siendo
información. `revocada_motivo` es una **etiqueta corta y cerrada** —
`veredicto_cambiado`—, nunca el texto que la provocó (R34).

Volver a aprobar es un `upsert` que sustituye la fila y deja
`revocada_at_utc` a `NULL` (R17).

### Qué pasa en cada escenario

| Escenario | Qué ocurre | Requisito |
|---|---|---|
| Se aprueba, se confirma la tanda, se archiva y se cierra | El circuito normal, con su confirmación única | R23, R27 |
| Se aprueba y luego se **corrige un campo** y se revalida | Si el veredicto cambia → **revocada**; hay que volver a aprobar | R30, R31 |
| Se aprueba y se revalida **sin que cambie nada** | Sigue vigente | R32 |
| Se recarga la página y se **vuelve a subir la misma remesa** | Se reprocesa, se vuelve a guardar la validación; si la lectura da el mismo veredicto, **la aprobación sigue ahí** y la pantalla la enseña | R22, R32 |
| Se reprocesa y la IA lee **otra cosa** (otra firma, otra observación) | **Revocada**: nadie ha opinado sobre lo nuevo | R30 |
| Se aprueba un parte al que le falta el nº de incidencia | No se puede: `ParteNoAprobable`, 409 | R7, R9 |
| Alguien llama a `/api/archivar` con `destino: revision_manual` y sin aprobación | `ParteNoApto`, como hoy | R25 |

---

## 8 · D-G · La pantalla: un cuarto estado, no un verde más

`semaforoDe` devuelve hoy `"verde" | "ambar" | "rojo" | ""`
(`js/pipeline.js`) **[MEDIDO]**. Pasa a aceptar un segundo argumento —la
aprobación— y a devolver además `"aprobado"`.

- **marca propia**: el mismo punto verde **con anillo** (`ring-2`), no el verde
  liso. Un parte aprobado y uno que siempre fue verde no pueden leerse igual de
  un vistazo (R36);
- **texto al lado**, en la fila y en el detalle: «aprobado por revisión humana ·
  venía de <destino> · <fecha>» (R36, R37). **Sin el `oid`, sin correo y sin
  nombre** (R38);
- **botón** «Aprobar este parte», en el **detalle** y solo si el parte es
  aprobable (R35, R39). Con el PDF delante, que es donde se mira una firma;
- **cuando no es aprobable**, en vez del botón, la frase que dice qué corregir
  (R39);
- **sin confirmación** (R29, P7): el botón es el acto explícito, y la
  confirmación única de F-025 sigue siendo la única que precede a una escritura
  externa. `test_f025_r2_solo_se_arma_una_confirmacion_en_todo_el_front` sigue
  en verde sin tocarlo.

El selector de la tanda (`pendientesDeCircuito`) pasa a usar `esCirculable(parte)`
—apto **o** aprobado vigente— en vez de `esArchivable(parte.validacion)`, y lo
mismo `cuerpoDeArchivo`, `esCerrable` y `cuerpoDeGrafico`, que se niegan a
componer nada que no pase por ahí. `esArchivable` **se conserva con su
significado actual** («lo que la máquina dio por bueno»), porque lo usa
`noArchivables()` y porque la distinción es el requisito.

---

## 9 · Ficheros

### 9.1 · Ficheros a crear

| Ruta | Qué es | Capa |
|---|---|---|
| `services/postventa-api/domain/models/aprobacion.py` | `Aprobacion` (dataclass), `MOTIVOS_APROBABLES`, `MotivoRevocacion`, `es_aprobable`, `huella_de_veredicto`, `esta_vigente`, `admite_circuito` | **domain** · puro, sin red, sin SQL |
| `services/postventa-api/infrastructure/persistencia/sql/10_aprobaciones.sql` | La tabla `postventa.aprobaciones` y su índice | **infrastructure** · esquema propio |
| `services/postventa-api/interface_adapters/api/aprobar.py` | Handler de `POST /api/aprobar` | **interface_adapters** |
| `services/postventa-api/tests/test_f026_aprobacion_dominio.py` | Las reglas puras: aprobable, huella, vigencia, admisión | tests |
| `services/postventa-api/tests/test_f026_aprobar_http.py` | El borde: cuerpo, códigos, recálculo del veredicto, log | tests |
| `services/postventa-api/tests/test_f026_persistencia.py` | Sentencias, mapeo y revocación, con dobles | tests |
| `services/postventa-api/tests/test_f026_puertas.py` | Los tres pasos con y sin aprobación | tests |
| `services/postventa-api/tests/test_f026_ddl_aprobaciones.py` | El **texto** del `.sql`: idempotente, cualificado, `CHECK` contra los `Enum` | tests |
| `services/postventa-front/tests_js/aprobacion.test.js` | `esAprobable`, `esCirculable`, `semaforoDe`, `cuerpoDeAprobacion` | tests |
| `services/postventa-front/tests/test_f026_front.py` | Que la pantalla trae el botón, la marca y el texto, y que **no** pinta el `oid` | tests |

### 9.2 · Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/errores.py` | Añade `ParteNoAprobable` (→ 409) |
| `services/postventa-api/domain/models/persistencia.py` | Nada de la aprobación: vive en su propio módulo. **Solo** se amplía la nota de cabecera de datos personales con `Aprobacion.aprobado_por` |
| `services/postventa-api/domain/ports/persistencia.py` | `RepositorioPartesPort` gana `consultar_aprobacion` y `guardar_aprobacion`; la docstring de `guardar_validacion` recoge la revocación |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | `upsert_aprobacion`, `select_aprobacion`, `revocar_aprobacion_si_cambio` |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | `fila_a_aprobacion`, `json_de_codigos_de_motivo` |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | Implementa las dos operaciones nuevas; `guardar_validacion` ejecuta además la revocación |
| `services/postventa-api/application/pipelines/contexto_parte.py` | Campo `aprobacion: Aprobacion \| None`, con la docstring que diga que **viene del repositorio y nunca del cuerpo** |
| `services/postventa-api/application/pipelines/paso_archivo.py` | `_exigir_apto` → `_exigir_admitido`: lee la aprobación y llama a `admite_circuito` |
| `services/postventa-api/application/pipelines/paso_grafico.py` | Igual |
| `services/postventa-api/application/pipelines/paso_cierre.py` | Igual |
| `services/postventa-api/interface_adapters/api/parte.py` | La respuesta añade `aprobacion` (R22); `_AnotaLosResultados` delega las dos operaciones nuevas |
| `services/postventa-api/function_app.py` | Ruta `aprobar` (`POST`, `ANONYMOUS`, como las demás) y su traducción de errores |
| `services/postventa-front/js/pipeline.js` | `esAprobable`, `esCirculable`, `cuerpoDeAprobacion`, `semaforoDe` con aprobación, y `pendientesDeCircuito`/`cuerpoDeArchivo`/`esCerrable`/`cuerpoDeGrafico` pasando por `esCirculable` |
| `services/postventa-front/js/api.js` | `aprobar(cuerpo, hash)` |
| `services/postventa-front/js/app.js` | `aprobarParte()`, `esAprobable()`, y el estado del parte gana `aprobacion` **declarado en `_parteInicial`** (si no, Alpine no lo hace reactivo) |
| `services/postventa-front/index.html` | El botón en el detalle, la marca del semáforo y el texto de R36/R37 |
| `docs/ARCHITECTURE.md` | Los tres puntos de R47, precisados |
| `specs/F-025-confirmacion-unica/requirements.md` | El recuadro de enmienda fechado bajo R36 (R46) |
| `harness/features.json` | Solo el estado de la feature, y lo mueve el líder |
| `azure-apps/postventa_incidencias.md` | El endpoint nuevo y la tabla nueva (R49) — **otro repositorio**, commit aparte |

### 9.3 · Ficheros que NO se tocan (los colindantes que tientan)

- **`domain/models/validacion.py`** — ni una regla de F-004. Si aquí cambia
  algo, la feature se ha ido de alcance (R11, R48).
- **`infrastructure/persistencia/sql/04_validaciones.sql`** — ni una columna. El
  argumento está en §2, y evitar el `ALTER TABLE` sobre una tabla del servidor
  compartido es un beneficio, no un accidente.
- **`interface_adapters/api/cola.py`** y **`sentencias.py::select_cola`** — la
  cola sigue sirviendo lo que sirve. Filtrar de ella los ya aprobados es una
  mejora razonable y **no es esta feature**.
- **`interface_adapters/api/validar.py`** — `/api/validar` no guarda nada y no
  tiene por qué saber de aprobaciones.
- **`domain/models/cierre.py`** y **`infrastructure/sigrid/escrituras.py`** —
  R42: lo que se escribe en el ERP no cambia.
- **`js/confirmacion.js`** — R29: no hay confirmación nueva.
- **`interface_adapters/api/archivar.py`, `adjuntar.py`, `cerrar.py`** — su
  contrato de cuerpo **no cambia ni una clave**. Lo que cambia está dentro de
  los pasos.

---

## 10 · El SQL

`services/postventa-api/infrastructure/persistencia/sql/10_aprobaciones.sql`.
Entra solo: `ficheros_ddl()` aplica los `NN_nombre.sql` en orden lexicográfico
y `10` va después de `09` **[MEDIDO]**.

```sql
CREATE TABLE IF NOT EXISTS postventa.aprobaciones (
    hash_parte        text PRIMARY KEY
                      REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    aprobado_por      text        NOT NULL,
    aprobado_at_utc   timestamptz NOT NULL,
    destino_aprobado  text        NOT NULL
                      CHECK (destino_aprobado IN ('cola_validacion_humana', 'revision_manual')),
    motivos_aprobados jsonb       NOT NULL DEFAULT '[]',
    huella_aprobada   text        NOT NULL,
    validado_at_utc   timestamptz NOT NULL,
    revocada_at_utc   timestamptz,
    revocada_motivo   text
);

CREATE INDEX IF NOT EXISTS ix_aprobaciones_vigentes
    ON postventa.aprobaciones (aprobado_at_utc)
    WHERE revocada_at_utc IS NULL;
```

Lo que decide cada cosa, y va escrito en la cabecera del fichero como en los
nueve anteriores:

- **`hash_parte` clave primaria y clave ajena**: una sola aprobación por parte
  (R17) y ninguna aprobación de un parte que no consta guardado. Es la misma
  restricción que sostiene F-019 y por el mismo motivo.
- **`aprobado_por` es dato personal seudónimo**: el `oid` opaco de Entra ID y
  nunca el correo, el nombre ni el login del ERP (R13). Mismo tratamiento y
  misma nota que `cierres.confirmado_por` y `graficos.confirmado_por`.
- **`destino_aprobado` con `CHECK`**, y **solo los dos no aptos**: aprobar un
  `archivo_y_cierre` no significa nada (R10). Los literales son los que emite
  `Destino` y un test los compara con el `Enum`, con el patrón de
  `tests/test_f005_ddl_idempotente_texto.py` **[MEDIDO]**: una etiqueta nueva en
  el dominio que no llegue a la base rompe la suite, no producción.
- **`motivos_aprobados` guarda códigos, no textos**: `["firma_no_humana"]`. El
  texto del motivo es redacción para Posventa y puede cambiar; el código es
  contrato (F-004).
- **`huella_aprobada`**: §3. Es un `sha256` hexadecimal, así que **no lleva
  dentro ni una letra del texto manuscrito** (R15).
- **`validado_at_utc`**: qué validación se aprobó. Es traza, no criterio: quien
  decide la vigencia es la huella (P5).
- **`revocada_at_utc` / `revocada_motivo`**: §7. `NULL` es «vigente», y el
  índice parcial indexa solo eso, que es lo único que se consulta —mismo patrón
  que `ix_validaciones_cola` **[MEDIDO]**.
- **Ni una columna binaria** y **ni una copia del texto manuscrito**: las dos
  prohibiciones que `ddl.py` y la cabecera de `04_validaciones.sql` ya imponen.

---

## 11 · Las firmas que importan

### `domain/models/aprobacion.py` — dominio puro

```python
MOTIVOS_APROBABLES: tuple[CodigoMotivo, ...]

class MotivoRevocacion(str, Enum):
    VEREDICTO_CAMBIADO = "veredicto_cambiado"

@dataclass(frozen=True)
class Aprobacion:
    hash_parte: str
    aprobado_por: str            # oid opaco, nunca correo ni nombre
    aprobado_at_utc: datetime
    destino_aprobado: Destino
    motivos_aprobados: tuple[CodigoMotivo, ...]
    huella_aprobada: str
    validado_at_utc: datetime
    revocada_at_utc: datetime | None = None
    revocada_motivo: str | None = None

def es_aprobable(validacion: ResultadoValidacion) -> bool: ...
def huella_de_veredicto(validacion: ResultadoValidacion) -> str: ...
def esta_vigente(aprobacion: Aprobacion | None) -> bool: ...
def admite_circuito(
    validacion: ResultadoValidacion | None,
    aprobacion: Aprobacion | None,
) -> bool: ...
```

`admite_circuito(None, …)` es **falso**: «no hay veredicto» sigue siendo un
motivo propio y distinto de «el veredicto dice que no», como ya distinguen los
tres `_exigir_apto` de hoy **[MEDIDO]**.

### `domain/ports/persistencia.py`

```python
def guardar_aprobacion(self, *, aprobacion: Aprobacion) -> ResultadoGuardado: ...
def consultar_aprobacion(self, *, hash_parte: str) -> Aprobacion | None: ...
```

`None` **no es un error**: es que a ese parte no lo ha aprobado nadie. La
docstring de `guardar_validacion` recoge además que **revoca** la aprobación
cuya huella ya no coincide (R30), porque es parte de su contrato y quien
implemente el puerto tiene que saberlo.

### `interface_adapters/api/aprobar.py`

```python
def aprobar_parte_http(
    cuerpo: Any,
    *,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]: ...
```

Misma forma que `guardar_parte_http`: el repositorio inyectable es la costura de
test, y la suite prueba el borde entero **sin base de datos**.

### `js/pipeline.js`

```js
esAprobable(validacion)                  // los motivos, contra la lista del dominio
esCirculable(parte)                      // apto  O  aprobado vigente
cuerpoDeAprobacion(parte, opciones)      // el de /api/parte + usuario_oid + confirmado
semaforoDe(validacion, aprobacion)       // "verde" | "aprobado" | "ambar" | "rojo" | ""
```

`MOTIVOS_APROBABLES` se duplica en el front como constante con el comentario que
apunta al módulo del dominio, igual que `UMBRAL_CONFIANZA` y `CAMPOS_DEL_PARTE`
**[MEDIDO]**, y **la decisión de verdad la toma el backend**: el front solo evita
ofrecer un botón que va a responder 409.

---

## 12 · Riesgos y alternativas descartadas

### 12.1 · El riesgo que la feature acepta, por escrito

F-026 permite que un parte que la validación rechazó acabe **cerrando una
incidencia en el ERP de producción**. Eso es lo que pidió el responsable y es el
objeto de la feature, pero conviene que esté escrito qué lo hace acotado:

- **hace falta una persona**, identificada, y queda registrado quién y cuándo
  (R2, R13);
- **no vale para cualquier cosa**: un parte al que le falte un campo decisivo
  **no es aprobable** (R7), así que la aprobación nunca inventa un dato;
- **no relaja nada más**: siguen en pie el archivo previo, el gráfico antes del
  cierre, el dry-run dentro de la llamada que escribe, el login verificado
  contra el ERP y el estado de origen en el `WHERE` (R26);
- **se deshace**: revalidar con otro resultado revoca la aprobación (R30), y los
  cierres se deshacen en el ERP —81 precedentes medidos por F-008—.

Lo que **no** queda acotado, y hay que decirlo: la decisión de una persona sobre
una firma dudosa o sobre «no se reparó la totalidad» **no la revisa nadie
después**. No hay doble aprobación ni informe periódico. Si eso hiciera falta, la
consulta de R41 es el material y sale como feature nueva.

### 12.2 · Riesgo técnico · la revocación silenciosa

Una aprobación puede quedar revocada sin que quien la hizo se entere: basta con
que otra persona reprocese la remesa y la IA lea la observación de otra forma.
Mitigación: la pantalla enseña el estado real tras cada guardado (R22) y el parte
vuelve a pintarse ámbar o rojo, con su botón de aprobar otra vez. El modo de
fallo es **pedir una aprobación de más**, no colar una de menos.

### 12.3 · Alternativas descartadas

| Alternativa | Por qué se descarta |
|---|---|
| **Que corregir un campo apruebe** (la otra lectura de «cuando se modifiquen los campos o se revise») | Corregir la promoción no dice nada sobre la firma. Y la mitad útil **ya funciona**: corregir un campo decisivo ilegible devuelve el parte a verde por las reglas de F-004, sin aprobar nada (§0.6 de `requirements.md`). Lo que quedaría de (b) es lo peligroso: dar por buena una firma dudosa por un efecto lateral, sin registro de quién decidió. Queda descrita aquí por si el humano la prefiere: sería no crear `/api/aprobar` y, en su lugar, que `POST /api/parte` escriba la aprobación cuando el cuerpo traiga campos editados. **No se recomienda** |
| **Reescribir el veredicto a `apto`** | §2: no sobreviviría al siguiente guardado, borraría el motivo y haría indistinguible el aprobado del verde |
| **Una columna `aprobado_por` en `postventa.validaciones`** | Lo mismo: `upsert_validacion` la pisaría **[MEDIDO]** |
| **Guardar la aprobación solo en el navegador** | Es exactamente lo que el responsable descartó: «hay que guardarlo» |
| **Caducar por marca de tiempo** en vez de por huella | Rompe el criterio de aceptación: volver a subir la remesa —la única forma de recuperar el trabajo tras recargar— invalidaría todas las aprobaciones (P5) |
| **Comprobar la vigencia al leer**, en los tres pasos | El cuerpo de `/api/archivar` no trae motivos ni observaciones y no puede recomputar la huella; ensancharlo haría viajar texto manuscrito que R45 de F-025 prohíbe (§5) |
| **Aprobar por lotes** («aprobar toda la cola») | R28. Aprobar es mirar **ese** parte; un botón que aprueba veintidós es un botón que nadie ha leído |
| **Marcar el cierre en `dbo.log.tex`** | R42 y P6: convierte en variable un texto homogéneo en 6.843 filas y es una escritura distinta en el ERP, que decide el dueño del proceso |

---

## 15 · D-H · El autoguardado de las correcciones (2026-09-11)

Lo añade el responsable después de leer la spec: «escribir en un campo debe
guardar lo que escribes, según escribe guarda, sin botón». Requisitos R50 a
R55.

### 15.1 · Se revalida y se guarda **juntos**, con retardo

**Decidido: reutilizar `revalidarYGuardar`, con un retardo de 1.500 ms desde
la última pulsación**, y solo si el valor cambió respecto a lo último
guardado.

Por qué juntos: el acoplamiento existe por una razón escrita en el propio
código —guardar sin revalidar deja en la base el veredicto que la IA emitió
sobre el dato sin corregir— y **revalidar no gasta IA** (contrato de F-007
R17, una sola petición). Mantener la invariante «el veredicto corresponde al
dato» sale más barato que gestionarla rota.

Por qué 1.500 ms y no menos: son dos peticiones por pausa contra un
PostgreSQL **compartido con otros dos proyectos en producción**. A 1.500 ms,
escribir una observación de dos frases produce del orden de dos o tres
guardados, no treinta. Es un número que se puede subir o bajar sin cambiar
nada más: vive en `config.js` como constante, no repartido por el código.

**Descartado: guardar solo el campo y marcar el veredicto como obsoleto.**
Obliga a inventar un estado que **las tres puertas** tendrían que mirar (D-D),
y a que alguien recuerde revalidar después. Se cambia un problema conocido por
uno nuevo y más caro.

**Descartado: guardar al salir del campo.** No cubre el caso que el
responsable quiere resolver: escribir y cerrar la pestaña sin salir del campo.

### 15.2 · Las correcciones no pisan lo que leyó la máquina

El valor y la confianza de la IA se conservan tal cual. Es lo que ya hace
`aplicarCorrecciones` en el front —devuelve la extracción con las correcciones
aplicadas **sin destruir el original**— y lo que **F-015 va a necesitar** para
evaluar el prompt: un prompt no se puede evaluar contra un dato que una
persona corrigió encima.

### 15.3 · Qué se le enseña a quien escribe

Tres estados, y el del medio es el que hoy no existe:

| Estado | Cuándo | Qué se ve |
|---|---|---|
| Guardando | mientras la petición está en vuelo | un indicador discreto, sin bloquear el campo |
| Guardado | respuesta correcta | la marca de tiempo del último guardado |
| **No se ha podido guardar** | la petición falló | **un aviso que no se va solo**, y lo escrito **se conserva en pantalla** |

El tercero es R52 y es el que importa: quien escribe y no ve nada supone que
se guardó.

### 15.4 · La revocación no ocurre a mitad de palabra

La revocación de una aprobación se evalúa **sobre lo guardado**, con la huella
de D-B, y el guardado ocurre como mucho una vez por pausa. Así que revocar es,
como mucho, una vez cada 1.500 ms de silencio, no una por tecla.

### 15.5 · Aplica a todos los partes

No solo a los que van a revisión: perder lo escrito es igual de malo en un
parte verde, y la revalidación mantiene el veredicto al día en los dos casos.

---

## 13 · Encaje en la arquitectura y límite de microservicio

**Encaje.** F-026 no añade ningún paso al pipeline: añade una **puerta** a los
pasos 6, 7a y 7b, y lo hace donde ya están las demás. El reparto lo sigue
decidiendo el paso 4 (F-004), intacto. La forma es la de siempre: reglas en
`domain/`, orquestación en `application/pipelines/`, SQL en
`infrastructure/persistencia/`, traducción HTTP en `interface_adapters/api/` y
composición en el punto de entrada.

**Límite de microservicio.** Todo lo que toca esta feature es de
`services/postventa-api` y `services/postventa-front`, que son el backend y la
pantalla del mismo dominio —el parte de posventa— y ya trabajan juntos en cada
feature desde F-007. No hay ninguna responsabilidad que pertenezca a otro
servicio: no se toca el catálogo del portal, no se pide nada nuevo a
`sigrid-api` —ni un endpoint, ni un campo— y no se escribe en ninguna base que
no sea el esquema propio. **No hay nada que extraer.**

**Fronteras que sí se cruzan, y qué hay que hacer con ellas.** El servicio
expone un endpoint nuevo y crea una tabla nueva en el PostgreSQL compartido
(dentro de su esquema). Eso es exactamente lo que documenta
`azure-apps/postventa_incidencias.md`, así que se actualiza **en este mismo
trabajo** (R49), con commit aparte porque es otro repositorio. El servidor
compartido no se toca a nivel de servidor: el DDL es `CREATE TABLE IF NOT
EXISTS` y `CREATE INDEX IF NOT EXISTS` dentro de `postventa`, y la guarda de
`ddl.py` lo rechazaría si no lo fuera.

---

## 14 · Preguntas abiertas

Las ocho de `requirements.md`, con su recomendación razonada. **P1, P2, P4 y P5
cambian el diseño**: si el humano decide otra cosa en cualquiera de ellas, esta
spec vuelve al taller antes de implementar. **P3, P6, P7 y P8** acotan el
alcance y pueden decidirse sin reescribir nada.
