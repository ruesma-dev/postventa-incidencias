<!-- specs/F-056-revision-bandeja-backend/design.md -->
# F-056 · Revisión de la bandeja en el backend — Diseño técnico

> **Aprobado por el humano el 2026-10-06** (decisiones en §15). **D-4: contra
> Sigrid en vivo, decisión del humano 2026-10-06.** **Q-5 resuelta el
> 2026-10-06** con la medición T0 del humano: las ubicaciones válidas son las
> de la **tipología de cada unidad** (`prmtpl.ubica`), por unidad (§16). La página y el
> cierre de la sección del portal son **F-038**
> (`specs/F-038-bandeja-revision/design.md`), que consume el contrato de §8.

## 0 · Dónde está el riesgo

| Si falla… | Consecuencia | Quién lo ve |
|---|---|---|
| «Solo lo aprobado es candidato» | F-040 crea en el **ERP de producción** partes que nadie aprobó, o con otros valores | Posventa y el propietario, en Sigrid; anularlos es a mano |
| La validación contra el catálogo | Se aprueba un oficio, un par o una ubicación que el volcado rechazará | Quien vuelca, en el dry-run de F-040 |
| La concurrencia | Dos personas revisan la misma fila y una pisa a la otra | Nadie, hasta que el parte sale mal |
| El histórico | Se pierde quién aprobó o descartó, o lo que trajo la propiedad | Quien audite |
| El correo | Sale en un log o en una respuesta que no toca | Quien lea los logs |
| El DDL | Algo fuera del esquema propio de `psql-albaranes-rs9k2`, compartido | Albaranes y los demás |

**Rigor `critico`**: la aprobación es la puerta del volcado al ERP. Fase RED en
los centrales (R1–R3, R7, R9–R11, R13, R20–R22, R24–R26, R34, R35), cobertura
≥ 80 % de lo cambiado, cero supervivientes sin justificación aceptada por
escrito, y las `MANUAL (humano)` con su comando exacto.

## 1 · Lo que hay hoy y lo que se reutiliza

De F-036 (`specs/F-036-importar-excel/design.md` §5.3, §6.1, §8, §15.5), **sin
modificar**: `bandeja_incidencias` y `IncidenciaEnBandeja`; `leer_catalogo`
(`application/pipelines/catalogo_obra.py`, las dos lecturas `sql/read` y sus
errores); `opciones_de_la_obra` (`application/pipelines/plantilla.py`, los
grupos vigentes); `clave_de_duplicado`; las etiquetas de urgencia
y listado (`cargar_plantilla_yaml`; **no** su lista de ubicaciones, D-4);
`MAX_USUARIO_OID` (`interface_adapters/api/importar.py`).
El patrón append-only de `historico_estado` (F-028) y
`decisiones_equivalencia` (F-036); el de identidad en el cuerpo con
`confirmado: true` booleano.

## 2 · Límite de servicio

Decidido (D-1): la revisión se parte. **F-056** es solo
`services/postventa-api` —estados, reglas, tabla, endpoints, documentos— y va
**antes**. **F-038** es solo `services/postventa-front` —la página
`bandeja.html` y el cierre de la sección `bandeja` del portal— y está
bloqueada por F-056: no empieza hasta que F-056 esté `done` y desplegada. F-038
sigue siendo la ficha de `Portal.SECCIONES`, y por eso la guardia de R62 de
F-035 no cambia de fichas. F-056 **no** toca el front ni la maqueta.

## 3 · El modelo

### 3.1 · Una revisión es una foto completa (D-3)

Cada acción añade a `postventa.revisiones_bandeja` una fila con **todos los
valores vigentes** tras ella, el `oid`, el correo y la hora. La fila de
`bandeja_incidencias` no se toca nunca: es lo que mandó la propiedad. Leer el
estado es leer una fila; lo aprobado es exactamente esa fila; los `CHECK` de
la bandeja se repiten y la base los hace cumplir; el histórico se cuenta
comparando fotos.

### 3.2 · Estados derivados (R1)

| Última revisión | Vigentes = importados | Estado |
|---|---|---|
| ninguna, `editar` o `recuperar` | sí | `nueva` |
| `editar` o `recuperar` | no | `editada` |
| `aprobar` | — | `aprobada` |
| `descartar` | — | `descartada` |

`volcada` no es de F-056: la añade F-040 con su propia tabla (§10).

### 3.3 · Acciones permitidas (R2; D-6, D-7)

| Desde \ acción | `editar` | `descartar` | `aprobar` | `recuperar` |
|---|---|---|---|---|
| `nueva`, `editada` | sí | sí | sí | — |
| `aprobada` | sí (pierde la aprobación) | sí | — | — |
| `descartada` | — | — | — | sí |

### 3.4 · Qué hace cada acción

| Acción | Lee Sigrid | Foto | Además |
|---|---|---|---|
| `editar` | sí | los pedidos, validados, con nombres de Sigrid | `sin_cambios` si son los vigentes |
| `descartar` | no | los vigentes | `motivo` opcional ≤ 500 |
| `recuperar` | no | los vigentes | — |
| `aprobar` | sí | los vigentes, sin cambiar | 409 con motivos; huella |

### 3.5 · Motivos de no aprobable (R21, D-4)

**Una** función pura los calcula para el listado, para el filtro
`con_motivos`, para el `resumen` y para la acción `aprobar`: lo que se enseña
y lo que se hace no pueden divergir.

| Código | Cuándo | Texto sugerido para F-038 |
|---|---|---|
| `unidad_fuera_de_la_obra` | la unidad no está hoy entre las de la obra | «La unidad ya no es de la obra en Sigrid» |
| `sin_ubicacion` | no hay ubicación | «Falta la ubicación» |
| `ubicacion_fuera_de_lista` | hay ubicación y no está en la lista de hoy | «La ubicación no está en la lista» |
| `sin_oficio` | no hay oficio | «Falta el oficio» |
| `oficio_ambiguo` | el oficio es ambiguo | «Elige el código del oficio: hay varios en la obra» |
| `oficio_fuera_de_la_obra` | el código no está hoy en `obrofc` de la obra | «Este oficio ya no está en la obra en Sigrid» |
| `par_fuera_de_la_obra` | hay proveedor y el par no es hoy una fila de `obrofc` | «Este proveedor ya no está en la obra con ese oficio» |
| `proveedor_ambiguo` | proveedor ambiguo (hoy imposible: F-050) | «Elige el proveedor» |
| `duplicada` | §3.6 | «Duplicada de la fila N: descarta una o distínguelas» |

