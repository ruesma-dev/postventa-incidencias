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

## 0 · Dónde está el riesgo

### 0.1 · Lo que se rompe si esto sale mal, y quién lo ve

| Fallo | Qué ve Posventa | Por qué es grave |
|---|---|---|
| El parte va a la carpeta de **otra unidad** de la misma obra | Un parte firmado de la Villa 5 dentro de la Villa 7, en su OneDrive | Lleva DNI manuscrito. Nadie lo busca ahí, y nuestra traza dice «archivado» |
| El parte va a **otra obra** | Igual, en otra promoción | El mismo, peor |
| Creamos una carpeta de obra o unidad **al lado** de la suya | `0677 15 VIVIENDAS...` junto a `0677 MIRASIERRA` | Su archivo partido en dos, y visible en todos sus equipos al momento |
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

### 0.3 · Rigor: se propone `critico`

F-013 está en `estandar`. Se propone **`critico`** (decisión **D-R**): escribe
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
no se compone.

## 2 · Ficheros

### 2.1 A crear

| Ruta | Capa | Qué |
|---|---|---|
| `services/postventa-api/domain/models/destino_posventa.py` | domain (puro) | `EstructuraArchivo`, `MotivoDestino`, `UbicacionReclamacion`, `clave_de_unidad`, `carpetas_de_obra`, `carpetas_de_unidad`, `carpeta_con_nombre`, `unir_ruta` (§4) |
| `services/postventa-api/domain/ports/biblioteca.py` | domain | `ExploradorBibliotecaPort`: `listar_carpetas`, `crear_hoja` (§3.2) |
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
| `services/postventa-api/config/settings.py` | Cuatro campos: `sharepoint_estructura` (`SHAREPOINT_ESTRUCTURA`, `"por_obra"`), `sharepoint_carpeta_incidencias` (`"PARTES INCIDENCIAS"`), `sharepoint_carpeta_firmados` (`"PARTES FIRMADOS"`), `sharepoint_crear_hoja` (`True`). Descripción de `sharepoint_carpeta_base` actualizada: vacía = raíz, solo admitida en `posventa` |
| `services/postventa-api/domain/models/errores.py` | `DestinoNoResuelto(motivo: str, detalle: str, candidatas: tuple[str, ...])` |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | `listar_carpetas` y `crear_hoja` en `AdaptadorSharePointGraph` (§6.1). Lo demás, intacto |
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

    def crear_hoja(self, *, padre: str, nombre: str) -> None:
        """Crea `nombre` dentro de `padre`, que TIENE que existir.
        Ya existente = éxito. Nunca crea intermedias: padre ausente = ArchivoFallido."""
```

El adaptador de Graph implementa `ArchivoPort` **y** este puerto; la fábrica
devuelve la misma instancia y el borde la pasa por los dos lados.

### 3.3 `UbicacionPort`

```python
# domain/models/destino_posventa.py
@dataclass(frozen=True)
class UbicacionReclamacion:
    obra_codigo: str | None
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
no casa → 409 `obra_sin_carpeta`. Es la dirección segura del fallo, y T2 lo
mide antes de encender nada. Si la medición lo desmiente, se amplía la regla
con el separador observado, **con test**, no a ojo.

### 4.2 Los tramos fijos (R14, R16)

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

## 5 · El paso, y el orden

`resolver_destino_posventa(ctx, *, nombre_fichero, explorador, ubicaciones,
base, incidencias, firmados, crear_hoja) -> DestinoResuelto`, en
`application/pipelines/destino_archivo.py`:

1. `leer_ubicacion(codigo_reclamacion=a_codigo_de_sigrid(numero))` — R6, R7.
   El código se convierte con la **misma** función que usa el cierre
   (`a_codigo_de_sigrid`, `domain/models/cierre.py`), nunca con una copia.
2. Obra de la ubicación vs. código de obra del parte, normalizados — R8.
3. `listar_carpetas(base)` → `carpetas_de_obra` — R10, R13.
4. `listar_carpetas(obra)` → `carpeta_con_nombre(INCIDENCIAS)` — R14.
5. `listar_carpetas(obra/INCIDENCIAS)` → `carpetas_de_unidad` — R11, R14.
6. `listar_carpetas(obra/INCIDENCIAS/unidad)` → `carpeta_con_nombre(FIRMADOS)`;
   si no está: `crear_hoja` pendiente (R15) o 409 `sin_carpeta_firmados` (R16).

