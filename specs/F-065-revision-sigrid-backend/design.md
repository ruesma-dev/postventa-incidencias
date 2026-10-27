<!-- specs/F-065-revision-sigrid-backend/design.md -->
# F-065 · Las reclamaciones de Sigrid en la revisión, en el backend — Diseño

> **Tramo A de la spec conjunta de F-064** (Q-1, aprobada por el humano el
> 2026-10-21). La página es F-064 (`specs/F-064-bandeja-con-sigrid/`).
> **Spec aprobada por el humano el 2026-10-21**: Q-1 a Q-10 y N-1 a N-3
> (§14).
>
> Base: `dev` `383bfd5`. Documentos contra los que se diseña:
> `docs/ARCHITECTURE.md` (F-036, F-056, F-038, F-060, F-059 y «Acceso a datos
> y sistemas externos»), `docs/CONVENTIONS.md`, `CHECKPOINTS.md`,
> `docs/referencia/03_modelo_posventa_sigrid.md`, `azure-apps/sigrid_api.md`
> (§4.1, §6, §8.9, §9) y `azure-apps/sigrid_tablas.md` (`con`, `rcp`,
> `conext`, `upv`, `per`, `auxofc`, `auxtrcp`, `auxrcp`). **No se ha consultado
> Sigrid ni la base**: lo que hay que medir está en `tasks.md` (T-A0).

## 0 · En una página

- **Una ruta nueva de solo lectura**, `GET /api/revision/sigrid?obra=`:
  **todas** las reclamaciones de la obra (Q-2) **con sus datos** —también los
  personales de la lista cerrada de R33 (Q-6, N-3)—, emparejadas con la bandeja
  por la referencia `PVI-` y cruzadas con tres criterios; devuelve las
  reclamaciones y los **hallazgos** (conflictos y avisos). La página filtra y
  busca sobre ellas (por propietario o teléfono, también).
- **Aparte del listado** (Q-5): `GET /api/revision` no cambia; si Sigrid falla,
  la bandeja sigue.
- **Una lectura con el techo de la pasarela, 500.000 filas**, comprobando
  `truncated` (N-1): nunca conflictos a medias.
- **Un conflicto avisa, no bloquea** (Q-4).
- **Ni un dato personal en logs, en la base ni en el repositorio** (Q-6).

## 1 · El límite de servicio

Leer Sigrid y cruzar es del backend (`services/postventa-api`, el único que
habla con `sigrid-api` y el dueño de las reglas de la bandeja); enseñarlo es
del front (F-064). Orden: **F-038 → F-065 → F-064 → F-040**. Nada de otro
proyecto: `sigrid-api` ya sirve `sql/read` con 500.000 filas; el portal
corporativo no cambia.

## 2 · Encaje en la arquitectura

```
GET /api/revision/sigrid?obra=
  interface_adapters/api/sigrid_bandeja.py     valida, construye (Sigrid → base), mide, serializa, no-store
    application/pipelines/sigrid_bandeja.py    mirar_sigrid: base → (tope) → Sigrid → (truncated, obras) → cruzar
      domain/models/sigrid_bandeja.py          puro: referencia, emparejar, criterios, parecido, severidad, orden
      domain/ports/reclamaciones_obra.py       ReclamacionesObraPort (nuevo) + RevisionPort (F-056, sin cambiar)
    infrastructure/sigrid/reclamaciones_obra.py             hereda AdaptadorCatalogoSigridApi (F-036) sin tocarlo
    infrastructure/sigrid/consultas_reclamaciones_obra.py   el SQL, puro, comprobado carácter a carácter
```

- **El dominio** importa solo del dominio (`revision.py`: `estado_de`,
  `valores_vigentes`; `normalizacion.py`: `clave_de_ubicacion`;
  `plantilla_incidencias.py`: `normalizar_para_clave`, `plegar`; `volcado.py`:
  `PREFIJO_REFERENCIA`) y **no modifica** ninguno.
- **El adaptador hereda** el de F-036, como `ubicaciones_validas.py` (F-056):
  la misma puerta, el mismo cliente, los mismos reintentos y errores. Pero su
  lectura es **otra regla**: pide 500.000 filas y un `truncated` es **409**,
  no el 503 de «cortada por debajo del techo» de F-036. Así que compone su
  propio `_leer` con las piezas heredadas (`_un_intento`, `_mapear`, la
  política de `tenacity`, `_cabeceras`, `_cliente_http`) **sin tocar
  `catalogo_obra.py`** (D-9), y devuelve la lectura con `llego_al_techo`
  (filas ≥ tope **o** `truncated`).