**La ubicación (D-4).** Obligatoria para aprobar y, si la hay, **válida en
Sigrid en el momento** de editar o aprobar (precisión del humano del
2026-10-06): no contra `config/plantilla_incidencias.yaml`. La lista sale de
una **tercera lectura** de Sigrid (§16.3): las ubicaciones de la **tipología
de la unidad** de la incidencia (Q-5). `ubicacion_fuera_de_lista` conserva su
nombre: la «lista» es la de Sigrid de hoy **para esa unidad**. Consecuencia
para la 0677: toda fila sin ubicación sale con `sin_ubicacion` hasta que
alguien se la ponga, y una fila cuya ubicación (de la plantilla) no esté en la
tipología de su unidad sale con `ubicacion_fuera_de_lista`; cuántas, lo dice
`resumen.por_motivo` en T19.

> **Aceptado por el líder el 2026-10-07** (ajustes de contrato del Bloque 1,
> `progress/impl_F-056.md`, «Decisiones de diseño», 1 y 2; anotados aquí por la
> N-1 de la review del Bloque 1):
>
> - **`sin_oficio` y el oficio ambiguo.** A efectos de `sin_oficio`, el oficio
>   ambiguo **cuenta como oficio** (como `hay_oficio` de R99 de F-036): una fila
>   con oficio ambiguo da **solo** `oficio_ambiguo`, nunca también
>   `sin_oficio`. `sin_oficio` es «ni código ni oficio ambiguo». Así los 47 de
>   la 0677 salen una vez en `por_motivo` (T19 espera `oficio_ambiguo` = 47) y
>   una ambigua sigue sin ser aprobable, porque `oficio_ambiguo` bloquea.
> - `motivos_no_aprobable` no recibe `listas` (tabla de §4).
>
> **Interpretaciones del implementer** (decisiones 3 y 4 del mismo informe),
> revisadas en la review del Bloque 1 y anotadas aquí por encargo del líder
> (2026-10-08):
>
> - **El par solo se mira con código de oficio.** `par_fuera_de_la_obra` exige
>   código de oficio y de proveedor: con el oficio ambiguo no hay par que
>   comprobar (el motivo ya es `oficio_ambiguo`). Con un oficio fuera de la obra
>   y proveedor salen los dos motivos.
> - **La ubicación se recorta** al validar, al guardar y al comparar en los
>   motivos (R47 y §16.2 mandan sobre el «solo se recortan» de §4). En una
>   edición, una ubicación `""` o de solo blancos es un **error** de
>   `ubicacion` (400 `valores_no_validos`), no se convierte en `null`: quien
>   quiera quitarla manda `null`.

### 3.6 · Duplicadas (D-5)

Una fila con `duplicada_de` repite en el mismo fichero la clave de otra.
Tiene el motivo `duplicada` **mientras** la otra no esté `descartada` **y**
las claves de las dos, con sus valores **vigentes**, coincidan. Salidas:
descartar una, o editar una para distinguirlas. La aprobación bloquea las dos
filas y comprueba que la última revisión de la original no ha cambiado.

> **Interpretación del implementer** (decisión 8 de `progress/impl_F-056.md`),
> revisada en la review del Bloque 1 y anotada aquí por encargo del líder
> (2026-10-08):
> una fila con `duplicada_de` cuya original **no viene cargada** en la
> situación tiene el motivo `duplicada`: lo que no se puede comprobar no se
> aprueba. El repositorio (Bloque 2) carga siempre la original con su última
> revisión, así que en la práctica solo pasa si la original falta.

## 4 · Dominio puro: `domain/models/revision.py`

Sin red, sin base, sin reloj, sin `infrastructure/`.

```python
class AccionRevision(StrEnum): EDITAR="editar"; DESCARTAR="descartar"; APROBAR="aprobar"; RECUPERAR="recuperar"
class EstadoRevision(StrEnum): NUEVA="nueva"; EDITADA="editada"; APROBADA="aprobada"; DESCARTADA="descartada"
class MotivoNoAprobable(StrEnum): ...   # los nueve de §3.5, en ese orden
class FiltroEstado(StrEnum): ACTIVAS="activas"; TODAS="todas"; NUEVA=...; EDITADA=...; APROBADA=...; DESCARTADA=...

MAX_MOTIVO = 500; MAX_CORREO = 254; TAMANO_POR_DEFECTO = 100; TAMANO_MAXIMO = 200
TOPE_LECTURA_OBRA = 10_000

@dataclass(frozen=True)
class Quien:                      # R9, R43: traza, no identidad verificada
    oid: str; correo: str

@dataclass(frozen=True)
class ValoresIncidencia:          # mismas invariantes que la bandeja (R99 de F-036)
    unidad_codigo: str; unidad_nombre: str; ubicacion: str | None
    descripcion: str; detalle: str | None
    oficio_codigo: str | None; oficio_nombre: str | None; oficio_ambiguo: bool
    proveedor_codigo: str | None; proveedor_nombre: str | None; proveedor_ambiguo: bool
    urgencia: Urgencia | None; listado: Listado | None

@dataclass(frozen=True)
class ValoresPedidos:             # lo que trae `valores`: códigos y textos, nunca nombres
    unidad_codigo: str; ubicacion: str | None; descripcion: str; detalle: str | None
    oficio_codigo: str | None; proveedor_codigo: str | None; urgencia: str | None; listado: str | None

@dataclass(frozen=True)
class Revision:                   # lectura: lleva el correo, NUNCA el oid
    revision_id: int; incidencia_id: UUID; accion: AccionRevision
    valores: ValoresIncidencia; huella: str; motivo: str | None
    correo: str; revisado_at_utc: datetime

@dataclass(frozen=True)
class RevisionNueva:              # escritura: lleva los dos
    incidencia_id: UUID; accion: AccionRevision; valores: ValoresIncidencia
    huella: str; motivo: str | None; quien: Quien; revisado_at_utc: datetime

@dataclass(frozen=True)
class SituacionDeRevision:
    incidencia: IncidenciaEnBandeja; obra_codigo: str; origen: OrigenIncidencia
    ultima: Revision | None; original: "SituacionDeRevision | None"

@dataclass(frozen=True)
class ClaveDeOrden:               # R25
    creada_at_utc: datetime; fila_origen: int | None; incidencia_id: UUID

@dataclass(frozen=True)
class CandidataAlVolcado:         # R34, R35, §10
    incidencia_id: UUID; obra_codigo: str; valores: ValoresIncidencia
    huella: str; aprobada_at_utc: datetime; revision_id: int
    def __post_init__(self) -> None: ...   # sin oficio, sin ubicación o con ambiguos → ValueError
```

