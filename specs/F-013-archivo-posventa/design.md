<!-- specs/F-013-archivo-posventa/design.md -->
# F-013 · Mudar el archivo a la biblioteca de Posventa — Diseño técnico

> Servicio: `services/postventa-api/` (backend). El front **no se toca**: ya
> pinta el campo `error` de un 409 de `/api/archivar` (`js/api.js`), y eso
> basta para que una persona lea el motivo. Encaja en `docs/ARCHITECTURE.md`,
> paso 6 del pipeline (archivo) y fila «SharePoint (Graph)» de sistemas
> externos, y en `docs/CONVENTIONS.md` (hexagonal, pasos con puertos,
> composición en el borde).
>
> **Esta spec no ha escrito en ningún sistema.** Las mediciones que cita son
> lecturas: el datamart (`maestro.obras`, herramienta de solo lectura) y el
> código y los documentos del repositorio. La biblioteca de Posventa **no se
> ha podido listar** desde aquí —la cuenta de la sesión no la alcanza por
> búsqueda y no hay identificador del sitio en el repo, a propósito—, así que
> todo lo que dependa de sus carpetas reales va marcado **[NO MEDIDO]** y
> tiene su verificación manual (T2, T3).
>
> **Enmienda del 2026-09-18 · decisiones cerradas.** El humano respondió a §9
> ese mismo día: *«si, pero quiero que tenga permiso para crear todas las
> carpetas no solo partes firmados.»* Acepta D-1, D-2, D-3, D-5, D-6, D-7 y
> D-R tal y como se recomendaban, y **cambia D-4**: el sistema puede crear
> **toda** la ruta que falte. Lo que eso obliga a resolver —con qué nombre se
> crea, y cuándo se crea y cuándo no— está en §4.5, §4.6 y §5; el riesgo
> nuevo, en §10 (11–14). §9 conserva el texto de las preguntas como se
> hicieron.

## 0 · Dónde está el riesgo

### 0.1 · Lo que se rompe si esto sale mal, y quién lo ve

| Fallo | Qué ve Posventa | Por qué es grave |
|---|---|---|
| El parte va a la carpeta de **otra unidad** de la misma obra | Un parte firmado de la Villa 5 dentro de la Villa 7, en su OneDrive | Lleva DNI manuscrito. Nadie lo busca ahí, y nuestra traza dice «archivado» |
| El parte va a **otra obra** | Igual, en otra promoción | El mismo, peor |
| Creamos una carpeta de obra o unidad **al lado** de la suya | `0677 15 VIVIENDAS...` junto a `0677-MIRASIERRA` | Su archivo partido en dos, y visible en todos sus equipos al momento. Desde D-4 (2026-09-18) el sistema **sí** crea carpetas, así que este es **el** riesgo de la feature: lo contiene la regla de las parecidas (§4.5, R35) |
| Se re-archiva en Posventa un parte ya archivado en IT | Aparece un parte «nuevo» | Y nuestra traza pierde el puntero a IT (F-033) |
| Reemplazamos un fichero que alguien tiene abierto por OneDrive | Conflicto de sincronización / `423 Locked` | Graph lo rechaza; no se reintenta (§10) |

Ninguno produce un error ruidoso en nuestro lado **si el diseño no lo
provoca**. Por eso el diseño elige siempre **no archivar y decir por qué**
antes que archivar en una carpeta dudosa.

### 0.2 · La biblioteca está sincronizada por OneDrive

Lo que suba el entorno desplegado —que se llama `dev` pero es **el único que
hay** y ya escribe en Sigrid de producción— aparece **en los equipos de
Posventa** en segundos. Consecuencias de diseño:

- no hay «prueba» contra la biblioteca real: cada subida es una entrega. La
  primera se hace con un parte autorizado por el humano (R33, paso 5 del corte en `tasks.md`);
- los tests siguen sin red (guardia de la suite) y ningún test construye un
  adaptador capaz de llegar a Graph (F-006 R19–R22, intactos);
- se prefiere el 409 «destino no resuelto» a cualquier heurística generosa.

### 0.3 · Rigor: `critico` (decidido por el humano el 2026-09-18, D-R)

F-013 estaba en `estandar`. Pasa a **`critico`** (D-R, aceptada): escribe
en la biblioteca real del negocio, con datos personales, y el fallo principal
es silencioso. Es exactamente el perfil por el que F-006 y F-031/F-033 son
`critico`. En la práctica cambia el umbral de cobertura y exige campaña de
mutación sin supervivientes sin justificar sobre `destino_posventa.py`,
`destino_archivo.py` y el paso.

## 1 · Lo medido y lo que falta medir

| Pregunta | Respuesta | Fuente |
|---|---|---|
| Nombre de la obra 0677 en Sigrid (`con.res`) | «15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)» | **[MEDIDO]** datamart `maestro.obras`, build 2026-09-17 |
| ¿Es único `con.cod` de obra? | **No**: la `0677` tiene 2 filas; 922 obras, 846 códigos, 134 filas en códigos repetidos | **[MEDIDO]** íd., 2026-09-18 |
| Qué imprime el parte como unidad | «Viviendas Bloque Villa 5» | **[MEDIDO]** `docs/referencia/02_parte_de_trabajo.md` |
| Cómo llama Posventa a la carpeta de esa unidad | `VILLA 05` | Humano, 2026-08-18 (memoria de decisiones); **[NO MEDIDO]** contra la biblioteca |
| Cómo se llama la carpeta de obra (`<cod> <OBRA>`) | Formato declarado por el humano; el literal (`0677 MIRASIERRA`?) **[NO MEDIDO]** | T2 |
| Camino reclamación → unidad → obra | `rcp.upvide → upv`; `upv.obride → obr`; `upv` y `obr` son «Propiedades de `con`» 1:1, así que su código y nombre son `con.cod` / `con.res` | **[MEDIDO en el diccionario]** `azure-apps/sigrid_tablas.md` (bloques `rcp`, `upv`, `obr`) y regla R-SIGRID-CON del datamart |
| Qué valen `con.cod` y `con.res` de la `upv` de la Villa 5 | **[NO MEDIDO]**. Hipótesis: `res` es lo que imprime el parte | T3 |
| ¿Consultamos ya `upv` u obra? | **No**. `infrastructure/sigrid/consultas.py` lee solo `con` y `conest` (F-009), y F-024 D-D decidió no guardar `upv_ide` | **[MEDIDO en código]** |
| ¿Contiene `upv.res` datos personales? | **[NO MEDIDO]**. `upv.cliide` apunta al propietario; `res` es un resumen libre | T3 lo mira y **no se loguea** (R23) |
| ¿Tiene versionado la biblioteca de Posventa? | **[NO MEDIDO]** (por omisión en SharePoint, sí) | T2 |