- **Sin DDL, sin variables nuevas, sin caché.**

## 3 · La consulta (`SQL_RECLAMACIONES_DE_LA_OBRA`)

```sql
SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt,
       CAST(r.tex AS nvarchar(max)), r.motrcp, r.texurg, r.rcptip, r.fecpre,
       CAST(r.solrcp AS nvarchar(max)), k.cod, k.res,
       CAST(r.tel AS nvarchar(max)), CAST(r.ele AS nvarchar(max)),
       cl.res, pr.nom, pr.tel, pr.tel2, pr.ele, pc.nom, pc.tel, pc.tel2, pc.ele
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
LEFT JOIN dbo.auxrcp k ON k.ide = r.rcpide
LEFT JOIN dbo.con cl ON cl.ide = r.cliide
LEFT JOIN dbo.per pr ON pr.ide = r.recide
LEFT JOIN dbo.per pc ON pc.ide = r.cntide
OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x
             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?
             ORDER BY x.ide) p
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?
ORDER BY c.cod
```

Treinta y una columnas. Parámetros: `RCPCLI`, `PVI-%`, el tipo y la obra
normalizada.

- Parte de `rcp` y sube a la obra por la UPV, como los scripts 24 y 28; el
  filtro de obra es **el mismo** que el de las unidades de F-036.
- La referencia, en un `OUTER APPLY … TOP 1`: un `LEFT JOIN` duplicaría la
  reclamación con dos filas `RCPCLI`, y el `LIKE 'PVI-%'` hace que una
  referencia que **no** es nuestra no se lea.
- **Todos los estados y todas las fechas** (Q-2). El estado, por código.
- **Los campos personales** (R33) son una **lista cerrada** escrita en el
  texto: un test comprueba que no nombra `dni`, `esiglog`, `esigpas`,
  `clamai`, `dir`, `dir1`, `dir2` ni `per.tex`. Los `text` de Sigrid van con
  `CAST(... AS nvarchar(max))` (la forma de F-056; §6.6 de la pasarela).
- **La fecha** es `con.fec`; si T-A0 dice que la que ve Posventa es
  `rcp.fec`, se cambia una columna y un test.
- **`OUTER APPLY`, rendimiento** (cuatro `LEFT JOIN` más y `conext` sin índice
  documentado por `conide`) **y tamaño**: los mide T-A0 con el mismo texto.
  Alternativas escritas: la subconsulta escalar `(SELECT MIN(x.valt) …)` en vez
  del `OUTER APPLY`; o los partes `PVI-` aparte con la forma del script 28.

## 4 · El volumen (Q-2 y N-1, aprobadas el 2026-10-21)

La 0677 tiene **≈ 1.276** reclamaciones. Decisión del humano: **una sola
lectura con el techo de la pasarela**, `MAX_ALLOWED_ROWS` = **500.000** en la
instancia desplegada («sigrid admite hasta 500k en la api»).

- **`max_rows` 500.000** (`TOPE_RECLAMACIONES_OBRA`, constante del dominio).
  Si la respuesta trae `truncated` o llega a ese número, **409
  `reclamaciones_sin_verificar`** y ningún conflicto calculado. La pasarela
  dice que `truncated` es el aviso que no hay que ignorar (§6.3): aquí es un
  error claro.
- **Los tiempos**: el balanceador corta a 230 s, pero nuestra lectura corta
  antes (`SIGRID_TIMEOUT_S`, 35 s) y el proxy de la Static Web App a los 45 s.
  Con ≈ 1.276 filas no se espera acercarse; T-A0 mide segundos y **bytes con
  todos los campos de R33** en la 0677.
- **Contingencia** (escrita, no implementada): si T-A0 mide más de ≈ 10 s, o
  una respuesta que pese demasiado para la página, la lectura se hace **por
  trozos** con `OFFSET … FETCH` y `ORDER BY c.cod` (§6.4 de la pasarela),
  dentro del adaptador y con el mismo resultado; se enmienda la spec antes del
  Bloque A3.
- **Sin cursor en la ruta**: los conflictos se calculan contra **todas** las
  reclamaciones de la obra, y los filtros y la búsqueda de la página (también
  por propietario o teléfono) necesitan la lista entera.