| Función | Responsabilidad | R |
|---|---|---|
| `valores_importados`, `valores_vigentes` | Las dos fotos | R1 |
| `estado_de(situacion)` | §3.2 | R1 |
| `acciones_posibles(estado)` | §3.3 | R2 |
| `validar_quien(oid, correo) -> Quien` | R5 y R9; el error no repite nada | R9 |
| `campos_cambiados(antes, despues)` | Los 8 campos lógicos, en orden | R29, R33 |
| `ubicaciones_de_tipologia(texto) -> tuple[str, ...]` | R48: partir por `;`, recortar, fuera vacíos y > 48, quitar solo repetidos exactos, en su orden; `None` → `()` | R47, R48 |
| `validar_valores(pedidos, *, vigentes, catalogo, ubicaciones, listas)` | R13–R15; **todos** los errores; `ubicaciones: Mapping[str, tuple[str, ...]]` (por unidad) | R13–R15, R48 |
| `motivos_no_aprobable(situacion, *, catalogo, ubicaciones)` (sin `listas`: ningún motivo mira urgencias ni listados; aceptado por el líder el 2026-10-07) | §3.5, §3.6; la ubicación, contra la lista de **su** unidad | R21, R22, R48 |
| `huella_de_valores(valores)` | `sha256` de los 13 valores en orden fijo, separador imposible en un texto, `None` ≠ `""` | R20 |
| `decidir(situacion, peticion, *, catalogo, ubicaciones, listas, ahora)` | Une todo: transición, frescura, validar o motivos, `sin_cambios`, motivo | R2–R22 |
| `clave_de_orden`, `texto_de_clave(clave) -> str`, `clave_de_texto(texto) -> ClaveDeOrden` | R25: la clave como JSON compacto y canónico, **sin codificar** (el base64url del cursor lo pone y lo quita el borde, §8); un texto que no es el canónico es `PeticionDeRevisionInvalida` | R23, R25 |
| `paginar(filas_ordenadas, *, filtro, con_motivos, despues_de, tamano)` | Filtra, corta y da la clave de la siguiente | R25, R26 |
| `resumen(filas)` | R27 | R27 |
| `es_candidata(situacion)` | Última revisión `aprobar` | R34 |

> **Decisión del humano 2026-10-07: el base64url vive en la capa HTTP (regla de
> F-012).** `test_f012_arquitectura_ni_domain_ni_application_nombran_base64`
> prohíbe la palabra `base64` en `domain/` y `application/` («el transporte es
> cosa del adaptador»). El dominio construye y valida la clave del cursor como
> texto JSON canónico (`texto_de_clave` / `clave_de_texto`); el borde
> (`interface_adapters/api/revision.py`, Bloque 3) la envuelve en base64url al
> responder y la desenvuelve al recibirla. El cliente sigue recibiendo un cursor
> opaco base64url: R25 se cumple igual. El test de F-012 no se toca.

Detalles que fijan los tests: comparación exacta de códigos y valores tasados
(solo descripción, detalle, motivo y correo se recortan; la descripción además
colapsa blancos); el nombre del oficio es el de Sigrid **de ese código** (sin
nombre en Sigrid, el código), no la etiqueta del grupo que guardó la bandeja;
el nombre del proveedor, el de su fila de `obrofc` (si el par sale dos veces
con nombres distintos, el primero por código, y el test lo fija); R15 conserva
`oficio_nombre` y `oficio_ambiguo` y exige el proveedor vigente o `null`.

Errores nuevos en `domain/models/errores.py`, traducidos en `function_app.py`:

| Error | HTTP | Cuerpo |
|---|---|---|
| `PeticionDeRevisionInvalida` | 400 | `{error, codigo: "peticion_invalida"}` |
| `ValoresNoValidos` | 400 | `{error, codigo: "valores_no_validos", errores: [{campo, problema}]}` |
| `SinCambios` | 400 | `{error, codigo: "sin_cambios"}` |
| `IncidenciaNoEncontrada` | 404 | `{error, codigo: "incidencia_no_encontrada"}` |
| `AccionNoPermitida` | 409 | `{error, codigo: "accion_no_permitida", estado, acciones}` |
| `RevisionDesactualizada` | 409 | `{error, codigo: "revision_desactualizada"}` |
| `IncidenciaNoAprobable` | 409 | `{error, codigo: "incidencia_no_aprobable", motivos}` |
| `BandejaDemasiadoGrande` | 409 | `{error, codigo: "bandeja_demasiado_grande", total}` |

## 5 · Puertos y adaptadores

`domain/ports/revision.py`:

```python
class RevisionPort(Protocol):
    def listar(self, *, obra_codigo: str, tope: int) -> tuple[SituacionDeRevision, ...]: ...
    def contar(self, *, obra_codigo: str) -> int: ...
    def situacion(self, *, incidencia_id: UUID) -> SituacionDeRevision | None: ...
    def registrar(self, *, revision: RevisionNueva, esperadas: Mapping[UUID, int | None]) -> int: ...
    def historial(self, *, incidencia_id: UUID) -> tuple[SituacionDeRevision, tuple[Revision, ...]] | None: ...
    def aprobadas(self, *, obra_codigo: str) -> tuple[CandidataAlVolcado, ...]: ...
```

`listar` trae, de una vez y hasta `tope + 1` filas (para saber si se pasa sin
un `COUNT` aparte; `contar` solo para el número del 409), cada incidencia con
su última revisión y la de su original (`LEFT JOIN LATERAL … ORDER BY
revision_id DESC LIMIT 1`), en el orden de R25. La lectura de 10.000 filas de
menos de 1 KB es del orden de 10 MB entre la base y el proceso, una vez por
página: dentro del presupuesto de 45 s y de la memoria de la instancia.