**Conclusión que manda sobre el diseño**: ni Sigrid ni el papel dan el nombre
de la carpeta; como mucho dan con qué **casarla**. La carpeta se **encuentra**,
no se compone. **Precisado el 2026-09-18 (D-4)**: cuando no hay ninguna que
encontrar —ni parecida—, se crea, y entonces sí se compone, desde Sigrid
(§4.5, §4.6).

## 2 · Ficheros

### 2.1 A crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/postventa-api/domain/models/destino_posventa.py` | domain (puro) | `EstructuraArchivo`, `MotivoDestino`, `UbicacionReclamacion`, `clave_de_unidad`, `carpetas_de_obra`, `carpetas_de_unidad`, `carpeta_con_nombre`, `unir_ruta` (§4) |
| `services/postventa-api/domain/ports/biblioteca.py` | domain | `ExploradorBibliotecaPort`: `listar_carpetas`, `crear_subcarpeta` (§3.2) |
| `services/postventa-api/domain/ports/ubicacion.py` | domain | `UbicacionPort`: `leer_ubicacion` (§3.3) |
| `services/postventa-api/application/pipelines/destino_archivo.py` | application | `resolver_destino_posventa` y `DestinoResuelto` (§5) |
| `services/postventa-api/infrastructure/sigrid/consultas_ubicacion.py` | infrastructure (puro) | SQL de la ubicación y su mapeo (§6.2) |
| `services/postventa-api/infrastructure/sigrid/ubicacion.py` | infrastructure | `AdaptadorUbicacionSigridApi` sobre `POST /api/sql/read` (§6.2) |
| `infra/23_destino_posventa.ps1` | infra | Solo lectura: URL → sitio y biblioteca, permisos del token, y en seco la estructura de una obra (R27, R28; §7.1) |
| `infra/24_ubicacion_sigrid.ps1` | infra | Solo lectura por `sql/read`: unidades de posventa de una obra con `con.cod`/`con.res` y número de reclamaciones (R32; §7.2) |
| `services/postventa-api/tests/test_f013_*.py` | tests | Ver §11 |
| `services/postventa-api/tests/utiles_destino.py` | tests | Dobles: `ExploradorFalso` (árbol de carpetas en memoria que registra cada llamada) y `UbicacionesFalsas` |

### 2.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/config/settings.py` | Cinco campos: `sharepoint_estructura` (`SHAREPOINT_ESTRUCTURA`, `"por_obra"`), `sharepoint_carpeta_incidencias` (`"PARTES INCIDENCIAS"`), `sharepoint_carpeta_firmados` (`"PARTES FIRMADOS"`), `sharepoint_crear_carpetas` (`SHAREPOINT_CREAR_CARPETAS`, `True`, D-4) y `sharepoint_nombre_unidad` (`SHAREPOINT_NOMBRE_UNIDAD`, `codigo`/`nombre`, por omisión el que fije T4; §4.6). Descripción de `sharepoint_carpeta_base` actualizada: vacía = raíz, solo admitida en `posventa` |
| `services/postventa-api/domain/models/errores.py` | `DestinoNoResuelto(motivo: str, detalle: str, candidatas: tuple[str, ...])` |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | `listar_carpetas` y `crear_subcarpeta` en `AdaptadorSharePointGraph` (§6.1). Lo demás, intacto |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | Valida `SHAREPOINT_ESTRUCTURA` y la base según estrategia (R3, R17), antes del token |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | `construir_ubicaciones(ajustes)`: entorno `dev`/`pro` y configuración de lectura de Sigrid; **sin** `CIERRE_HABILITADO` (§6.2) |
| `services/postventa-api/application/pipelines/paso_archivo.py` | Parámetro opcional `resolver_destino`; si llega, sustituye a `componer_destino` + `asegurar_carpeta` en el orden de §5. Sin él, el paso hace **exactamente** lo de hoy (R2) |
| `services/postventa-api/interface_adapters/api/archivar.py` | Compone según `ajustes.sharepoint_estructura`; con `posventa` construye explorador y ubicaciones y pasa el resolutor. Dos costuras de test nuevas (`explorador`, `ubicaciones`) |
| `services/postventa-api/function_app.py` | `DestinoNoResuelto` → **409** `{"error", "motivo", "candidatas"}` (R19) |
| `services/postventa-api/tests/test_f006_repo_sin_identificadores.py` | Añade el barrido del host del tenant (R30); el patrón se construye troceado para no contenerse a sí mismo |
| `infra/00_vars_postventa.ps1` y `infra/desplegar_backend.ps1:430` | La estructura y la base salen de variables (`$EstructuraArchivo`, `$CarpetaBaseArchivo`), con **`por_obra` / `Postventa` hasta el corte** (§7.3) |
| `docs/INTEGRACION.md`, `docs/DESPLIEGUE.md`, `docs/ARCHITECTURE.md`, `specs/F-006-sharepoint/{requirements,design}.md` | Recuadros fechados (R29), §8 de este diseño |
| `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` | **Otro repositorio**. Destino, estructura, lectura nueva de Sigrid y variables. Commit propio allí (T19) |

### 2.3 Lo que NO se toca (y tienta)

- `domain/models/nombrado.py`: el nombre del fichero no cambia (H2, R5), y
  `carpeta_de_archivo` sigue sirviendo a `por_obra`. La base vacía se rechaza
  **en la fábrica**, no aquí: el dominio no sabe de estrategias.