**La bandeja no se cae ni se ralentiza**: es otra petición (§7); el listado de
F-056 no hace ni una lectura más.

## 5 · Emparejar y cruzar

### 5.1 · Por la referencia `PVI-`

La referencia de F-059 es `PVI-` + el `incidencia_id` canónico
(`volcado.py::referencia_de`). La pasarela compara sin distinguir mayúsculas;
aquí también (`incidencia_de_referencia`).

| Situación | Hallazgo | Severidad |
|---|---|---|
| `PVI-<id>` de una incidencia de la obra que **no** está `volcada` | `ya_en_sigrid` | conflicto |
| Dos o más `PVI-<id>` de la misma incidencia | `varias_en_sigrid` | conflicto |
| Incidencia `volcada` sin reclamación emparejada | `volcada_no_encontrada` | aviso |
| Incidencia `volcada` emparejada con otro código que el guardado | `codigo_distinto` | aviso |
| Incidencia `volcada` emparejada con una `NPR` | `anulada_en_sigrid` | aviso |
| `PVI-` sin UUID o de una incidencia que no es de esta obra | `referencia_desconocida` | aviso |

`ya_en_sigrid` es típicamente una `en_duda` cuyo volcado sí llegó: **ensayar y
volcar de nuevo la deja `volcada` sin crear otro parte** (la pasarela devuelve
`idempotente`). Una incidencia emparejada no choca consigo misma (R13); su
reclamación sí con las demás: es el criterio del humano «la fila del Excel que
ya se volcó desde el portal», en sus dos sentidos (Q-3).

### 5.2 · Los criterios (Q-3, aprobada el 2026-10-21)

Se cruzan las incidencias **evaluables** (`nueva`, `editada`, `aprobada`,
`en_duda`) con **todas** las reclamaciones de su **misma unidad** (el índice es
por unidad: una unidad tiene decenas de reclamaciones, así que el cruce es
barato aunque la obra tenga miles).

| Criterio | Regla |
|---|---|
| **`misma_unidad_oficio_ubicacion`** | unidad y oficio por código exacto; ubicación por `clave_de_ubicacion` (F-060). Sin oficio en un lado, no se evalúa; ubicación vacía no casa |
| **`misma_unidad_descripcion_parecida`** | misma unidad y **parecido ≥ 50 con ≥ 2 palabras en común**, o la misma descripción normalizada (parecido 100). §5.3 |

**Severidad**: conflicto si la reclamación está en `SAT`/`PTE`; **aviso**
(reincidencia) si está en `TER`/`CER`, **de cualquier fecha** (Q-2: no hay
corte; la página filtra por fecha). `NPR` y estados desconocidos no dan pares.

### 5.3 · El parecido de dos descripciones (N-2, aprobada el 2026-10-21)

Jaccard sobre palabras significativas, sin IA ni distancia de edición:

1. `plegar` (F-036): sin tildes, minúsculas, blancos colapsados.
2. Partir por todo lo que no sea letra o cifra.
3. Quitar las de menos de 3 caracteres y las de `PALABRAS_VACIAS` (lista
   cerrada del dominio: `del`, `las`, `los`, `con`, `por`, `para`, `que`,
   `sus`, `una`, `unos`, `unas`, `muy`, `mas`, `sin`, `sobre`, `entre`, `hay`,
   `esta`, `este`, `esto`, `son`, `como`, `han`, `tiene`).
4. Quitar la `s` final a las de 5 o más caracteres (plural simple).
5. Parecido = `floor(100 × |A ∩ B| / |A ∪ B|)`; 100 si las
   `normalizar_para_clave` son iguales; 0 si un lado se queda vacío.
6. Casa con **parecido ≥ 50 y ≥ 2 palabras en común** (o 100).

El umbral (`UMBRAL_PARECIDO`, 50) es una **constante del dominio**; T-A0
cuenta, dentro de Sigrid, cuántos pares de una misma unidad pasarían con 40,
50 y 60, y con eso el humano confirma o mueve el número antes del Bloque A2.

### 5.4 · Ejemplos (ficticios)

Unidad `VILLA 05`, oficio `0039`, salvo que se diga otra cosa.