`registrar`, en **una** transacción (R7, R22): `SELECT incidencia_id FROM
postventa.bandeja_incidencias WHERE incidencia_id = ANY(%s) ORDER BY
incidencia_id FOR UPDATE` (orden fijo: sin interbloqueos); la última
`revision_id` de cada una contra `esperadas` (si no cuadra,
`RevisionDesactualizada` y `ROLLBACK`); `INSERT … RETURNING revision_id`;
`COMMIT`. **Nunca `pg_advisory_lock`**: el espacio de claves es del servidor
compartido.

`infrastructure/persistencia/sentencias_revision.py` (puro, esquema de la
configuración como `sentencias_bandeja.py`) e
`infrastructure/persistencia/repositorio_revision_pg.py`
(`RepositorioRevisionPostgres`), con `construir_revision(ajustes)` en
`fabrica.py`. **Ninguna lectura selecciona `revisado_por`** (el `oid`): se
escribe y no se lee. `revisado_correo` sí se lee, para R10.

## 6 · SQL: `15_revisiones_bandeja.sql`

Esquema `postventa`, siguiente a `14_…`; lee de `13_bandeja_incidencias.sql`;
solo `CREATE TABLE IF NOT EXISTS` y `CREATE INDEX IF NOT EXISTS`.

```sql
CREATE TABLE IF NOT EXISTS postventa.revisiones_bandeja (
    revision_id       bigserial   PRIMARY KEY,
    incidencia_id     uuid        NOT NULL
                      REFERENCES postventa.bandeja_incidencias (incidencia_id),
    accion            text        NOT NULL
                      CHECK (accion IN ('editar', 'descartar', 'aprobar', 'recuperar')),
    unidad_codigo     text        NOT NULL,
    unidad_nombre     text        NOT NULL,
    ubicacion         text        CHECK (char_length(ubicacion) <= 48),
    descripcion       text        NOT NULL CHECK (char_length(descripcion) BETWEEN 1 AND 128),
    detalle           text        CHECK (char_length(detalle) <= 2000),
    oficio_codigo     text,
    oficio_nombre     text,
    oficio_ambiguo    boolean     NOT NULL DEFAULT false,
    proveedor_codigo  text,
    proveedor_nombre  text,
    proveedor_ambiguo boolean     NOT NULL DEFAULT false,
    urgencia          text        CHECK (urgencia IN ('urgente', 'seguridad')),
    listado           text        CHECK (listado IN ('primero', 'segundo')),
    huella_valores    text        NOT NULL,
    motivo            text        CHECK (char_length(motivo) <= 500),
    revisado_por      text        NOT NULL,
    revisado_correo   text        NOT NULL CHECK (char_length(revisado_correo) BETWEEN 3 AND 254),
    revisado_at_utc   timestamptz NOT NULL,
    CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL)),
    CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL)),
    CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL),
    CHECK (motivo IS NULL OR accion = 'descartar')
);

CREATE INDEX IF NOT EXISTS ix_revisiones_bandeja_incidencia
    ON postventa.revisiones_bandeja (incidencia_id, revision_id DESC);
```

La cabecera del `.sql` dice: append-only (manda la de mayor `revision_id`);
el estado no se guarda; la bandeja no se toca; `revisado_por` es el `oid`
opaco (seudónimo), que **no sale** en ninguna respuesta ni log;
`revisado_correo` es el **correo corporativo** de quien revisa (§9): dato
personal de un **empleado interno**, guardado por decisión del humano del
2026-10-06 para enseñar quién hizo cada cosa, que **solo** devuelven
`GET /api/revision` y su historial y que **nunca** va a un log; `motivo` es
texto libre que solo sale en el historial; el `CHECK` de `accion` no se puede
ampliar después (F-040 llevará el volcado en su tabla); «aprobar exige oficio
y ubicación» vive en el dominio y no en un `CHECK`, porque un `CHECK` no se
cambia después; sin `ON DELETE CASCADE`; ni binarias ni JSON (listas para
F-048).

## 7 · Aplicación: `application/pipelines/revision.py`

```python
def listar_para_revisar(peticion: PeticionDeListado, *, revision, catalogo_obra, equivalencias, listas) -> PaginaDeRevision
def aplicar_accion(peticion: PeticionDeAccion, *, revision, catalogo_obra, listas, ahora) -> IncidenciaRevisada
def historial(incidencia_id, *, revision) -> HistorialDeRevision
def candidatas_al_volcado(obra_codigo, *, revision) -> tuple[CandidataAlVolcado, ...]
```

`aplicar_accion`, lo barato primero y **Sigrid fuera de la transacción**:
`situacion` (404) → `acciones_posibles` (409) → frescura contra la última
leída (409, sin Sigrid) → solo en `editar` y `aprobar`, `leer_catalogo` y
las ubicaciones válidas (§16.3) →
`decidir` (400/409) → `registrar` (segunda frescura, en la transacción) → la
respuesta con la foto nueva (`motivos_no_aprobable` con el catálogo leído, o
`None`).

`listar_para_revisar`: `revision.listar(tope=10_000)` (si vuelven más,
`BandejaDemasiadoGrande` con `contar`) → `leer_catalogo` + `opciones_de_la_obra`
+ las ubicaciones válidas (una vez cada una) → por fila, estado, cambios y motivos → `resumen` sobre todas →
`paginar` con los filtros y el cursor.

`candidatas_al_volcado` no tiene ruta HTTP: es el punto de entrada de F-040.

## 8 · Borde HTTP: `interface_adapters/api/revision.py`

Tres rutas nuevas en `function_app.py`, en `ANONYMOUS` como las diecisiete de
hoy (veinte en total), sin mirar ninguna ventana de escritura. El handler
compone `construir_revision`, `construir_catalogo_obra`,
`construir_equivalencias` y el adaptador de ubicaciones (§16.3); los puertos inyectables
son su costura de test.