- `domain/ports/archivo.py` (`ArchivoPort`): no gana métodos. Las dos
  operaciones nuevas van en un puerto aparte para no romper `BibliotecaFalsa`
  ni los `isinstance` de F-006 contra un `Protocol` `runtime_checkable`.
- `infrastructure/sigrid/consultas.py` y `cliente.py` (F-009): la consulta del
  cierre sigue sin saber de unidades. `ErpPort` sigue con sus tres métodos.
- `paso_grafico.py`, `paso_cierre.py`, `domain/models/grafico.py`: el gráfico
  se nombra con `nombre_de_archivo`, que no cambia; la precondición «consta
  archivado» se lee de la traza y no depende de la biblioteca.
- `postventa.archivos` y todo el SQL de `persistencia/sql/`: **ni una columna
  nueva**. `carpeta` ya es texto libre y `drive_id` ya distingue IT de
  Posventa. No hay DDL en esta feature.
- `infra/verificar_destino_sharepoint.ps1` (T17 de F-006) y su test: se deja
  como está; el script nuevo es otro fichero (§7.1).
- El front.
- La capa L1 de F-033 y el origen de los códigos de F-031 (§8).

## 3 · Puertos

### 3.1 La estrategia

```python
# domain/models/destino_posventa.py
class EstructuraArchivo(StrEnum):
    POR_OBRA = "por_obra"   # F-006: <base>/<cod obra>
    POSVENTA = "posventa"   # F-013: <base>/<obra>/<INCIDENCIAS>/<unidad>/<FIRMADOS>
```

### 3.2 `ExploradorBibliotecaPort`

```python
# domain/ports/biblioteca.py
@runtime_checkable
class ExploradorBibliotecaPort(Protocol):
    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        """Nombres de las CARPETAS hijas (no ficheros), todas las páginas.
        `carpeta=""` es la raíz. `None` si la carpeta no existe."""

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        """Crea `nombre` dentro de `padre`, que TIENE que existir (`padre=""` es
        la raíz). Ya existente = éxito. Nunca crea intermedias: padre ausente =
        ArchivoFallido. Un nivel por llamada (R15)."""
```

El adaptador de Graph implementa `ArchivoPort` **y** este puerto; la fábrica
devuelve la misma instancia y el borde la pasa por los dos lados.

### 3.3 `UbicacionPort`

```python
# domain/models/destino_posventa.py
@dataclass(frozen=True)
class UbicacionReclamacion:
    obra_codigo: str | None
    obra_nombre: str | None      # con.res de ESA obra (upv.obride), para crear (R36)
    unidad_codigo: str | None
    unidad_nombre: str | None

# domain/ports/ubicacion.py
class UbicacionPort(Protocol):
    def leer_ubicacion(self, *, codigo_reclamacion: str) -> tuple[UbicacionReclamacion, ...]:
        """Todas las filas: el dominio decide qué es 0, 1 o varias (R7)."""
```

Puerto nuevo y no un método en `ErpPort` por lo mismo que F-012 hizo
`GraficoPort`: `ErpPort` documenta «tres métodos y ni uno más», su doble y sus
tests siguen tal cual, y su fábrica exige `CIERRE_HABILITADO`, que **no** debe
hacer falta para archivar (§6.2).

## 4 · El casado (dominio puro)

### 4.1 La carpeta de obra (R10, R13)

```python
def carpetas_de_obra(nombres: Iterable[str], *, codigo_obra: str) -> tuple[str, ...]:
```

Candidata = nombre recortado que **es** el código o **empieza por el código
seguido de un blanco**. El código llega ya pasado por `normalizar_codigo` y se
compara literal: `0677` ≠ `677`, `06770 X` no casa. **No** se mira el nombre
de la obra: medido, el de Sigrid no se parece a una carpeta (§1).

Riesgo declarado: si Posventa escribe `0677-MIRASIERRA` o `0677_MIRASIERRA`,
no casa. Desde D-4 eso **no** lleva a crear `0677 ...` al lado: esas grafías
son **parecidas** (§4.5) y bloquean la creación → 409 `obra_parecida`. T2 lo
mide antes de encender nada; si la medición muestra un separador sistemático,
se amplía la regla **estricta** con ese separador, **con test**, no a ojo.

### 4.2 Los tramos fijos (R14, R16, R34, R35)

```python
def carpeta_con_nombre(nombres: Iterable[str], *, buscado: str) -> tuple[str, ...]:
```

Igualdad por `clave_de_unidad` (mayúsculas, sin tildes, blancos colapsados):
`Partes Incidencias` casa con `PARTES INCIDENCIAS`, y se usa **el nombre tal
y como existe**. Dos que casen (p. ej. `PARTES INCIDENCIAS` y `Partes
incidencias`) → ambigüedad → 409.

### 4.3 La carpeta de unidad (R11, R14) — regla propuesta, **D-6**

```python
def clave_de_unidad(texto: str | None) -> tuple[str, ...]:
    """NFKD sin marcas, mayúsculas, todo lo no alfanumérico es separador,
    tokens; los tokens NUMÉRICOS pasan a str(int(t)): '05' -> '5'."""

def carpetas_de_unidad(nombres: Iterable[str], *, ubicacion: UbicacionReclamacion) -> tuple[str, ...]:
```

Una carpeta `C` casa con la unidad si su clave `K(C)` **no está vacía, lleva
al menos un token numérico** y cumple una de dos:

1. `K(C) == K(unidad_codigo)`, o
2. `K(C)` es un **sufijo contiguo** de `K(unidad_nombre)`.

| Carpeta | Unidad en Sigrid (hipótesis, T3) | ¿Casa? |
|---|---|---|
| `VILLA 05` | nombre «Viviendas Bloque Villa 5» | **Sí** (`VILLA 5` es sufijo) |
| `Villa 5` | íd. | Sí |
| `VILLA 15` | íd. | No (`15` ≠ `5`) |
| `VILLA 05 - GARCÍA` | íd. | **No** → 409; nunca se «acerca» |
| `05` | íd. | Sí, y si además existe `VILLA 05` → **ambigua** → 409 |
| `BLOQUE A` | íd. | No (sin número) |