| # | Bandeja (vigentes) | Sigrid | Resultado |
|---|---|---|---|
| E1 | `nueva` · Cocina · 0039 · «Gotea el grifo» | RS26.09/0123 · **PTE** · Cocina · 0039 · «Fuga bajo el fregadero» | `coincide` [oficio-ubicación] · **conflicto** |
| E2 | `editada` · Baño principal · 0012 · «Silicona negra en bañera» | RS26.08/0045 · **SAT** · Baño 1 · 0050 · «Silicona negra en bañera.» | `coincide` [descripción, parecido 100] · **conflicto** |
| E2b | `nueva` · Baño principal · 0012 · «Silicona negra en bañera» | RS26.08/0046 · **SAT** · «Cambiar silicona bañera» | {silicona, negra, banera} y {cambiar, silicona, banera}: 2 de 4 → **50**, 2 en común → `coincide` · conflicto |
| E2c | `nueva` · «Humedad en techo del baño» | RS26.08/0047 · **SAT** · «Mancha de humedad en pared del salón» | {humedad, techo, bano} y {mancha, humedad, pared, salon}: 1 de 6 → 16 → nada |
| E2d | `nueva` · «Grifos sueltos» | RS26.08/0048 · **SAT** · «Grifo suelto en cocina» | {grifo, suelto} y {grifo, suelto, cocina}: 2 de 3 → 66 → `coincide` |
| E3 | como E1 | RS26.03/0456 · **CER** (hace 7 meses) · Cocina · 0039 | `coincide` · **aviso** (reincidencia) |
| E4 | como E1 | RS23.06/0300 · **CER** (hace 40 meses) | `coincide` · **aviso** (se lee todo; la página filtra por fecha) |
| E5 | como E1 | RS26.09/0200 · **NPR** · Cocina · 0039 | nada |
| E6 | A `volcada` como RS26.10/0074; B `nueva` · Cocina · 0039 | RS26.10/0074 · SAT · `PVI-<A>` · Cocina · 0039 | A: emparejada, sin hallazgo. B: `coincide` · conflicto, «volcada desde el portal» |
| E7 | X `en_duda` | RS26.10/0080 · SAT · `PVI-<X>` | `ya_en_sigrid` · conflicto |
| E8 | — | RS26.09/0439 · `PVI-PRUEBA-0001` (la prueba de la pasarela en la 0626) | `referencia_desconocida` · aviso |
| E9 | `nueva` · **COCINA** · 0039 | E1 | casa (misma clave de ubicación) |
| E10 | `nueva` · Cocina **1** · 0039 | E1 | no casa por ubicación |
| E11 | `nueva` · Cocina · oficio **ambiguo** | E1 | solo se evalúa la descripción |
| E12 | `descartada` · como E1 | E1 | nada |
| E13 | Y `volcada` como RS26.10/0090 | ninguna con `PVI-<Y>` | `volcada_no_encontrada` · aviso |

## 6 · ¿Un conflicto impide aprobar? (Q-4, aprobada el 2026-10-21)

**No.** El backend no gana motivo de no aprobable ni cambia la acción de
F-056; la página pide un segundo clic «Aprobar a pesar del conflicto» (F-064
R58). Descartadas: el motivo nuevo (bloquea sin salida para un falso positivo,
y aceptarlo pediría DDL) y la confirmación en el backend (cambia el contrato y
añade una lectura de Sigrid a cada aprobación).

## 7 · Aparte del listado, el coste y si Sigrid no responde (Q-5, aprobada)

- **Una ruta aparte**, pedida por la página a la vez que el listado: el
  listado sigue igual (≈ 5 s p50); si esta lectura falla, solo el panel lo
  dice; los contratos y las guardas de F-056/F-060 no se tocan.
- **Coste**: una lectura de la base + una de Sigrid por carga de la página y
  por «Volver a mirar Sigrid»; **ninguna** por «Ver más», filtro, búsqueda ni
  acción.
- **Sin caché** (D-7): tras un volcado, una caché enseñaría
  `volcada_no_encontrada` de un parte que existe; Flex reparte las peticiones
  entre instancias; las cachés del listado son de F-061. Y con datos
  personales, cuanto menos se guarde, mejor (R37).
- **Si Sigrid no responde**: 503 de esta ruta, con los reintentos y el tiempo
  de F-036; la página sigue entera (F-064 R51).

## 8 · Datos personales y seguridad (Q-6 y N-3, aprobadas el 2026-10-21)

**Decisión del humano**: los datos personales de la reclamación **sí** se
enseñan en la página, porque la usa personal interno del grupo, y **viajan en
el listado** («si los datos personales son necesarios no hay problema con que
viajen»): lo que pesa es poder **buscar y filtrar por propietario o teléfono**.
La ficha bajo demanda que se propuso desaparece.