| Ruta | Éxito | Errores |
|---|---|---|
| `GET /api/revision?obra=&estado=&con_motivos=&tamano=&cursor=` | 200 | 400; 404 `ObraSinUnidades`; 409 `ObraAmbigua`, `CatalogoSinVerificar`, `bandeja_demasiado_grande`; 503 |
| `GET /api/revision/historial?incidencia_id=` | 200 | 400; 404; 503 base |
| `POST /api/revision/acciones` | 200: la incidencia | 400; 404; 409; los del catálogo; 503 |

`GET /api/revision` (datos ficticios):

```json
{"obra": "9901",
 "catalogo": {"unidades": [{"codigo": "9901.03VILLA 1.", "nombre": "Villa Ejemplo 1"}],
              "ubicaciones": {"9901.03VILLA 1.": ["baño", "cocina"]},
              "oficios": [{"codigo": "0046", "nombre": "Carpintería de madera",
                           "grupo": {"etiqueta": "Carpintería de madera", "codigos": ["0046", "0143"]}}],
              "pares": [{"oficio_codigo": "0046", "proveedor_codigo": "EJ07",
                         "proveedor_nombre": "Carpintería Ejemplo, S.L."}],
              "urgencias": [{"codigo": "urgente", "etiqueta": "Urgente"}],
              "listados": [{"codigo": "primero", "etiqueta": "Primer listado"}]},
 "resumen": {"total": 160, "por_estado": {"nueva": 150, "editada": 6, "aprobada": 3, "descartada": 1},
             "con_motivos": 120, "por_motivo": {"sin_ubicacion": 40, "oficio_ambiguo": 47, "…": 0}},
 "filtros": {"estado": "activas", "con_motivos": null},
 "total_filtrado": 159,
 "incidencias": [{"incidencia_id": "…", "origen": "excel", "importacion_id": "…",
   "fila_origen": 7, "creada_at_utc": "…", "duplicada_de": null,
   "importados": {"unidad_codigo": "…", "unidad_nombre": "…", "ubicacion": null,
                  "descripcion": "…", "detalle": null, "oficio_codigo": null,
                  "oficio_nombre": "Carpintería de madera", "oficio_ambiguo": true,
                  "proveedor_codigo": null, "proveedor_nombre": null,
                  "proveedor_ambiguo": false, "urgencia": null, "listado": null},
   "vigentes": {"…": "las mismas claves"}, "cambios": [], "estado": "nueva",
   "revision_id": null, "revisado_at_utc": null, "revisado_por": null,
   "motivos_no_aprobable": ["sin_ubicacion", "oficio_ambiguo"]}],
 "siguiente": "eyJjIjoi…"}
```

`GET /api/revision/historial`:

```json
{"incidencia_id": "…",
 "importada": {"origen": "excel", "importacion_id": "…", "creada_at_utc": "…"},
 "revisiones": [{"revision_id": 12, "accion": "editar", "revisado_at_utc": "…",
                 "correo": "persona@ejemplo.invalid", "campos_cambiados": ["oficio"], "motivo": null}]}
```

`POST /api/revision/acciones`:

```json
{"incidencia_id": "…", "accion": "editar", "usuario_oid": "…",
 "usuario_correo": "persona@ejemplo.invalid", "confirmado": true, "revision_previa": null,
 "valores": {"unidad_codigo": "…", "ubicacion": "baño", "descripcion": "…", "detalle": null,
             "oficio_codigo": "0046", "proveedor_codigo": "EJ07", "urgencia": null, "listado": null}}
```

(`descartar` lleva `motivo` opcional; `aprobar` y `recuperar`, solo lo común.)
En `valores.ubicacion`, `null` quita la ubicación; un texto se recorta por los
extremos y, si queda vacío, es el error `{campo: "ubicacion"}` (400
`valores_no_validos`), **no** un `null` (§3.5).
Se comprueba el cuerpo entero antes de construir nada. El log: obra (en el
listado), `incidencia_id`, acción y resultado; nunca `oid`, correo ni textos.

## 9 · El correo de quien actúa (D-8): qué cambia y qué no

**Hasta hoy, la regla del servicio era «el `oid` y nada más»**, escrita en las
cabeceras del DDL —`02_remesas` (además en `NULL`, D3 de F-019), `06_cierres`,
`07_preferencias`, `08_usuarios_sigrid`, `09_graficos`, `10_aprobaciones`,
`11_historico_estado` y `12_importaciones`: «NUNCA su correo, NUNCA su
nombre»—, en R52 de F-028 (ni el `oid`, ni el correo, ni el nombre salen en
pantallas, respuestas o logs) y en R47 de F-036. El correo ya llega al backend
en un caso, `POST /api/cerrar` (para proponer el login de Sigrid), pero no se
guarda.

**Lo que cambia, y solo aquí**: `postventa.revisiones_bandeja` guarda, en cada
fila, `revisado_correo` junto al `oid`, y `GET /api/revision` (el de la última
revisión) y `GET /api/revision/historial` (el de cada una) lo devuelven, para
que la página enseñe quién hizo cada cosa. Decisión del humano del
2026-10-06.

**Lo que no cambia**: ninguna de esas ocho tablas, ni sus respuestas, ni sus
tests; el `oid` sigue sin salir en ninguna respuesta (tampoco en las de
F-056); y el correo **nunca va a un log** ni a un mensaje de error.

**Qué es**: el correo **corporativo** de un **empleado interno** del grupo
`posventa-usuarios` (sale de `/.auth/me`: el claim de correo o
`userDetails`, lo que ya hace `identidadDe` en `js/api.js`); **no** es un dato
del cliente ni de la propiedad. Como el `oid`, es una **traza de quién dice
ser**: la cabecera del proxy no va firmada (D-13). Va a `docs/INTEGRACION.md`
§7 (datos personales) con esta explicación, y **no** se publica en el
datamart (F-048) sin otra decisión expresa.

## 10 · Lo que hereda F-040