La exigencia del token numérico evita que `VILLA` a secas case con todas. El
sufijo evita el falso positivo «contiene»: `VILLA 5` no casa con «Villa 51».

**Por qué no se usa la `unidad` extraída del papel**: es lectura de IA con
confianza, y la de Sigrid es el dato del ERP de la reclamación que vamos a
cerrar. Se podría usar como segunda comprobación, pero una discrepancia
sistemática (el papel abrevia) mandaría a la cola partes buenos. Queda
fuera, y anotado en §9 como variante.

### 4.4 La ruta

```python
def unir_ruta(*tramos: str) -> str:
    """Une ignorando tramos vacíos y barras de los extremos: base '' no produce '/0677'."""
```

### 4.5 Parecidas: cuándo se crea y cuándo no (R34, R35) — D-4

La regla que convierte el permiso de crear de D-4 en algo seguro: **por
nivel**, se clasifican las carpetas hijas en tres grupos.

| Grupo | Regla | Qué pasa |
|---|---|---|
| **Casan** | La estricta del nivel (§4.1–§4.3) | 1 → se usa; >1 → 409 `<nivel>_ambigua` |
| **Parecidas** | No casan, pero cumplen la **amplia** del nivel (abajo) | ≥1 y 0 que casan → **409 `<nivel>_parecida`**, no se crea nada |
| Ninguna de las dos | — | 0 casan y 0 parecidas → **se crea** (si `SHAREPOINT_CREAR_CARPETAS`) |

```python
def parecidas_de_obra(nombres, *, codigo_obra) -> tuple[str, ...]
def parecidas_de_unidad(nombres, *, ubicacion) -> tuple[str, ...]
def parecidas_de_tramo(nombres, *, buscado) -> tuple[str, ...]
```

Las reglas amplias, a propósito **generosas** —su error cuesta un 409, el de
la estricta cuesta un duplicado en OneDrive—:

- **Obra**: algún token de `clave_de_unidad(nombre)` es numéricamente igual
  al código (`int`, así que `677` y `00677` también): `0677-MIRASIERRA`,
  `0677_X`, `OBRA 0677`, `677 MIRASIERRA`. Si el código de obra no es numérico
  (hay códigos administrativos), igualdad de token literal.
- **Unidad**: algún token numérico de la carpeta es igual a algún token
  numérico de `K(unidad_codigo)` o `K(unidad_nombre)`: `VILLA 05 - GARCIA`,
  `CHALET 5`, `V-5`, `5`. **No** lo son `VILLA 07` ni `VILLA 15`: un número
  distinto es otra unidad, y es justo lo que se tiene que poder crear.
- **Tramo fijo**: la clave de la carpeta contiene el token distintivo del
  tramo (`INCIDENCIAS` para `PARTES INCIDENCIAS`, `FIRMADOS` para `PARTES
  FIRMADOS`; se toma el **último** token de la clave configurada):
  `PARTES DE INCIDENCIAS`, `INCIDENCIAS 2025`, `FIRMADOS`.

Consecuencia que hay que aceptar sabiéndola: una obra cuyo código aparezca
como número en el nombre de otra carpeta de la raíz (p. ej. una obra `0005` y
una carpeta `LISTADO 5`) bloquea la creación de esa obra. Es un 409 con la
carpeta culpable en `candidatas`, y lo resuelve una persona. Se prefiere así.

### 4.6 Con qué nombre se crea (R36–R38) — condicionado a T2/T3

| Nivel | Nombre | Medido / condición |
|---|---|---|
| Obra | `<cod obra> <con.res de la obra>`, blancos colapsados | Hoy daría `0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)` **[MEDIDO]**. Posventa probablemente usa algo corto (`0677 MIRASIERRA`) **[NO MEDIDO]**, que **no** se puede derivar de Sigrid sin inventar. Si T2 muestra una relación determinista con `con.res` (p. ej. siempre la última palabra antes del paréntesis), se escribe como regla con test en T4; si no, se queda el literal: largo, pero de origen conocido y el mismo para todos |
| `PARTES INCIDENCIAS` | literal de `SHAREPOINT_CARPETA_INCIDENCIAS` | — |
| Unidad | `con.cod` o `con.res` de la `upv`, según `SHAREPOINT_NOMBRE_UNIDAD` | **Se decide en T4**: `codigo` si T3 muestra que `upv.cod` ya es de la forma `VILLA 05`; `nombre` si no (daría «Viviendas Bloque Villa 5», hipótesis). **Si `upv.res` trae nombres de persona (T3), `nombre` queda descartado**: el nombre de carpeta acaba en logs y en OneDrive |
| `PARTES FIRMADOS` | literal de `SHAREPOINT_CARPETA_FIRMADOS` | — |

Tres reglas comunes:

1. **Literal, nunca reformateado**: ni relleno de ceros, ni abreviaturas, ni
   mayúsculas forzadas. Reformatear sería inventar la convención de Posventa a
   partir de un ejemplo.
2. **Imposible = 409, nunca saneo** (R38): mismos caracteres prohibidos que
   `nombrado.CARACTERES_PROHIBIDOS` —se **importan**, no se copian— más blancos
   en los extremos y punto final.
3. **Todos los nombres se componen y comprueban antes de la primera creación**
   (R38): no puede quedar una carpeta de obra vacía porque el nombre de la
   unidad era imposible.

Y la propiedad que lo cierra (R39): **lo que se crea casa consigo mismo**. El
nombre de obra empieza por `<cod> ` (regla estricta §4.1); el de unidad es
`K == K(unidad_codigo)` o `K == K(unidad_nombre)` (sufijo trivial, §4.3); los
tramos fijos son el literal buscado. Un test por nivel lo fija: resolver, crear
en el doble, volver a resolver → casa, 0 creaciones.

## 5 · El paso, y el orden

`resolver_destino_posventa(ctx, *, nombre_fichero, explorador, ubicaciones,
base, incidencias, firmados, crear_carpetas, nombre_unidad) -> DestinoResuelto`,
en `application/pipelines/destino_archivo.py`:

1. `leer_ubicacion(codigo_reclamacion=a_codigo_de_sigrid(numero))` — R6, R7.
   El código se convierte con la **misma** función que usa el cierre
   (`a_codigo_de_sigrid`, `domain/models/cierre.py`), nunca con una copia.
   Fallo de red/configuración → se deja subir (503, R41).
2. Obra de la ubicación vs. código de obra del parte, normalizados — R8.
3. **Componer y comprobar los cuatro nombres de creación** (§4.6) — R36–R38.
   Aún no se ha listado nada.
4. Por cada nivel, en orden (obra, `INCIDENCIAS`, unidad, `FIRMADOS`):
   `listar_carpetas(padre)` → casan / parecidas (§4.5):
   - 1 casa → se baja a ella;
   - >1 casan → 409 `<nivel>_ambigua`;
   - 0 casan y ≥1 parecida → 409 `<nivel>_parecida`;
   - 0 y 0 → si `crear_carpetas`, se **anota** la creación y **todos los
     niveles de debajo se anotan también sin listar** (el padre es nuevo, no
     puede tener nada); si no, 409 `sin_carpeta_<nivel>` (R16).
5. Nada se crea aquí: el resolutor es **puro respecto a escrituras** y devuelve
   la lista de creaciones pendientes. Las ejecuta el paso **después** de la
   traza previa (§5, tabla, paso 6).

```python
@dataclass(frozen=True)
class DestinoResuelto:
    destino: DestinoArchivo                          # carpeta completa + nombre (nombrado.py)
    carpetas_por_crear: tuple[tuple[str, str], ...]  # (padre, nombre), en orden
```

Cada fallo levanta `DestinoNoResuelto(motivo, detalle, candidatas)`. **Hasta
cuatro listados y una lectura por parte**, todo lecturas; con 22 partes, ~110 GET.
Asumible (F-006 hace ~3 por parte) y dentro de los 35 s por llamada. Sin caché
entre partes: cada llamada es un parte y la Function no guarda estado (y una
caché escondería la carpeta que Posventa acaba de crear, que es justo el
reintento de R20).

`paso_archivo` con `resolver_destino`:

| # | Paso | Hoy (`por_obra`) | Con `posventa` |
|---|---|---|---|
| 1 | Puerta de estado `aprobado` | igual | igual |
| 2 | Nombre del fichero | `componer_destino` | `nombre_de_archivo` (el mismo) |
| 3 | L1 (traza `archivado` corta) | **inerte** hoy; F-033 | F-033 |
| 4 | **Resolver destino** | — | §5 arriba. `DestinoNoResuelto` → traza `error` con motivo (R18) y se relanza |
| 5 | Traza previa `pendiente` (F-019) | igual | igual, con la carpeta resuelta |
| 6 | Carpeta | `asegurar_carpeta` (crea intermedias) | `crear_subcarpeta` por cada `carpetas_por_crear`, en orden, un nivel por llamada; aviso y log por carpeta (R40); **nunca** `asegurar_carpeta` (R15). Si una creación falla, `ArchivoFallido` como hoy: traza `error`, y el reintento vuelve a resolver y encuentra lo ya creado (R39) |
| 7–9 | `buscar`, `subir` (replace), traza final | igual | igual |

La traza de error del paso 4 **puede** fallar con `ReferenciaNoConsta` si el
parte no está guardado: se deja subir, y el borde responde el 409 «guarda el
parte primero» que ya existe. Es coherente: sin parte guardado no hay nada que
resolver.

## 6 · Infraestructura

### 6.1 Graph

- `listar_carpetas`: `GET /drives/{drive}/root/children` (raíz) o
  `/root:/{ruta}:/children`, con `$select=name,folder&$top=200`, siguiendo
  `@odata.nextLink` hasta agotarlo (R12). Filtra **en cliente** los elementos
  con `folder` (el `$filter` por `folder` no es fiable en bibliotecas de
  SharePoint). `404` → `None`. Todo con `_con_reintentos`: `404` tolerado,
  transitorios reintentados, el resto → `ArchivoFallido` con el código y nada
  más (R26 de F-006). El `nextLink` lleva el `drive_id`: **no se loguea**.
- `crear_subcarpeta`: `POST {ruta del padre}:/children` (o
  `root/children` si `padre=""`) con `conflictBehavior=fail` y `409`
  tolerado —lo que ya hace `_crear_carpeta`, que se reutiliza— y **sin
  recorrer tramos**: si el padre no existe, Graph responde `404` y eso es
  `ArchivoFallido`, no una carpeta nueva. El `409` de una carrera entre dos
  partes (R39) deja **una** carpeta porque el nombre es determinista.
- La puerta de entorno del constructor no cambia: listar también exige
  `dev`/`pro`, porque solo se construye el adaptador allí.

### 6.2 Sigrid, solo lectura

```sql
-- infrastructure/sigrid/consultas_ubicacion.py  (SQL_UBICACION)
SELECT o.cod, o.res, u.cod, u.res
FROM dbo.con c
JOIN dbo.rcp r      ON r.ide = c.ide
LEFT JOIN dbo.upv v ON v.ide = r.upvide
LEFT JOIN dbo.con u ON u.ide = v.ide
LEFT JOIN dbo.con o ON o.ide = v.obride
WHERE c.tip = ? AND c.cod = ?
```

- Parámetros `(SIGRID_TIP_RECLAMACION, código con barra)`, nunca
  interpolados (`azure-apps/sigrid_api.md` §5.2). `LEFT` en la unidad y la obra
  para distinguir «no existe» (0 filas) de «existe sin unidad» (fila con nulos
  → `reclamacion_sin_unidad`).
- Adaptador `AdaptadorUbicacionSigridApi`: **reutiliza** de `cliente.py`
  `construir_cliente_http`, `ErrorDeSigrid`, `es_transitorio` y la cabecera
  `x-functions-key`; **solo** `POST /api/sql/read`. Un test comprueba que el
  módulo no nombra `sql/write` ni `concepto-grafico`.