**Qué viaja** (R6, R33): lo de trabajo (código, estado, fecha, unidad,
ubicación, oficio, tipo, descripción corta, referencia `PVI-`) y la lista
cerrada de R33 (descripción larga, motivo, urgencia, forma de comunicación,
fecha prevista, solución, clase, teléfonos y correo adicional de avisos,
propietario, persona que reclama y persona de contacto con sus teléfonos y
correo). **Nunca**: `per.dni`, las credenciales de i-Sigrid (`per.esiglog`,
`per.esigpas`, `per.clamai`, que existen en la tabla `per`), direcciones,
observaciones de la persona ni ningún `ide`. Ampliar la lista es decisión del
humano.

Lo que sigue en pie por las reglas del proyecto:

| Dónde | Regla |
|---|---|
| **Logs y trazas** | Nunca. Solo la obra, códigos de resultado, recuentos, bytes y segundos (R24, R25, R38) |
| **Nuestra base** | Nunca: se leen de Sigrid y se sirven (R37) |
| **Repositorio, specs, progress, tests** | Nunca valores reales: «Ejemplo …», `@ejemplo.invalid`, `000 000 000` (R39) |
| **Navegador** | `Cache-Control: no-store` (R35); la página no los guarda en el almacenamiento ni los manda a la consola (F-064 R62) |
| **Mensajes de error y excepciones** | No repiten filas; las filas del puerto no imprimen valores en su `repr` (R22, R40) |

## 9 · Ficheros

### 9.1 · A crear

| Ruta | Qué |
|---|---|
| `services/postventa-api/domain/models/sigrid_bandeja.py` | El dominio puro (§10.1) |
| `services/postventa-api/domain/ports/reclamaciones_obra.py` | `FilaReclamacionObra`, `FichaReclamacion` y `ReclamacionesObraPort` |
| `services/postventa-api/infrastructure/sigrid/consultas_reclamaciones_obra.py` | El SQL de §3, sus parámetros y el mapeo |
| `services/postventa-api/infrastructure/sigrid/reclamaciones_obra.py` | `AdaptadorReclamacionesObraSigridApi(AdaptadorCatalogoSigridApi)` |
| `services/postventa-api/application/pipelines/sigrid_bandeja.py` | `mirar_sigrid` y `VistaDeSigrid` |
| `services/postventa-api/interface_adapters/api/sigrid_bandeja.py` | `sigrid_de_la_bandeja` |
| `infra/29_reclamaciones_obra_sigrid.ps1` | La medición de R29 |
| `services/postventa-api/tests/test_f065_dominio.py` | R10–R19, R36 |
| `services/postventa-api/tests/test_f065_consulta.py` | R5, R6, R33 |
| `services/postventa-api/tests/test_f065_adaptador.py` | R2, R8, R25, R27, R40 |
| `services/postventa-api/tests/test_f065_aplicacion.py` | R3, R4, R8, R9 |
| `services/postventa-api/tests/test_f065_http.py` | R1, R20–R24, R35, R38 |
| `services/postventa-api/tests/test_f065_datos_personales.py` | R37–R39 |
| `services/postventa-api/tests/test_f065_alcance_cerrado.py` | R26–R28 |
| `services/postventa-api/tests/test_f065_scripts_infra.py` | R29 |
| `services/postventa-api/tests/test_f065_documentacion.py` | R30 |

### 9.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `infrastructure/sigrid/fabrica.py` | `construir_reclamaciones_obra(ajustes)`, con las dos puertas de `construir_ubicaciones_validas`. Nada más |
| `domain/models/errores.py` | `ReclamacionesSinVerificar` (409, con `filas`). Nada más |
| `function_app.py` | La ruta `revision/sigrid`, su traducción de errores y un `_json_sin_cache` (el `_json` de siempre más `Cache-Control: no-store`), usado **solo** por ella; su párrafo en la cabecera |
| `docs/ARCHITECTURE.md` | Sección «Las reclamaciones de Sigrid en la revisión (F-065)» y la fila `sigrid-api` |
| `docs/INTEGRACION.md` | §1 la cuarta lectura; §4 «Las de F-065: ninguna» |
| `azure-apps/postventa_incidencias.md` | Lo mismo, en el mismo trabajo |
| `azure-apps/sigrid_api.md` | La fila de `postventa-incidencias` en consumidores (§10) |