| Campo de §8.9 | De dónde sale | Garantiza / decide |
|---|---|---|
| `obra` | `obra_codigo`, literal | F-056 |
| `usu` | Login de Sigrid de quien vuelca (correspondencia de F-009) | **F-040** |
| `commit` | Dry-run por defecto | **F-040** |
| `referencia_externa` | `PVI-` + `incidencia_id` (≤ 80) | **F-040** |
| `unidad_postventa` | `unidad_codigo`, de la obra al aprobar | F-056 |
| `descripcion` (1–128) | `descripcion` | F-056 |
| `descripcion_larga` | `detalle`, o nada | **F-040** (y la urgencia) |
| `tipo` | `0002` por defecto; regla con `listado` abierta | **F-040** |
| `clase` | no se manda | **F-040** |
| `oficio` | `oficio_codigo`, resuelto, no ambiguo, de `obrofc` al aprobar | F-056 |
| `ubicacion` (≤ 48) | `ubicacion`, **siempre presente** (D-4) y una de las de la tipología de su unidad en Sigrid el día de la aprobación (§16; §8.9 la acepta sin validarla) | F-056 |
| `forma_comunicacion` | Escrita por defecto | **F-040** |
| `intervinientes` | `[{oficio, proveedor}]` si hay proveedor (par de `obrofc` al aprobar) | F-056 el par; **F-040/F-039** el resto y «Causante» |

> **O-1 de la review del Bloque 1, hecho en el Bloque 2 (2026-10-08):**
> `CandidataAlVolcado` exige además que la ubicación venga **ya recortada**
> (`ubicacion == ubicacion.strip()`, no vacía) y de **≤ 48** caracteres
> (`MAX_UBICACION`): es la última defensa antes del ERP, y aprobar guarda los
> vigentes sin cambiarlos. Sin `CHECK` equivalente en el DDL: §6 deja «aprobar
> exige oficio y ubicación» en el dominio, y un `CHECK` de recorte afectaría a
> todas las acciones (también a descartar una fila importada) y no se podría
> cambiar después.

Para F-040: Sigrid puede cambiar entre aprobar y volcar —su dry-run lo
detecta y, para corregir, basta **editar** (saca la incidencia de las
candidatas)—; `volcada` va en su propia tabla y la costura es
`acciones_posibles` y `es_candidata`; y puede comprobar que manda lo aprobado
con `huella_de_valores`.

## 11 · Los 144 y los 47

| Caso | Se ve como | Se resuelve |
|---|---|---|
| Oficio que hoy ya no está en la obra | `oficio_fuera_de_la_obra` | Editar |
| Proveedor que hoy ya no está con ese oficio | `par_fuera_de_la_obra` | Editar |
| Par válido que el `v2` cambió | No se ve (Q-1: basta con lo de hoy) | — |
| Oficio ambiguo (los 47) | `oficio_ambiguo` | Editar: elegir el código |
| Sin ubicación | `sin_ubicacion` (D-4) | Editar |

No se descarta y reimporta (D-10): el índice `ux_bandeja_clave` no sabe de
revisiones y el `v2` sin cambios es `ya_importado`; D-7 de F-036 no cambia.
`resumen.por_motivo` da los recuentos para la verificación.

## 12 · Ficheros

**A crear** (`services/postventa-api/`): `domain/models/revision.py`,
`domain/ports/revision.py`, `application/pipelines/revision.py`,
`infrastructure/persistencia/sql/15_revisiones_bandeja.sql`,
`infrastructure/persistencia/sentencias_revision.py`,
`infrastructure/persistencia/repositorio_revision_pg.py`,
`interface_adapters/api/revision.py`; `domain/ports/ubicaciones_validas.py`,
`infrastructure/sigrid/consultas_ubicaciones_validas.py` y
`infrastructure/sigrid/ubicaciones_validas.py` (§16.3); tests
`test_f056_ubicaciones.py`, `test_f056_revision_dominio.py`, `test_f056_paginacion.py`,
`test_f056_ddl.py`, `test_f056_repositorio_revision.py`,
`test_f056_pipeline_revision.py`, `test_f056_revision_http.py`,
`test_f056_alcance_cerrado.py`, `test_f056_documentacion.py` y
`tests_bbdd/tests/test_f056_bbdd_revision.py`.

**A modificar**: `domain/models/errores.py` (ocho errores);
`infrastructure/persistencia/fabrica.py` (`construir_revision`);
`function_app.py` (tres rutas, errores, cabecera: veinte anónimos y
`GET /api/revision` como tercer endpoint de dato de fuera acumulado, con la
paginación como su cautela de volumen); los tests que enumeran rutas,
ficheros `.sql` o tablas (`test_f005_ddl_idempotente_texto.py`,
`test_f010_endpoints_protegidos.py`, `test_f036_ddl.py` si fija el último),
añadiendo sin quitar y citándolos en el informe; `docs/ARCHITECTURE.md`
(sección «Revisión de la bandeja (F-056)», enmienda en «Lo que no hacen» de
F-036); `docs/INTEGRACION.md` (§2, §7, §8); `azure-apps/postventa_incidencias.md`.

**No se toca**: `bandeja_incidencias` y los `12_`–`14_`; `importacion.py`,
`plantilla_incidencias.py`, `equivalencias.py` (dominio y aplicación, que toca
F-053), `catalogo_obra.py`, `plantilla.py`, `paso_importacion.py` (se importan);
`interface_adapters/api/bandeja.py`, `importar.py`, `equivalencias.py`;
`sentencias_bandeja.py`, `repositorio_bandeja_pg.py`; lo que **ya hay** en
`infrastructure/sigrid/*` (las dos lecturas de F-036 no cambian; la tercera,
la de ubicaciones, se **añade** en módulos nuevos, §16.3; en
`infrastructure/sigrid/fabrica.py` solo se **añade** `construir_ubicaciones_validas`);
`config/plantilla_incidencias.yaml`; las tablas y respuestas que dicen «nunca
el correo» (§9); `services/postventa-front/` entero (es F-038); `infra/*`.

## 13 · Tests

Sin red, base, IA ni `.xlsx`; nombres `test_f056_rN_…`.