- `construir_ubicaciones(ajustes)`: entorno `dev`/`pro` (la lista del cierre,
  importada, no copiada) y configuración de Sigrid completa; **no** exige
  `CIERRE_HABILITADO`. Consecuencia buscada: con la ventana del ERP cerrada se
  puede archivar en Posventa. Consecuencia a documentar: con `posventa`,
  **archivar pasa a depender de `sigrid-api`**; si la pasarela cae, `503`
  (`ConfiguracionSigridIncompleta`/transitorio) y no se sube nada.
- `unidad_nombre` **no se registra** en ningún log (puede llevar texto libre
  de la ficha; §1). Sí el nombre de la carpeta resuelta o creada —por eso, si
  T3 muestra nombres de persona en `upv.res`, `SHAREPOINT_NOMBRE_UNIDAD` no
  puede valer `nombre` (§4.6)—.

## 7 · Infra, despliegue y el corte

### 7.1 `infra/23_destino_posventa.ps1` (solo lectura)

Parámetros: `-UrlSitio` (obligatorio), `-NombreBiblioteca` (por omisión
«Documentos compartidos»), `-CodigoObra` (opcional), `-MostrarIdentificadores`
(switch), `-WhatIf`. Credenciales `GRAPH_*` de la sesión, como el script de
F-006. Hace:

1. Token app-only; roles del token (avisa de los amplios: F-018).
2. `GET /sites/{host}:{ruta}` → sitio; `GET /sites/{id}/drives` → la
   biblioteca cuyo `webUrl` termina en la ruta de «Documentos compartidos»
   (el nombre interno puede ser «Documentos» o «Shared Documents»; se casa por
   URL, no por nombre visible). Dice si la encuentra; los IDs solo con
   `-MostrarIdentificadores`, con el aviso de que van a Key Vault con
   `cargar_secretos_postventa.ps1 -Solo` y a ningún fichero.
3. Con `-CodigoObra`: lista **solo carpetas** raíz → obra → `PARTES
   INCIDENCIAS` → cada unidad → si tiene `PARTES FIRMADOS`, y aplica **la
   misma regla** de §4 (el script ejecuta `domain/models/destino_posventa.py`
   con el intérprete del servicio **por fichero, nunca con `-c`**, con
   `Invoke-PythonDelServicio` de `08_lectura_sigrid_comun.ps1`) para decir, por
   cada unidad que le pase el humano (salida de `24_ubicacion_sigrid.ps1`), si
   la **resolvería**, la **crearía** —y con qué nombre— o la **bloquearía**
   (parecida o ambigua). **No crea nada.** **No lista ficheros** —sus nombres pueden llevar el de
   un cliente— y cuenta cuántos hay en cada hoja sin nombrarlos.

Ni `POST` (salvo el token), ni `PUT`, ni `PATCH`, ni `DELETE`: lo comprueba un
test estático (T1 y T14).

### 7.2 `infra/24_ubicacion_sigrid.ps1` (solo lectura)

Con `08_lectura_sigrid_comun.ps1`: `-CodigoObra` → para las reclamaciones de
esa obra, `GROUP BY` unidad: `u.cod`, `u.res`, número de reclamaciones. Aviso
en cabecera: `u.res` puede traer texto libre; el resultado se anota en
`progress/` **sin nombres de persona**.

### 7.3 El corte (runbook en `docs/DESPLIEGUE.md`)

Orden, y cada paso lo da el humano:

1. **F-033 desplegada** (D-2). Sin ella no se enciende nada.
2. `23_destino_posventa.ps1 -UrlSitio ... -CodigoObra 0677` y
   `24_ubicacion_sigrid.ps1 -CodigoObra 0677` en verde (T2, T3).
3. Consulta de solo lectura de lo archivado en IT (R26) y anotación del
   recuento, sin identificadores.
4. Cargar en Key Vault los IDs de Posventa en `sharepoint-site-id` y
   `sharepoint-drive-id` (`cargar_secretos_postventa.ps1 -Solo`). Los de IT
   **no se guardan en el repo**; si se quieren conservar, en el propio Key
   Vault con otro nombre (decisión del humano).
5. `00_vars_postventa.ps1`: `$EstructuraArchivo = "posventa"`,
   `$CarpetaBaseArchivo = ""` (o lo que diga D-1). Desplegar.
6. Ventana `ARCHIVO_HABILITADO` abierta **solo** para el parte autorizado
   (R33), comprobación con Posventa en su OneDrive, y cierre de ventana.

Vuelta atrás: los pasos 4 y 5 al revés. No hay datos que deshacer: la traza de
cada parte dice en qué biblioteca está (`drive_id`).

## 8 · Relación con F-033, F-031 y F-018

### 8.1 F-033 (L1 inerte) — **D-2**

Hoy `/api/archivar` sube siempre; lo que evitaba el duplicado era reemplazar
el homónimo **en la misma carpeta**. Con F-013 la carpeta cambia de biblioteca
entera, así que re-archivar un parte ya archivado en IT: (a) lo sube a
Posventa, contra H4; y (b) `upsert` de `postventa.archivos` por `hash_parte`
**pisa** `drive_id`, `carpeta` y `web_url`, y el puntero a IT se pierde, contra
R26. Y re-archivar no es raro: el circuito de F-025 re-archiva al reintentar.

**Recomendación: F-033 se implementa y despliega antes que F-013**
(dependencia dura para el corte, §7.3 paso 1). F-013 no la absorbe: F-033 toca
`SituacionParte`, `RepositorioPartesPort` y su sentencia, que son de otro
terreno, y tiene su propia ficha `critico`. Lo único que F-013 añade es el
test R25 desde el endpoint, que presupone F-033 mergeada. Alternativa
descartada: que F-013 compare el `drive_id` de la traza con el configurado —es
leer la traza, o sea hacer F-033 por la puerta de atrás—.

### 8.2 F-031 (nombrado desde el cuerpo) — **D-3**

F-013 usa `codigo_obra` y `numero_incidencia` **tal y como llegan al paso**
(`ctx.extraccion`), igual que hoy. No cambia su origen: eso es F-031, que
además toca el front. Lo que F-013 **sí** añade es R8: la obra que dice Sigrid
para ese número tiene que ser la del parte. Así un cuerpo que mezcle el número
de una obra con el código de otra ya no archiva; lo que **no** cubre es un
cuerpo que mienta en los dos de forma coherente (obra A + incidencia de A para
un parte de B). Eso solo lo cierra F-031.