### 9.3 · Lo que NO se toca

`domain/models/revision.py`, `application/pipelines/revision.py`,
`interface_adapters/api/revision.py`; `catalogo_obra.py`,
`consultas_catalogo.py`, `ubicaciones_validas.py`; todo el volcado;
`normalizacion.py`, `plantilla_incidencias.py` (se usan sus funciones);
`interface_adapters/api/tiempos.py`; `config/settings.py`; `sql/`;
`requirements.txt`; `services/postventa-front/` (es F-064).

## 10 · Clases y funciones

### 10.1 · Dominio — `domain/models/sigrid_bandeja.py`

```python
class EstadoSigrid(StrEnum):  SAT = "SAT"; PTE = "PTE"; TER = "TER"; CER = "CER"; NPR = "NPR"
ABIERTAS = frozenset({EstadoSigrid.SAT, EstadoSigrid.PTE})
CERRADAS = frozenset({EstadoSigrid.TER, EstadoSigrid.CER})
TOPE_RECLAMACIONES_OBRA = 500_000     # N-1: el MAX_ALLOWED_ROWS de la pasarela desplegada
TOPE_COINCIDENCIAS = 10               # R18
UMBRAL_PARECIDO = 50                  # N-2
MIN_PALABRAS_COMUNES = 2              # N-2
PALABRAS_VACIAS: frozenset[str]       # §5.3

class Severidad(StrEnum):    CONFLICTO, AVISO
class Criterio(StrEnum):     MISMA_UNIDAD_OFICIO_UBICACION, MISMA_UNIDAD_DESCRIPCION_PARECIDA
class TipoHallazgo(StrEnum): COINCIDE, YA_EN_SIGRID, VARIAS_EN_SIGRID, VOLCADA_NO_ENCONTRADA,
                             CODIGO_DISTINTO, ANULADA_EN_SIGRID, REFERENCIA_DESCONOCIDA

@dataclass(frozen=True)
class ReclamacionSigrid:
    cod: str; estado: str | None; fecha: date | None; unidad_codigo: str | None
    ubicacion: str | None; oficio_codigo: str | None; oficio_nombre: str | None
    tipo_codigo: str | None; tipo_nombre: str | None; descripcion: str | None
    referencia: str | None
    ficha: FichaReclamacion = field(repr=False)   # R33; el cruce no la mira

@dataclass(frozen=True)
class Hallazgo:
    tipo: TipoHallazgo; severidad: Severidad; incidencia_id: UUID | None
    sigrid_cod: str | None; sigrid_cods: tuple[str, ...] = ()
    criterios: tuple[Criterio, ...] = (); parecido: int | None = None

@dataclass(frozen=True)
class Cruce:
    reclamaciones: tuple[tuple[ReclamacionSigrid, UUID | None], ...]
    hallazgos: tuple[Hallazgo, ...]
    coincidencias_total: Mapping[UUID, int]
    evaluadas: int
    estados_desconocidos: int

def palabras_significativas(texto: str | None) -> frozenset[str]: ...   # R36
def parecido(a: str | None, b: str | None) -> int: ...                  # R36
def incidencia_de_referencia(referencia: str | None) -> UUID | None: ...# R10
def cruzar(situaciones: Sequence[SituacionDeRevision],
           reclamaciones: Sequence[ReclamacionSigrid]) -> Cruce: ...    # R10–R18
```

### 10.2 · Puerto — `domain/ports/reclamaciones_obra.py`

```python
@dataclass(frozen=True)
class FichaReclamacion:      # la lista cerrada de R33; todos los campos con repr=False
    descripcion_larga: str | None; motivo: str | None; urgencia: str | None
    forma_comunicacion: int | None; fecha_prevista: date | None; solucion: str | None
    clase_codigo: str | None; clase_nombre: str | None
    telefonos_avisos: str | None; correo_avisos: str | None; propietario: str | None
    reclama_nombre: str | None; reclama_telefono: str | None; reclama_telefono2: str | None
    reclama_correo: str | None; contacto_nombre: str | None; contacto_telefono: str | None
    contacto_telefono2: str | None; contacto_correo: str | None

@dataclass(frozen=True)
class FilaReclamacionObra:   # las 31 columnas de §3; obra_ref nunca sale; textos con repr=False
    obra_ref: str; cod: str; estado_codigo: str | None; fecha: date | None
    unidad_codigo: str | None; oficio_codigo: str | None; oficio_nombre: str | None
    tipo_codigo: str | None; tipo_nombre: str | None; ubicacion: str | None
    descripcion: str | None; referencia: str | None; ficha: FichaReclamacion

class ReclamacionesObraPort(Protocol):
    def leer(self, *, codigo_obra: str, tip: int) -> LecturaCatalogo[FilaReclamacionObra]: ...
```