| R | Lo que fija además de lo obvio |
|---|---|
| R1–R3 | Las filas de §3.2; las 16 casillas de §3.3; aprobar → editar saca de las candidatas |
| R5 | Cada forma inválida (también `"true"`, `1`, clave de otra acción, `revision_previa: 0`, correo sin `@`, con blanco, con dos `@`, de 255) → 400 sin construir adaptadores; el mensaje no contiene el `oid` ni el correo |
| R7, R22 | Primera frescura sin Sigrid; segunda en la transacción; la original cambia entre medias → 409 |
| R9–R12 | El correo se guarda recortado; sale en listado e historial; **el `oid` de la prueba no aparece en ningún JSON**; `caplog`: ni el correo ni el `oid` en ningún registro, también en los 400 y 409 |
| R13–R16 | Cada campo con sus casos exactos; todos los errores a la vez; R15; `sin_cambios` (también con un blanco que se colapsa) |
| R18, R19 | Motivo 500/501; sin Sigrid (el doble del catálogo falla si se llama) |
| R20–R21 | Cada motivo solo y todos juntos, en el orden de §3.5; `sin_ubicacion` |
| R23–R27 | Validación antes de nada; tope 10.000 (con 10.001 → 409, sin truncar); orden total con empates de fecha y filas sin `fila_origen`; recorrer todas las páginas da cada fila **una vez** y en orden; cursor manipulado → 400; filtros en el servidor; `resumen` sin filtros y con `por_motivo`; una lectura de Sigrid por petición |
| R29, R33 | Forma de la fila y del historial; `revisado_por` es el correo |
| R34, R35 | Solo última `aprobar`; `CandidataAlVolcado` no se construye sin oficio, sin ubicación o con ambiguos |
| R36–R38 | La guarda real acepta el `.sql`; idempotente; `CHECK` = `Enum`; ningún `UPDATE`/`DELETE`/`TRUNCATE`; ninguna lectura selecciona `revisado_por`; `ORDER BY … revision_id DESC` |
| R39, R40, R45 | Alcance con base fija `349ba06`: ninguna ruta de escritura de la pasarela; ni ventanas ni variables nuevas; los ficheros de «No se toca» sin cambios; ninguna columna `correo` nueva fuera de `revisiones_bandeja` |
| R44 | Frases clave en los tres documentos, con el correo en §7 |
| R46–R48 | La consulta de §16.3 carácter a carácter (test puro); una lectura por petición, compartida; ninguna en descartar, recuperar e historial; al techo → 409, cortada por debajo → 503 (como F-036); sin Sigrid → 503 sin escribir; `ubicaciones_de_tipologia` con `;` dobles, blancos, vacíos, > 48, repetidos exactos (fuera) y que difieren en mayúsculas (se quedan los dos), `None`; unidad sin tipología → lista vacía → `ubicacion_fuera_de_lista`; una ubicación válida en otra unidad de la obra **no** vale; cambiar la unidad al editar revalida; `catalogo.ubicaciones` es el mismo mapa que valida |

## 14 · Riesgos y alternativas descartadas

1. **Actualizar la bandeja en sitio** (D-3): pierde lo que mandó la propiedad.
2. **Guardar el estado**: diverge del histórico (lección F-026 → F-028).
3. **Bloqueo consultivo**: espacio de claves compartido con otros proyectos.
4. **Validar contra el catálogo de la importación**: es lo que dejó viejos los
   144.
5. **Paginar en SQL** (`LIMIT`/`OFFSET` o keyset con los filtros en la
   consulta): el estado y los motivos se calculan en el dominio (el segundo,
   con el catálogo de Sigrid); llevarlos a SQL duplicaría las reglas. Se lee la
   obra entera con tope explícito y se pagina en Python.
6. **Riesgo: obras de más de 10.000 incidencias**: 409 explícito, nunca
   truncado; si llega a pasar, paginar en SQL por estado guardado sería otra
   ficha.
7. **Riesgo: cada página relee Sigrid** (tres `sql/read` pequeñas con la de
   ubicaciones); aceptado.
8. **Riesgo: el correo** amplía lo que se guarda de las personas; acotado a
   una tabla, sin logs, solo a usuarios autenticados del grupo (§9).
9. **Riesgo: conflicto con F-053** en `docs/INTEGRACION.md` §8 y
   `azure-apps/postventa_incidencias.md`; el código no se cruza.

## 15 · Decisiones (aprobadas por el humano el 2026-10-06)

| Id | Decisión |
|---|---|
| D-1 | Partir: F-056 (este backend) va antes; F-038 (front y cierre) queda bloqueada por ella |
| D-3 | Una foto completa por acción en `revisiones_bandeja`, append-only; la bandeja intacta |
| D-4 | **Ubicación obligatoria para aprobar** (`sin_ubicacion`) y, si la hay, **contra Sigrid en vivo** al editar y al aprobar (decisión del humano 2026-10-06; ya no la lista de la plantilla). Fuente: la tipología de la unidad (Q-5, §16) |
| Q-5 | **Resuelta el 2026-10-06** (T0 del humano; el líder, opción a): `prmtpl.ubica` de la tipología de cada unidad, por unidad, exacta tras recortar (§16) |
| D-5 | Duplicada no aprobable mientras la original no esté descartada y las claves coincidan |
| D-6 | Se puede recuperar una descartada |
| D-7 | Una aprobada se puede editar (pierde la aprobación) o descartar |
| D-8 | **Se guarda y se enseña el correo** de quien actúa, junto al `oid` (§9); nunca en logs |
| D-9 | Motivo de descarte libre, opcional, ≤ 500; solo en el historial |
| D-10 | Los 144 se ven y se corrigen editando; no se reimporta |
| D-13 | `oid` y correo del cuerpo, de `/.auth/me` |
| D-14 | Sin Sigrid, 503 al listar |
| Q-1 | Basta con el desfase con Sigrid de hoy |
| Q-2 | **Se pagina** (§4, §7, §8) |
| Q-3 | Cualquiera de `posventa-usuarios` |
| Q-4 | Merge normal a `dev` |

D-2, D-11 y D-12 son de F-038.

## 16 · Q-5 · De dónde salen las ubicaciones válidas en Sigrid — RESUELTA

### 16.1 · Lo que había y lo que se midió

Antes de medir (`azure-apps/sigrid_tablas.md`, `docs/referencia/04_alta_incidencia_sigrid.md`,
`infra/24_ubicacion_sigrid.ps1`, D-3 de F-036): `rcp.resubi` es texto libre de
48 sin catálogo; `upv.espacios` estaba vacío en la 0677; `auxubi` y
`auxobrubi` son de almacén y de la situación de la obra; y la única candidata
a maestro era `prmtpl.ubica`, «Ubicaciones» de la **tipología** de la
promoción, a la que apunta cada unidad con `upv.obrtplide`. Opciones que se
plantearon: (a) esa tipología, con medición previa; (b) `DISTINCT rcp.resubi`
de la obra; (c) (b) más la lista de la plantilla; (d) sin lista.