**Recomendación**: orden **F-033 → F-031 → F-013**. Si el humano prefiere
F-013 antes que F-031, el riesgo residual es **el de hoy, estrictamente
menor** gracias a R8, y queda escrito así en los riesgos. El diseño de F-013
no se toca en ninguno de los dos órdenes: el resolutor recibe los códigos del
contexto, y F-031 decide de dónde salen.

### 8.3 F-018 (mínimo privilegio)

Hoy la app tiene `Sites.ReadWrite.All` y `Sites.FullControl.All`, así que
**escribirá en el sitio de Posventa sin que nadie le conceda nada**. Al
recortar a `Sites.Selected`, habrá que conceder **el sitio de Posventa**
(`write`) —y, si se conserva la lectura de lo de IT, el de IT (`read`)—.
Se anota en la ficha de F-018 (T18); no se hace aquí.

## 9 · Decisiones del humano (cerradas el 2026-09-18)

Las preguntas se hicieron con la tabla de abajo, y el humano respondió el
mismo día, literal: *«si, pero quiero que tenga permiso para crear todas las
carpetas no solo partes firmados.»* La columna «Decidido» es lo que manda; las
opciones y la recomendación se conservan para que se entienda por qué.

| Id | Pregunta | Opciones | Recomendación | **Decidido (humano, 2026-09-18)** |
|---|---|---|---|---|
| **D-1** | Carpeta base con la estructura de Posventa (H3: «PARTES FIRMADOS (sistema)») | (a) **raíz** de la biblioteca (`SHAREPOINT_CARPETA_BASE=""`); (b) una carpeta delante | (a). Con (b) las carpetas de obra serían nuestras, contra H2 | **(a) raíz** |
| **D-2** | ¿F-033 antes de F-013? | (a) sí, dependencia dura; (b) F-013 la absorbe; (c) F-013 compara `drive_id` | (a), §8.1 | **(a)** |
| **D-3** | ¿F-031 antes de F-013? | (a) sí; (b) no, con riesgo residual escrito | (a) | **(a)**: orden F-033 → F-031 → F-013 |
| **D-4** | ¿Quién crea las carpetas? | (a) solo la hoja `PARTES FIRMADOS`; (b) nada; (c) también la unidad | (a) | **Otra: el sistema puede crear toda la ruta que falte** —obra, `PARTES INCIDENCIAS`, unidad y `PARTES FIRMADOS`—. Traducción: §4.5 (solo si no hay ninguna **ni parecida**), §4.6 (nombres), `SHAREPOINT_CREAR_CARPETAS` encendido |
| **D-5** | Cola humana del «destino no resuelto» | (a) el 409 con motivo; (b) filtro en el front; (c) mapa `unidad → carpeta` | (a); (b) y (c) fichas nuevas | **(a)** |
| **D-6** | Regla de casado de la unidad (§4.3) | (a) la propuesta; (b) igualdad con `upv.cod`; (c) mapa a mano | (a), condicionada a T3 | **(a), condicionada a T3** |
| **D-7** | Si la ubicación de Sigrid falla por red | (a) 503; (b) caer a la `unidad` del papel | (a) | **(a)** |
| **D-R** | Rigor | `estandar` / `critico` | `critico` | **`critico`** |

Lo que D-4 deja **pendiente de medir**, sin reabrirla: el nombre corto de la
obra (§4.6, T2) y el campo de la unidad (`SHAREPOINT_NOMBRE_UNIDAD`, T3). Se
fijan en la parada T4 con los datos delante.

Y una que **no** es de F-013 pero hay que saber: la nomenclatura manual de
Posventa (`RS26.08 – 0123 PARTE FIRMADO`, sin obra, con raya) **no coincide**
con la nuestra, así que en una carpeta donde ya subieran el parte a mano
convivirán dos ficheros del mismo parte. No se deduplica por contenido (F-006
R13); se avisa a Posventa en la comunicación del corte.

## 10 · Riesgos y alternativas descartadas

1. **Componer la carpeta desde Sigrid** (`<con.cod> <con.res>`) **en vez de
   buscarla**. Descartada: medido, `con.res` es «15 VIVIENDAS UNIFAMILIARES EN
   MIRASIERRA(MADRID)», y crearía carpetas paralelas en el archivo de Posventa.
   Desde D-4 se compone así **solo** para crear cuando no hay ninguna ni
   parecida (§4.6).
2. **Componer la unidad desde el papel**. Descartada: «Viviendas Bloque Villa
   5» ≠ `VILLA 05`, y es lectura de IA.
3. **Crear lo que falte** (como F-006 R11), **sin mirar parecidas**.
   Descartada. D-4 permite crear toda la ruta, pero crear a ciegas —el
   `asegurar_carpeta` de F-006— pondría `0677 15 VIVIENDAS...` junto a
   `0677-MIRASIERRA`. Se crea solo con 0 que casan y 0 parecidas (§4.5).
4. **Casado «contiene» o por similitud**. Descartado: `VILLA 5` dentro de
   `VILLA 51`. Una similitud difusa es la forma de que el DNI acabe en la
   vivienda de al lado sin que nadie se entere.
5. **Buscar por `$search`/índice de SharePoint** en vez de listar. Descartado:
   el índice va con retraso (una carpeta recién creada no aparece) y devuelve
   por relevancia, no por nombre exacto.
6. **Listar la raíz entera en cada parte**: se asume el coste (paginado, ~N/200
   llamadas). Si T2 mide miles de carpetas de obra, se propone filtrar con
   `$filter=startswith(name,'<cod>')` **medido** antes de usarlo.
7. **`423 Locked`** (fichero abierto por un usuario de OneDrive al
   reemplazar): no está en `CODIGOS_TRANSITORIOS` y no se añade: es
   `ArchivoFallido` con su código, y el reintento lo decide una persona. Se
   documenta en INTEGRACION.