`FichaReclamacion` vive en el puerto (es lo que llega de Sigrid) y el dominio
la importa del puerto sin mirarla: solo la lleva. Si el reviewer prefiere el
sentido contrario (dominio → puerto), se mueve a `domain/models/` sin cambiar
nada más.

### 10.3 · Aplicación — `application/pipelines/sigrid_bandeja.py`

```python
def mirar_sigrid(obra_codigo: str, *, revision: RevisionPort,
                 reclamaciones: ReclamacionesObraPort, tip: int) -> VistaDeSigrid: ...
```

`revision.listar(tope=TOPE_LECTURA_OBRA)` → si pasa, `contar` y
`BandejaDemasiadoGrande` sin leer Sigrid → `reclamaciones.leer` → techo o
`truncated`: `ReclamacionesSinVerificar` → varios `obra_ref`: `ObraAmbigua` →
`cruzar`.

### 10.4 · Borde — `interface_adapters/api/sigrid_bandeja.py`

```python
def sigrid_de_la_bandeja(obra: Any, *, revision=None, reclamaciones=None) -> dict[str, Any]: ...
```

Valida antes de construir (R1), construye Sigrid y después la base (R2), mide
con `Cronometro`, serializa (R20, R21) y deja su línea en un `finally` (R24,
R38), con los bytes del cuerpo serializado. Las fábricas de módulo son la
costura de test.

## 11 · Medición previa (T-A0)

El script 29 se escribe en el Bloque A1 y lo lanza el humano para la 0677 y la
0626 **antes** del dominio: filas, `truncated`, **bytes con todos los campos**
y los de R33 aparte, segundos, si la pasarela acepta el `OUTER APPLY`,
población por estado y antigüedad, por unidad, cuántas traen cada campo de
R33, ruido de R14 dentro de Sigrid, pares de descripción parecida con
40/50/60, y `con.fec` frente a `rcp.fec`. Si los segundos pasan de ≈ 10 o el
tamaño no le cabe a la página, se aplica la contingencia de §4 enmendando la
spec **antes** del Bloque A2; si el umbral o la fecha cambian, también.

## 12 · Riesgos y decisiones

| # | Decisión | Por qué / alternativa |
|---|---|---|
| D-1 | Dos tramos, este primero (Q-1) | Límite de servicio |
| D-2 | Ruta aparte (Q-5) | §7 |
| D-3 | Todas las reclamaciones de la obra (Q-2) | Filtros en la página |
| D-4 | Criterios de §5 (Q-3) | — |
| D-5 | No bloquea (Q-4) | §6 |
| D-6 | Datos personales en la página, nunca en logs, base ni repositorio (Q-6) | §8 |
| D-7 | Sin caché, sin variables nuevas | §7 |
| D-8 | Una lectura con el techo de la pasarela, 500.000, y `truncated` = 409 (N-1) | §4; por trozos si T-A0 lo pide |
| D-9 | El adaptador hereda el de F-036 sin tocarlo, con su propia lectura | Dos copias divergen; la regla del techo es otra |
| D-10 | Dominio en módulo nuevo; `revision.py` intacto | Guardas de F-056/F-059/F-060 y R26 |
| D-11 | Tope de 10 pares por incidencia, con el total | — |
| D-12 | Jaccard, umbral 50 y 2 en común (N-2) | §5.3 |
| D-13 | Todo en el listado, una sola ruta, con lista cerrada (N-3) | §8 |

Todas **aprobadas por el humano el 2026-10-21**.

**Riesgos**:

- **Datos personales de toda la obra en cada carga, visibles a todo
  `posventa-usuarios`** —**decisión del humano del 2026-10-21 (Q-6, N-3)**—.
  Hoy el grupo son 7 personas (ARCHITECTURE, fila Entra ID); el riesgo crece
  con él. Viajan en bloque (la agenda de la promoción entera en cada carga)
  para poder buscar por propietario o teléfono. Mitigado con la lista cerrada
  (sin DNI ni credenciales), `no-store`, nada en logs ni en la base y nada en
  el almacenamiento del navegador. **Lo asume el humano.**