```python
@dataclass(frozen=True)
class DestinoResuelto:
    destino: DestinoArchivo                 # carpeta completa + nombre (de nombrado.py)
    hoja_por_crear: tuple[str, str] | None  # (padre, nombre) o None
```

Cada fallo levanta `DestinoNoResuelto(motivo, detalle, candidatas)`. **Cuatro
listados y una lectura por parte**, todo lecturas; con 22 partes, ~110 GET.
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
| 6 | Carpeta | `asegurar_carpeta` (crea intermedias) | `crear_hoja` **solo** si hace falta; **nunca** `asegurar_carpeta` (R15) |
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
- `crear_hoja`: `POST {ruta del padre}:/children` con
  `conflictBehavior=fail` y `409` tolerado —lo que ya hace `_crear_carpeta`,
  que se reutiliza—, pero exigiendo `padre` no vacío y **sin recorrer
  tramos**: si el padre no existe, Graph responde `404` y eso es
  `ArchivoFallido`, no una carpeta nueva.
- La puerta de entorno del constructor no cambia: listar también exige
  `dev`/`pro`, porque solo se construye el adaptador allí.

### 6.2 Sigrid, solo lectura

```sql
-- infrastructure/sigrid/consultas_ubicacion.py  (SQL_UBICACION)
SELECT o.cod, u.cod, u.res
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
  de la ficha; §1). Sí el nombre de la carpeta resuelta.

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
   `Invoke-PythonDelServicio` de `08_lectura_sigrid_comun.ps1`) para decir qué
   carpeta resolvería. **No lista ficheros** —sus nombres pueden llevar el de
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

## 9 · Decisiones abiertas para el humano

| Id | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **D-1** | Carpeta base con la estructura de Posventa (H3: «PARTES FIRMADOS (sistema)») | (a) **raíz** de la biblioteca (`SHAREPOINT_CARPETA_BASE=""`); (b) una carpeta delante, p. ej. `PARTES FIRMADOS (sistema)/<cod> <OBRA>/...` | **(a)**. Con (b) las carpetas de obra serían **nuestras**, no las de Posventa, y habría que crearlas: contradice H2 y R15. Si las carpetas de obra de Posventa no están en la raíz (T2 lo dirá), (b) pasa a ser «la ruta donde sí están», no una carpeta nuestra |
| **D-2** | ¿F-033 antes de F-013? | (a) sí, dependencia dura; (b) F-013 la absorbe; (c) F-013 compara `drive_id` | **(a)**, §8.1 |
| **D-3** | ¿F-031 antes de F-013? | (a) sí; (b) no, con riesgo residual escrito | **(a)**; (b) aceptable, §8.2 |
| **D-4** | ¿Quién crea las carpetas? | (a) nosotros **solo la hoja** `PARTES FIRMADOS` dentro de una unidad existente (`SHAREPOINT_CREAR_HOJA=true`); (b) nada: toda carpeta ausente → 409; (c) también la unidad | **(a)**. La hoja es la carpeta «de los partes firmados», que es lo que archivamos; obra y unidad son el esqueleto de Posventa. (c) descartada: una unidad mal casada crearía `VILLA 5` junto a `VILLA 05` |
| **D-5** | Cola humana del «destino no resuelto» | (a) el 409 con motivo, y la persona archiva a mano o pide la carpeta; (b) además, filtro en el front de partes con traza `error` por destino; (c) además, que una persona **elija** la carpeta y se guarde un mapa `unidad → carpeta` en el schema propio | **(a)** en F-013. (b) y (c) son **fichas nuevas** (front; y tabla + endpoint), y (c) solo si T2/T3 muestran que la regla falla a menudo |
| **D-6** | Regla de casado de la unidad (§4.3) | (a) la propuesta: clave canónica, números como enteros, sufijo contiguo con número; (b) igualdad estricta con `upv.cod`; (c) mapa explícito mantenido a mano | **(a)**, **condicionada a T3**: si `upv.cod` resulta ser ya `VILLA 05` o equivalente, (b) es más simple y más segura |
| **D-7** | Si la ubicación de Sigrid falla por red | (a) 503, no se sube; (b) caer a la `unidad` del papel | **(a)**. (b) reintroduce la IA en la decisión de la carpeta |
| **D-R** | Rigor | `estandar` / `critico` | **`critico`** (§0.3) |

Y una que **no** es de F-013 pero hay que saber: la nomenclatura manual de
Posventa (`RS26.08 – 0123 PARTE FIRMADO`, sin obra, con raya) **no coincide**
con la nuestra, así que en una carpeta donde ya subieran el parte a mano
convivirán dos ficheros del mismo parte. No se deduplica por contenido (F-006
R13); se avisa a Posventa en la comunicación del corte.

## 10 · Riesgos y alternativas descartadas

1. **Componer la carpeta desde Sigrid** (`<con.cod> <con.res>`). Descartada:
   medido, `con.res` es «15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)», y
   crearía carpetas paralelas en el archivo de Posventa.
2. **Componer la unidad desde el papel**. Descartada: «Viviendas Bloque Villa
   5» ≠ `VILLA 05`, y es lectura de IA.
3. **Crear lo que falte** (como F-006 R11). Descartada para obra y unidad
   (D-4): el fallo se vería en todos los equipos de Posventa.
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

## 11 · Tests (todos sin red, sin BBDD y sin IA)

| Fichero | Cubre |
|---|---|
| `test_f013_destino_dominio.py` | R9, R10, R11, R13, R14 (casado), R17 (`unir_ruta`), tabla de §4.3 entera, `clave_de_unidad` con tildes/ceros/blancos |
| `test_f013_resolver_destino.py` | R6–R8, R13–R16 con `ExploradorFalso` y `UbicacionesFalsas`; que la obra se valida **antes** de listar; `crear_hoja` solo con la opción |
| `test_f013_paso_archivo_posventa.py` | R4, R5, R15, R18, R20–R22: orden de §5 (registro de llamadas del doble), sin `asegurar_carpeta` en `posventa`, traza `error` con motivo, reintento tras crear la carpeta |
| `test_f013_por_obra_intacto.py` | R2: el paso sin resolutor hace las mismas llamadas que hoy; los tests de F-006 no se tocan (control de alcance por diff, patrón de `test_f032_alcance_cerrado.py`, con su mitad que no depende de git) |
| `test_f013_adaptador_graph_listado.py` | R12 (dos páginas con `nextLink`), filtro de carpetas, `404`→`None`, `crear_hoja` con padre ausente → `ArchivoFallido` y **ningún** `POST` a la raíz |
| `test_f013_ubicacion_sigrid.py` | SQL carácter a carácter, parámetros en orden, mapeo con nulos, solo `sql/read` |
| `test_f013_fabricas.py` | R1, R3, R17 (base vacía en `por_obra`), `construir_ubicaciones` sin `CIERRE_HABILITADO` y con entorno `test` → se niega |
| `test_f013_archivar_http.py` | R19 (409, `error`/`motivo`/`candidatas`, sin IDs), R23 (log sin `unidad_nombre`), R25 desde el endpoint (tras F-033) |
| `test_f013_arquitectura.py` | domain sin `httpx`; `destino_posventa.py` sin E/S; `nombrado.py` y `ArchivoPort` sin cambios |
| `test_f013_scripts_infra.py` | R27, R28, R30: los dos scripts solo `GET` (+ token / `sql/read`), sin IDs ni host del tenant, UTF-8 con BOM y CRLF |
| `test_f013_documentacion.py` | R26, R29: los recuadros fechados existen y citan la premisa literal |

## 12 · Límite de microservicio

Todo cae dentro de `postventa-api` y de su responsabilidad —archivar el parte—:
no hay servicio nuevo ni lógica ajena. Lo que **no** es de aquí y se deja
fuera: el esqueleto de carpetas de Posventa (lo mantiene Posventa, D-4), los
permisos del tenant (humano, F-018), el endpoint o el SQL de `sigrid-api` (se
usa `sql/read` tal y como está desplegado; **no** hace falta tocar la
pasarela) y el documento de `azure-apps/` (otro repositorio, T19). La cola
visual del «destino no resuelto» sería del front (`postventa-front`) y se
propone como ficha aparte (D-5).