8. **Renombrado de carpetas por Posventa** después de archivar: la traza
   guarda `web_url` e `item_id`, que siguen al fichero; `carpeta` queda con el
   nombre viejo. Se documenta; no se persigue.
9. **Archivar depende de `sigrid-api`** con `posventa` (§6.2). Aceptado: es
   una lectura por parte, y el circuito ya depende de la pasarela para
   adjuntar y cerrar justo después.
10. **Dos `upv` o dos obras con el mismo código**: la obra se valida contra el
   código del parte (R8), no contra su `ide`, así que dos obras `0677` en el
   maestro no molestan mientras la carpeta sea una. Si hubiera dos carpetas
   `0677 ...`, 409 ambigua (R13).
11. **Duplicado por otra grafía** (D-4). El riesgo principal desde el
   2026-09-18. Contención: la regla de parecidas (§4.5), generosa a propósito;
   tests obligatorios de R35. Residual: una grafía que ni siquiera comparta el
   número (`VILLA CINCO`) no se detecta y se crearía `VILLA 5` al lado. T2 mide
   si hay casos así en la obra piloto antes de encender.
12. **El nombre creado no le sirve a Posventa** (`0677 15 VIVIENDAS
   UNIFAMILIARES EN MIRASIERRA(MADRID)` frente a su `0677 MIRASIERRA`). Es
   **correcto pero feo**, y visible en todos sus equipos. Contención: T4 fija el
   nombre con T2 delante; R42 hace la primera creación con Posventa avisada.
13. **Carpetas creadas y vacías** si la subida falla después de crearlas.
   Aceptado: el reintento las encuentra y sube (R39). No se borran.
14. **Deshacer una carpeta creada por error** lo hace **una persona**; el
   sistema no borra, no mueve y no renombra nunca (R43). Procedimiento en
   `docs/INTEGRACION.md`: localizar los partes de esa carpeta con la consulta
   de solo lectura sobre `postventa.archivos`, moverlos a la buena dentro de la
   misma biblioteca (el `item_id` se conserva; la columna `carpeta` de la traza
   queda con el nombre viejo, riesgo 8), y borrar o renombrar la sobrante. El
   borrado va a la papelera del sitio y se propaga a los OneDrive. Si la carpeta
   buena **no** existía y el nombre creado solo es feo, lo sencillo es
   **renombrarla** a mano: la siguiente resolución la encontrará si sigue
   empezando por el código (obra) o casando con la unidad (§4.1, §4.3); si no,
   dará 409 `parecida`, que es el aviso correcto.

## 11 · Tests (todos sin red, sin BBDD y sin IA)

| Fichero | Cubre |
|---|---|
| `test_f013_destino_dominio.py` | R9, R10, R11, R13, R14 (casado), R17 (`unir_ruta`), tabla de §4.3 entera, `clave_de_unidad` con tildes/ceros/blancos; **§4.5 entera** (casan / parecidas / ninguna por nivel, con los cuatro casos obligatorios de R35); **§4.6** (nombres de R36–R38, literal sin reformatear, imposibles) |
| `test_f013_resolver_destino.py` | R6–R8, R13–R16, R34–R39, R41 con `ExploradorFalso` y `UbicacionesFalsas`: la obra se valida **antes** de listar; los nombres se comprueban antes de anotar ninguna creación; con un nivel nuevo, los de debajo se anotan **sin listar**; `crear_carpetas` apagado → `sin_carpeta_<nivel>`; lo creado casa en la segunda resolución (R39) |
| `test_f013_paso_archivo_posventa.py` | R4, R5, R15, R18, R20–R22, R40 (aviso por carpeta creada), creación **después** de la traza previa y en orden: orden de §5 (registro de llamadas del doble), sin `asegurar_carpeta` en `posventa`, traza `error` con motivo, reintento tras crear la carpeta |
| `test_f013_por_obra_intacto.py` | R2: el paso sin resolutor hace las mismas llamadas que hoy; los tests de F-006 no se tocan (control de alcance por diff, patrón de `test_f032_alcance_cerrado.py`, con su mitad que no depende de git) |
| `test_f013_adaptador_graph_listado.py` | R12 (dos páginas con `nextLink`), filtro de carpetas, `404`→`None`, `crear_subcarpeta` con padre ausente → `ArchivoFallido` sin crear intermedias; `409` → éxito |
| `test_f013_ubicacion_sigrid.py` | SQL carácter a carácter (con `o.res`), parámetros en orden, mapeo con nulos, solo `sql/read` |
| `test_f013_fabricas.py` | R1, R3, R17 (base vacía en `por_obra`), `construir_ubicaciones` sin `CIERRE_HABILITADO` y con entorno `test` → se niega |
| `test_f013_archivar_http.py` | R19 (409, `error`/`motivo`/`candidatas`, sin IDs), R23 (log sin `unidad_nombre`), R25 desde el endpoint (tras F-033) |
| `test_f013_arquitectura.py` | domain sin `httpx`; `destino_posventa.py` sin E/S; `nombrado.py` y `ArchivoPort` sin cambios |
| `test_f013_scripts_infra.py` | R27, R28, R30: los dos scripts solo `GET` (+ token / `sql/read`), sin IDs ni host del tenant, UTF-8 con BOM y CRLF |
| `test_f013_documentacion.py` | R26, R29: los recuadros fechados existen y citan la premisa literal |

## 12 · Límite de microservicio

Todo cae dentro de `postventa-api` y de su responsabilidad —archivar el parte—:
no hay servicio nuevo ni lógica ajena. Lo que **no** es de aquí y se deja
fuera: renombrar, mover o borrar carpetas de Posventa (lo hace una persona;
el sistema solo **crea** cuando no hay ninguna ni parecida, D-4), los
permisos del tenant (humano, F-018), el endpoint o el SQL de `sigrid-api` (se
usa `sql/read` tal y como está desplegado; **no** hace falta tocar la
pasarela) y el documento de `azure-apps/` (otro repositorio, T19). La cola
visual del «destino no resuelto» sería del front (`postventa-front`) y se
propone como ficha aparte (D-5).