- **Tamaño de la respuesta** con la descripción larga y la solución (texto
  ilimitado): T-A0 lo mide en la 0677; contingencia en §4.
- **Una obra enorme** se comería los 45 s del proxy antes de llegar al techo
  de 500.000: no hay ninguna conocida; el error sería un 503 de la página de
  Sigrid, no de la bandeja.
- **Ruido de los criterios** (falsos positivos de R14 y de la descripción
  parecida): avisa y no bloquea; medido en T-A0.
- **Reincidencias de toda la historia**: muchos avisos en obras viejas; la
  página los filtra por fecha y por severidad.
- **`OUTER APPLY`, `conext` sin índice, cuatro `LEFT JOIN` más**: T-A0.
- **Dos peticiones por carga**: medido en T-A15.
- **Lo que hay en Sigrid cambia mientras se revisa**: «Volver a mirar
  Sigrid»; el panel enseña `leido_at_utc`.

## 13 · Lo que no hace

No escribe nada (ni Sigrid, ni la base, ni SharePoint); no bloquea la
aprobación ni cambia el volcado (el ensayo de F-059 no mira los conflictos);
no corrige Sigrid (un duplicado se anula en la UI de Sigrid; desde el portal,
F-062); no casa con IA; no optimiza el listado (F-061); no guarda datos
personales.

## 14 · Decisiones

### 14.1 · Del humano (todas «Aprobada por el humano el 2026-10-21»)

- **Q-1 · Partición.** Dos tramos: **F-065** (este, backend) y **F-064** (la
  página). Orden F-038 → F-065 → F-064 → F-040. *Aprobada por el humano el
  2026-10-21.*
- **Q-2 · Qué se lee.** **Todas** las reclamaciones de la obra, de cualquier
  estado y fecha, con **filtros en pantalla**; el techo de 1.000 no vale (la
  0677 tiene ≈ 1.276). *Aprobada por el humano el 2026-10-21.*
- **Q-3 · Criterios.** Misma unidad + oficio + ubicación; el emparejamiento
  `PVI-` y los avisos de coherencia; y **misma unidad + descripción parecida**.
  *Aprobada por el humano el 2026-10-21.*
- **Q-4 · No bloquea.** Aviso y segundo clic «Aprobar a pesar del conflicto».
  *Aprobada por el humano el 2026-10-21.*
- **Q-5 · Ruta aparte.** *Aprobada por el humano el 2026-10-21.*
- **Q-6 · Datos personales.** **Sí** se enseñan en la página; nunca en logs ni
  trazas, nunca en el repositorio, specs, progress ni tests con valores reales,
  y no se guardan en nuestra base. Riesgo anotado en §12. *Aprobada por el
  humano el 2026-10-21.*
- **Q-7 · Vista**, **Q-8 · tras una acción**, **Q-9 · obras 0677 y 0626**,
  **Q-10 · bandeja contra bandeja fuera**: como se recomendaban. *Aprobadas
  por el humano el 2026-10-21.*

### 14.2 · Las que derivan de ellas

- **N-1 · Volumen.** Una sola lectura **con el techo de la pasarela,
  `MAX_ALLOWED_ROWS` = 500.000**, comprobando `truncated` (si viniera
  recortada, 409 claro y nunca conflictos a medias) y el corte de 230 s; T-A0
  mide el tiempo real y, si pasa de ≈ 10 s, se lee por trozos. *Aprobado por el
  humano el 2026-10-21* (sustituye a la propuesta de un techo propio de
  20.000).
- **N-2 · «Descripción parecida».** Jaccard sobre palabras significativas,
  umbral 50 y al menos 2 palabras en común, ajustable con T-A0. *Aprobado por
  el humano el 2026-10-21.*
- **N-3 · Datos personales.** **Todo en el listado, una sola ruta**; la ficha
  bajo demanda (`GET /api/revision/sigrid/reclamacion`) desaparece. Lista
  cerrada de R33; siguen fuera el DNI, las credenciales de i-Sigrid y lo que no
  sirva al trabajo de Posventa. La ventaja que pesa: buscar y filtrar por
  propietario o teléfono en la página (F-064). *Aprobado por el humano el
  2026-10-21* (sustituye a la propuesta de ficha bajo demanda).