**Medición T0** (el humano, 2026-10-06, script de solo lectura fuera del
repositorio sobre `08_lectura_sigrid_comun.ps1`; solo recuentos), en la 0677:

| Qué | Resultado |
|---|---|
| Unidades de posventa / sin tipología (`upv.obrtplide`) / tipologías distintas | 15 / 0 / 3 |
| `prmtpl.ubica` relleno | En las 3 |
| Separador | Punto y coma (`;`) |
| Ubicaciones por tipología | 35, 37 y 31; 58 distintas en la unión (normalizada) |
| Ubicaciones distintas usadas en reclamaciones (`rcp.resubi`, tip 708) que casan **exactas** con la unión, recortando blancos | 44 de 44 |
| Reclamaciones cubiertas | 1.261 de 1.261 |
| Calidad | La lista trae alguna errata propia de Sigrid y variantes de mayúsculas: es su dato y **se respeta tal cual** |

**Decisión** (el líder, con el dato, dentro de la opción a que el humano pidió
medir): **(a), la tipología de la unidad**, **por unidad**, comparación
**exacta tras recortar**.

### 16.2 · La regla (R47, R48)

- Por cada unidad de la obra, su lista es `prmtpl.ubica` de su tipología,
  partida por `;`, cada valor recortado por los extremos, sin vacíos ni
  valores de más de 48, en su orden, quitando solo los **repetidos exactos**.
  No se deduplica por mayúsculas ni se corrigen erratas: dos valores que
  difieren en una mayúscula son dos opciones.
- Una unidad sin tipología, o con `ubica` vacía o `NULL`, tiene lista vacía:
  sus incidencias no se pueden aprobar con ubicación (todas saldrán con
  `ubicacion_fuera_de_lista` o `sin_ubicacion`). En la 0677 no pasa (0 sin
  tipología).
- La ubicación de una incidencia vale SI, recortada, es exactamente uno de los
  valores de la lista **de su unidad** (no de otra unidad de la obra). Al
  editar, se valida contra la unidad **pedida**: cambiar la unidad revalida la
  ubicación (R13).

### 16.3 · La tercera lectura (R46)

Módulo puro nuevo `infrastructure/sigrid/consultas_ubicaciones_validas.py`,
como `consultas_catalogo.py` (que **no** se toca), con el mismo filtro de obra
que `SQL_UNIDADES_DE_LA_OBRA` (código **literal**, la obra ya resuelta como
única por `leer_catalogo`, que va **antes**):

```sql
-- SQL_UBICACIONES_DE_LAS_UNIDADES · parámetro: el código de obra normalizado
SELECT u.cod, CAST(t.ubica AS nvarchar(max))
FROM dbo.upv v
JOIN dbo.con o ON o.ide = v.obride
JOIN dbo.con u ON u.ide = v.ide
LEFT JOIN dbo.prmtpl t ON t.ide = v.obrtplide
WHERE LTRIM(RTRIM(o.cod)) = ?
ORDER BY u.cod
```

- Una fila por unidad (15 en la 0677). `max_rows` = `MAX_FILAS_CATALOGO`
  (1.000) y el mismo tratamiento de `truncated` que el adaptador del catálogo:
  al techo → `CatalogoSinVerificar` (**409**); cortada por debajo del techo o
  respuesta mal formada → `CatalogoNoDisponible` (**503**); lo transitorio se
  reintenta como allí. Sigrid caído → **503** sin escribir (D-14).
- Puerto `domain/ports/ubicaciones_validas.py`:
  `UbicacionesValidasPort.leer(*, codigo_obra) -> LecturaCatalogo[FilaUbicacionesUnidad]`
  (`FilaUbicacionesUnidad(unidad_codigo, ubica: str | None)`; reutiliza
  `LecturaCatalogo` de `domain/ports/catalogo_obra.py`, sin modificarlo).
  Adaptador `infrastructure/sigrid/ubicaciones_validas.py`, con la misma
  puerta de entorno y el mismo cliente que `catalogo_obra.py`;
  `construir_ubicaciones_validas(ajustes)` se **añade** a
  `infrastructure/sigrid/fabrica.py`.
- La aplicación: tras `leer_catalogo`, `UbicacionesValidasPort.leer` →
  `{unidad_codigo: ubicaciones_de_tipologia(ubica)}` para las unidades del
  catálogo (una unidad del catálogo sin fila en la lectura → lista vacía; una
  fila de una unidad que no está en el catálogo se ignora).
- **Una vez por petición**: `GET /api/revision` (cada página), `editar` y
  `aprobar`; nunca en `descartar`, `recuperar` ni el historial. **Sin caché
  entre peticiones**.
- **Lo elegible es lo aprobable**: `catalogo.ubicaciones` de la respuesta es
  este mismo mapa (`{unidad_codigo: [ubicaciones]}`) y F-038 ofrece las de la
  unidad elegida.
- **El texto de `ubica` no va a ningún log** (puede ser largo y es dato de
  Sigrid); el log dice cuántas unidades y cuántas sin tipología.
- **§8.9 (F-040)**: lo aprobado es un texto de ≤ 48 que estaba en la
  tipología de su unidad el día de la aprobación; §8.9 lo escribe en
  `rcp.resubi` sin validarlo, así que el dry-run de F-040 no lo rechazará por
  la ubicación. Si F-040 quiere volver a comprobarlo, usa este mismo puerto.

### 16.4 · La plantilla Excel de F-036

**No se toca aquí.** Su desplegable de `Ubicación` sigue saliendo de
`config/plantilla_incidencias.yaml` (la lista de la obra piloto, normalizada),
igual para todas las filas. Puede pasar que una ubicación de la plantilla no
esté en la tipología de la unidad de su fila: la fila entra en la bandeja y
aquí sale con `ubicacion_fuera_de_lista` hasta que se corrija. **Propuesta**:
una **ficha aparte** para que la plantilla ofrezca las ubicaciones de la
tipología **de la unidad de cada fila** (propuesta de alta en
`progress/spec_F-038.md`).
