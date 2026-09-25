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
>
> **Enmienda del 2026-09-24 · la medición (T2/T3) y la parada T4.** La
> medición (`progress/explore_F-013.md`) desmintió §4.1: la carpeta de la 0677
> es `677  MIRASIERRA`, y con la regla literal no casaba. El humano decidió en
> T4 (§9 ter): casar la obra **por número**, crear la unidad como `VILLA NN`
> derivado del `con.cod`, crear `PARTES FIRMADOS` en una unidad sin
> subcarpetas, admitir `PARTES FIRMADO` como hoja, crear las villas 8–15 y
> **arrancar creando desde el primer despliegue**, con las ventanas abiertas.
> Además se ponen al día los desfases que dejaron F-031, F-033 y F-034, ya
> desplegadas (`progress/impl_F-013.md` §8). Cambian §1, §2, §3.3, §4 entera,
> §5, §6.2, §7, §8, §10 y §11; cada cambio de fondo lleva recuadro con esta
> fecha y cita lo que decía.

> **Enmienda del 2026-09-25 (F-049) · las villas que se crean, con tres
> cifras.** En el paso 2 del corte, el script 23 mostró que Posventa ha
> reorganizado las carpetas de unidad de la 0677 a `VILLA 001` … `VILLA 007`,
> `VILLA 012` y `VILLA 013`, y el humano decidió ese día «siempre con tres
> cifras» (`VILLA 008`; con 1.000 o más, tal cual). Llevan recuadro de esta
> fecha §1 (la medición), §4.5, §4.6 (la regla y su código) y §7.3 (el
> runbook). Donde este documento dice `VILLA NN` sin más —§7.1, §9 ter,
> §10—, léase «`VILLA` y el número con al menos tres cifras». **El casado no
> cambia** (§4.3, §4.5): compara enteros. Spec: `specs/F-049-villa-tres-cifras/`.

## 0 · Dónde está el riesgo

### 0.1 · Lo que se rompe si esto sale mal, y quién lo ve

| Fallo | Qué ve Posventa | Por qué es grave |
|---|---|---|
| El parte va a la carpeta de **otra unidad** de la misma obra | Un parte firmado de la Villa 5 dentro de la Villa 7, en su OneDrive | Lleva DNI manuscrito. Nadie lo busca ahí, y nuestra traza dice «archivado» |
| El parte va a **otra obra** | Igual, en otra promoción | El mismo, peor |
| Creamos una carpeta de obra o unidad **al lado** de la suya | `0677 15 VIVIENDAS...` junto a `0677-MIRASIERRA` | Su archivo partido en dos, y visible en todos sus equipos al momento. Desde D-4 (2026-09-18) el sistema **sí** crea carpetas, así que este es **el** riesgo de la feature: lo contiene la regla de las parecidas (§4.5, R35) |
| Se re-archiva en Posventa un parte ya archivado en IT | Aparece un parte «nuevo» | Y nuestra traza pierde el puntero a IT (F-033). **Desde el 2026-09-22 (§9 bis) esto ya no puede pasar y así se quiere**: F-033 corta, y las 133 trazas de IT no se tocan |
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
  **enmendado el 2026-09-24 (T4-3)**: con las ventanas abiertas por defecto y
  «crear desde el principio», la primera la hace quien archive primero; lo
  que se conserva es la comprobación con Posventa ese mismo día (R33, R42,
  §7.3);
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

> **Medido el 2026-09-24 (T2 y T3; `progress/explore_F-013.md`).** Filas que
> sustituyen a las **[NO MEDIDO]** de arriba, que se dejan como estaban:
>
> | Pregunta | Respuesta medida |
> |---|---|
> | Biblioteca | Una sola en el sitio, «Documentos» (`…/Documentos compartidos`), la de por defecto. Token con `Mail.ReadWrite` y `Sites.ReadWrite.All` |
> | Raíz (D-1) | 52 carpetas y 7 ficheros sueltos |
> | Carpeta de obra de la 0677 | **`677  MIRASIERRA`**: sin el cero y con **dos** blancos; el nombre corto **no** es el `con.res`. Ninguna otra carpeta de la raíz casa ni se parece |
> | `PARTES INCIDENCIAS` | Existe dentro y casa. Hay otras tres subcarpetas de trabajo interno y 2 ficheros sueltos |
> | Unidades en Posventa | 7: `VILLA 01` … `VILLA 07`, **siempre dos cifras** |
> | Hoja | `PARTES FIRMADOS` en 01, 03, 05, 06 y 07; en **VILLA 02**, `PARTES FIRMADO` (literal dado por el humano el 2026-09-24); **VILLA 04** sin subcarpetas y 142 ficheros sueltos |
> | Obras con código 0677/677 y unidades de posventa en Sigrid | **1**, código guardado `0677` |
> | Unidades de posventa de la 0677 | **15**: `con.cod` `0677.03VILLA N.` y `con.res` `Viviendas Bloque Villa N`, N = 1 … 15 sin cero; 1.197 reclamaciones; sin reclamaciones las 8, 9, 10, 11, 14 y 15; la 12 tiene 9 y la 13, 213 |
> | ¿Nombres de persona en `con.res` de las unidades? | **Ninguno** |
> | Versionado | No concluyente (el fichero mirado tiene 1 versión) |
>
> Y las villas 8 a 15 **no tienen carpeta en ningún otro sitio** de la
> biblioteca (humano, 2026-09-24: «no tienen carpeta, que se creen»).

> **Enmienda del 2026-09-25 (F-049) · Posventa reorganizó sus unidades.** La
> fila «Unidades en Posventa» decía, literal: *«7: `VILLA 01` … `VILLA 07`,
> **siempre dos cifras**»*. **Qué la invalidó**: en el paso 2 del corte
> (2026-09-25), el script 23 contra la biblioteca real listó **`VILLA 001` …
> `VILLA 007`, `VILLA 012` y `VILLA 013`**: tres cifras, y dos villas más de
> las que había el 2026-09-24. Las hojas de esas carpetas **no se han
> medido** [NO MEDIDO]. El humano decidió ese día que lo que cree el sistema
> vaya también con tres cifras (§4.6). La fila de arriba se deja como estaba:
> es la foto del 2026-09-24, y los tests de F-013 la conservan como dato
> medido.

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
| `infra/23_destino_posventa.ps1` | infra | Solo lectura: URL → sitio y biblioteca, permisos del token, y en seco la estructura de una obra (R27, R28; §7.1). **Creado en T1**; T14 lo modifica |
| `infra/24_ubicacion_sigrid.ps1` | infra | Solo lectura por `sql/read`: unidades de posventa de una obra con `con.cod`/`con.res` y número de reclamaciones (R32; §7.2). **Creado en T1**; T14 le añade la salida para el 23 |
| `services/postventa-api/tests/test_f013_*.py` | tests | Ver §11 |
| `services/postventa-api/tests/utiles_destino.py` | tests | Dobles: `ExploradorFalso` (árbol de carpetas en memoria que registra cada llamada) y `UbicacionesFalsas` (con las dos lecturas de §3.3) |

> **Precisión del 2026-09-24.** `infra/23_destino_posventa.ps1` e
> `infra/24_ubicacion_sigrid.ps1` **ya existen** (T1, commit `553ce39`); en
> este feature se **modifican** en T14 (§7.1). Y `domain/models/destino_posventa.py`
> gana, respecto a la lista de arriba, `numero_de_obra`,
> `nombre_derivado_de_unidad`, `obras_del_mismo_numero` y
> `unidades_que_casan` (§4.1, §4.6, §4.7).

### 2.2 A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/config/settings.py` | Cinco campos: `sharepoint_estructura` (`SHAREPOINT_ESTRUCTURA`, `"por_obra"`), `sharepoint_carpeta_incidencias` (`"PARTES INCIDENCIAS"`), `sharepoint_carpeta_firmados` (`"PARTES FIRMADOS"`), `sharepoint_carpeta_firmados_alternativa` (`SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA`, `"PARTES FIRMADO"`, vacía = ninguna; R49) y `sharepoint_crear_carpetas` (`SHAREPOINT_CREAR_CARPETAS`, `True`, D-4). Descripción de `sharepoint_carpeta_base` actualizada: vacía = raíz, solo admitida en `posventa`. **Enmendado el 2026-09-24**: decía `sharepoint_nombre_unidad` (`SHAREPOINT_NOMBRE_UNIDAD`, `codigo`/`nombre`, por omisión el que fije T4) en lugar de la alternativa; se retira por T4-1 (R1, R37) |
| `services/postventa-api/domain/models/errores.py` | `DestinoNoResuelto(motivo: str, detalle: str, candidatas: tuple[str, ...])` |
| `services/postventa-api/infrastructure/sharepoint/graph.py` | `listar_carpetas` y `crear_subcarpeta` en `AdaptadorSharePointGraph` (§6.1). Lo demás, intacto |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | Valida `SHAREPOINT_ESTRUCTURA` y la base según estrategia (R3, R17), antes del token |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | `construir_ubicaciones(ajustes)`: entorno `dev`/`pro` y configuración de lectura de Sigrid; **sin** `CIERRE_HABILITADO` (§6.2) |
| `services/postventa-api/application/pipelines/paso_archivo.py` | Parámetro opcional `resolver_destino`; si llega, sustituye a `componer_destino` + `asegurar_carpeta` en el orden de §5. Sin él, el paso hace **exactamente** lo de hoy (R2). **Precisado el 2026-09-24**: el resolutor entra entre L1 y el aviso del intento anterior, y recibe los códigos de `codigos_guardados(ctx)` —que el paso ya calcula— como **dos cadenas**, nunca el contexto (§5) |
| `services/postventa-api/interface_adapters/api/archivar.py` | Compone según `ajustes.sharepoint_estructura`; con `posventa` construye explorador y ubicaciones y pasa el resolutor ya configurado (`functools.partial` de `resolver_destino_posventa` con explorador, ubicaciones, base, tramos, alternativa y `crear_carpetas`). Dos costuras de test nuevas (`explorador`, `ubicaciones`). `CAMPOS_OBLIGATORIOS` **no cambia** (lo fija `test_f033_alcance_cerrado.py`) |
| `services/postventa-api/function_app.py` | `DestinoNoResuelto` → **409** `{"error", "motivo", "candidatas"}` (R19) |
| `services/postventa-api/tests/test_f006_repo_sin_identificadores.py` | Añade el barrido del host del tenant (R30); el patrón se construye troceado para no contenerse a sí mismo |
| `infra/00_vars_postventa.ps1` y `infra/desplegar_backend.ps1:430` | La estructura y la base salen de variables (`$EstructuraArchivo`, `$CarpetaBaseArchivo`), con **`por_obra` / `Postventa` hasta el corte** (§7.3). **Enmendado el 2026-09-24**: la línea citada ya no es la 430; `"SHAREPOINT_CARPETA_BASE=Postventa",` está hoy en la **497** (se cita por contenido, que no se mueve). Entra una tercera variable, `$CrearCarpetasArchivo` (`"true"`, T4-3), que el despliegue escribe como `SHAREPOINT_CREAR_CARPETAS` y que es el freno de la creación sin tocar la estructura (§7.3). `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` no se escribe: vale su defecto del código |
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

> **Añadido el 2026-09-24 · lo que F-031, F-033 y F-034 dejaron fijado, y
> que F-013 tiene que respetar sin tocar sus tests.** Tres controles de
> alcance se comprueban **siempre**, en cualquier rama, y lo vigilan:
>
> - `application/pipelines/codigos_del_parte.py` y
>   `application/pipelines/puerta_de_estado.py` **no se tocan** (la puerta de
>   archivo del gráfico y del cierre sigue sin mirar la biblioteca: H-3 de
>   F-034, `requirements.md` R26).
> - `paso_archivo.py` **no lee `ctx.extraccion`** ni vuelve a tener `_campo`
>   (`test_f031_alcance_cerrado.py::test_f031_r29_el_paso_de_archivo_ya_no_lee_la_extraccion`).
> - Los nombres de las tablas `NOMBRES_NUEVOS_Y_DONDE_VIVEN` de
>   `test_f031_alcance_cerrado.py`, `test_f033_alcance_cerrado.py` y
>   `test_f034_alcance_cerrado.py` solo aparecen donde dicen. En concreto,
>   **ni `destino_archivo.py` ni `destino_posventa.py`** pueden nombrar
>   `codigos_guardados`, `CodigosDelParte`, `codigos_declarados`,
>   `exigir_codigos_declarados`, `es_el_mismo_codigo`, `drive_id_vigente` ni
>   `_en_otro_destino`. Por eso el resolutor recibe dos cadenas (§5) y R8
>   compara con `normalizar_codigo` (que no está en esas tablas), no con
>   `es_el_mismo_codigo`. Si un día hiciera falta, se amplía la tabla **en una
>   tarea con nombre**, nunca de paso.
> - `ArchivoPort` no gana métodos
>   (`test_f032_alcance_cerrado.py::test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado`):
>   por eso el explorador es un puerto aparte (§3.2).
> - Los controles del **diff** de F-031, F-033 y F-034 (p. ej.
>   `test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza`) se **saltan**
>   fuera de su rama; T10 lo comprueba con `-rs` en el primer cambio de
>   `paso_archivo.py`.

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

**Dos métodos y ninguno más** (precisado el 2026-09-24, R48): ni listar
ficheros, ni mover, ni renombrar, ni borrar. Un test lo fija sobre los
nombres de los métodos, con el patrón de
`test_f032_r24_el_puerto_de_archivo_no_gana_borrado_ni_renombrado`. Es lo que
garantiza que los 142 partes sueltos de VILLA 04 no se tocan.

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

> **Añadido el 2026-09-24 · R44 y R50.** Una segunda lectura, en el mismo
> puerto (es la misma pasarela, el mismo `sql/read` y la misma fábrica):
>
> ```python
> # domain/models/destino_posventa.py
> @dataclass(frozen=True)
> class UnidadDeObra:
>     obra_ref: str            # referencia OPACA de la obra (upv.obride); solo para contar obras (R44)
>     obra_codigo: str | None
>     unidad_codigo: str | None
>     unidad_nombre: str | None
>
> # domain/ports/ubicacion.py
>     def leer_unidades_del_numero(self, *, codigo_obra: str) -> tuple[UnidadDeObra, ...]:
>         """Las unidades de posventa de las obras cuyo código tiene el número de
>         `codigo_obra` (o el mismo código, si no es numérico). El SQL
>         preselecciona; el dominio decide qué fila es de la misma obra (§4.7)."""
> ```
>
> `obra_ref` es un identificador del ERP y se trata como los de SharePoint
> (R23): no se loguea, no se devuelve, no se persiste y no aparece en ningún
> mensaje ni candidata. Sirve **solo** para contar obras distintas: dos obras
> con el mismo código literal (`0677` y `0677`) no se distinguen de otra forma.

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

> **Enmienda del 2026-09-24 · T4-4: la obra casa por su número.** La regla
> de arriba («empieza por el código seguido de un blanco», comparación
> literal) queda **solo** para códigos de obra que no son numéricos. T2 midió
> que la carpeta real de la 0677 es `677  MIRASIERRA`: la literal no la casaba,
> y todos los partes de la obra piloto habrían sido 409 `obra_parecida`.
>
> ```python
> def numero_de_obra(codigo: str) -> int | None:
>     """int(codigo) si, ya normalizado, está formado solo por cifras 0-9;
>     None si lleva cualquier otra cosa (códigos administrativos)."""
> ```
>
> **Regla estricta nueva** (R10): con `n = numero_de_obra(codigo_obra)` no
> nulo, una carpeta casa si `nombre.split()` —blancos de cualquier clase y
> cantidad— no está vacío, su **primera palabra** cumple
> `re.fullmatch("[0-9]+", palabra)` (cifras ASCII: `str.isdigit` admitiría
> `²`) e `int(palabra) == n`. El resto del nombre no se mira. Con `n` nulo, la
> literal de siempre.
>
> | Carpeta (obra `0677`) | ¿Casa? | ¿Parecida (§4.5)? |
> |---|---|---|
> | `677  MIRASIERRA` (la real) | **Sí** | no (casa) |
> | `0677 MIRASIERRA` | Sí | no |
> | `677` | Sí | no |
> | `00677 X` | Sí (mismo entero) | no |
> | `0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)` (la que crearía el sistema) | Sí | no |
> | `06770 X` | No (6770) | No |
> | `0677-MIRASIERRA` | No (la primera palabra no es solo cifras) | **Sí** |
> | `677MIRASIERRA` | No | **Sí** (§4.5 enmendado) |
> | `OBRA 0677`, `LISTADO 677` | No | **Sí** |
> | `0680 OTRA` | No | No |
>
> Dos carpetas que casan —`677  MIRASIERRA` y `0677 MIRASIERRA FASE 2`— son
> `obra_ambigua` con las dos (R13): el sistema no elige por el resto del
> nombre ni por los ceros. **Por qué no se elige «la más parecida»**: sería
> volver a mirar el nombre, que es justo lo que la medición demostró que no
> se puede derivar de Sigrid.
>
> **Lo que se pierde, y se acepta**: con la literal, `0677` y `677` eran
> obras distintas; ahora van a la misma carpeta. Solo es un problema si
> Sigrid tiene **dos obras** con el mismo número, y eso lo para R44 (§4.7).

### 4.2 Los tramos fijos (R14, R16, R34, R35)

```python
def carpeta_con_nombre(nombres: Iterable[str], *, buscado: str) -> tuple[str, ...]:
```

Igualdad por `clave_de_unidad` (mayúsculas, sin tildes, blancos colapsados):
`Partes Incidencias` casa con `PARTES INCIDENCIAS`, y se usa **el nombre tal
y como existe**. Dos que casen (p. ej. `PARTES INCIDENCIAS` y `Partes
incidencias`) → ambigüedad → 409.

> **Añadido el 2026-09-24 · T4-6 (R49).** La hoja admite **una** forma
> alternativa, la de `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` (por omisión
> `PARTES FIRMADO`, el literal de VILLA 02):
>
> ```python
> def carpeta_con_nombre(nombres, *, buscado: str, alternativa: str = "") -> tuple[str, ...]:
> ```
>
> Casa lo que tenga la clave de `buscado` **o** la de `alternativa` (si no
> está vacía); nada más. `INCIDENCIAS` no tiene alternativa. La regla es
> mínima a propósito: **una** forma más, escrita, y no «singular o plural».
>
> | Hojas en la unidad | Resultado |
> |---|---|
> | `PARTES FIRMADOS` | casa, se usa |
> | `PARTES FIRMADO` (VILLA 02) | casa, se usa **con su nombre** |
> | `Partes Firmado` | casa (misma clave) |
> | `PARTES FIRMADOS` y `PARTES FIRMADO` | **`firmados_ambigua`** → 409 con las dos |
> | `PARTE FIRMADO`, `FIRMADOS 2024` | no casan; **parecidas** (§4.5) → 409 `firmados_parecida` |
> | ninguna subcarpeta (VILLA 04) | 0 y 0 → **se crea `PARTES FIRMADOS`** (R48), nunca la alternativa |
> | alternativa configurada vacía y solo `PARTES FIRMADO` | no casa; parecida → 409 |

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

> **Medido el 2026-09-24: la regla se sostiene (D-6 cerrada).** Los siete
> casos reales casan por la regla 2, contra el `con.res`:
> `K(VILLA 05) = (VILLA, 5)` es sufijo de
> `K(Viviendas Bloque Villa 5) = (VIVIENDAS, BLOQUE, VILLA, 5)`. La regla 1
> no casa nunca con los datos reales —`K(0677.03VILLA 5.) = (677, 03VILLA, 5)`—
> y se deja: no estorba y cubre un ERP que algún día guarde la forma corta.
> `VILLA 01` **no** casa con la unidad 11 (`(VILLA, 1)` no es sufijo de
> `(…, VILLA, 11)`), que es lo que R50 vuelve a comprobar contra todas las
> unidades de la obra.

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

> **Enmienda del 2026-09-24 · lo que la medición enseñó de las amplias.**
> Casan y parecidas son una **partición** (se clasifica primero con la
> estricta; solo lo que no casa puede ser parecida), así que la carpeta real
> `677  MIRASIERRA` casa y **no** es parecida. Y las tres amplias se
> ensanchan, porque su error cuesta un 409 y el de quedarse cortas, un
> duplicado:
>
> - **Obra**: en vez de los tokens de la clave, **todas las secuencias de
>   cifras** del nombre (`re.findall("[0-9]+", nombre)`), comparadas como
>   entero con el número de la obra. Así `677MIRASIERRA` y `OBRA0677` también
>   paran, y `06770 X` sigue sin parar. Para códigos no numéricos, lo de
>   antes.
> - **Unidad**: del lado de la carpeta, también **todas las secuencias de
>   cifras** (`VILLA5`, `V-5`). Del lado de la unidad, los números de
>   `K(unidad_nombre)` y el `<n>` del patrón de R37 si el `con.cod` lo cumple;
>   **no** todos los de `K(unidad_codigo)`: el `con.cod` medido
>   (`0677.03VILLA 13.`) lleva el número de la obra y el `03` del grupo, y con
>   ellos `VILLA 03` sería parecida de la unidad 13 y bloquearía crear
>   `VILLA 13` (T4-5). Solo si el `con.cod` no cumple el patrón se usan los de
>   `K(unidad_codigo)`, como antes.
> - **Tramo fijo**: la palabra distintiva se compara **sin su `S` final** y
>   por **prefijo**: un token de la carpeta es del tramo si empieza por
>   `FIRMADO` (o `INCIDENCIA`). Motivo, medido: la hoja de VILLA 02 es
>   `PARTES FIRMADO`, y con «contiene el token `FIRMADOS`» **no** habría sido
>   parecida —el sistema habría creado `PARTES FIRMADOS` a su lado—. Hoy casa
>   como alternativa (§4.2), pero `PARTE FIRMADO` o `PARTES INCIDENCIA` tienen
>   que parar.
>
> | Nivel | Carpeta | Para lo buscado | Estricta | Amplia | Resultado |
> |---|---|---|---|---|---|
> | Obra | `677  MIRASIERRA` | obra 0677 | casa | — | se usa |
> | Obra | `677MIRASIERRA` | obra 0677 | no | sí | 409 `obra_parecida` si no hay otra que case |
> | Unidad | `VILLA 03` | unidad 13 (`0677.03VILLA 13.`) | no | **no** | no bloquea: se crea `VILLA 13` |
> | Unidad | `VILLA 01` … `VILLA 07` | unidades 8 … 15 | no | no | se crean `VILLA 08` … `VILLA 15` |
> | Unidad | `VILLA5` | unidad 5 | no | sí | 409 `unidad_parecida` |
> | Hoja | `PARTE FIRMADO` | `PARTES FIRMADOS` | no | sí | 409 `firmados_parecida` |
> | Hoja | `PARTES FIRMADO` | `PARTES FIRMADOS` | **casa** (alternativa) | — | se usa |
> | Incidencias | `PARTES INCIDENCIA` | `PARTES INCIDENCIAS` | no | sí | 409 `incidencias_parecida` |
>
> Consecuencia nueva, aceptada: una unidad con el número de la obra en el
> nombre de otra carpeta hermana (`LISTADO 677` dentro de `PARTES
> INCIDENCIAS`) ya **no** bloquea, porque el número de la obra dejó de ser
> número de la unidad. Es lo correcto: no es la misma villa.

> **Enmienda del 2026-09-25 (F-049) · lo que se crea, con tres cifras; las
> reglas, igual.** La tabla de arriba decía, literal, que junto a `VILLA 01` …
> `VILLA 07` *«se crean `VILLA 08` … `VILLA 15`»*, y que junto a `VILLA 03`
> *«se crea `VILLA 13`»*. **Qué la invalidó**: la decisión del humano del
> 2026-09-25, «siempre con tres cifras» (§4.6). Se crean `VILLA 008` …
> `VILLA 015` y `VILLA 013`. **Las reglas estricta y amplia no cambian**: las
> dos comparan números enteros, así que con la biblioteca reorganizada
> (`VILLA 001` … `VILLA 007`, `VILLA 012`, `VILLA 013`) ninguna carpeta es
> parecida de otra unidad —`VILLA 001` no lo es de la 10 ni de la 11—, y
> `VILLA 01` con `VILLA 001` en la misma obra son dos candidatas que casan con
> la villa 1: `unidad_ambigua`, 409.

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

> **Enmienda del 2026-09-24 · T4-1: los nombres, decididos con la medición
> delante.** La tabla y las reglas de arriba se conservan como se escribieron;
> esto es lo que manda desde hoy.
>
> | Nivel | Nombre al crear | Por qué |
> |---|---|---|
> | Obra | `<cod obra> <con.res de la obra>`, blancos colapsados (**sin cambios**, R36) | T2 midió `677  MIRASIERRA`, que no se deriva del `con.res` sin inventar. Posventa puede renombrarla: mientras empiece por el número y un blanco, se sigue encontrando (§4.1). Para la 0677 **no se crea**: existe |
> | `PARTES INCIDENCIAS` | literal de `SHAREPOINT_CARPETA_INCIDENCIAS` | — |
> | Unidad | **`VILLA NN`**, derivado del `con.cod` (R37) | T2 midió siete `VILLA 01` … `VILLA 07`, siempre dos cifras; T3, que ni `con.cod` ni `con.res` tienen esa forma. El humano eligió «unidad al estilo Posventa» |
> | `PARTES FIRMADOS` | literal de `SHAREPOINT_CARPETA_FIRMADOS`; **nunca** la alternativa | R49 |
>
> ```python
> #: R37 · el único patrón del que se deriva un nombre de unidad. Medido en T3.
> PATRON_CODIGO_UNIDAD = re.compile(r"(?P<obra>[0-9]+)\.(?P<grupo>[0-9]+)VILLA +(?P<n>[0-9]+)\.")
>
> def nombre_derivado_de_unidad(unidad_codigo: str | None, *, codigo_obra: str) -> str | None:
>     """`VILLA NN` si `unidad_codigo.strip()` cumple ENTERO el patrón (fullmatch)
>     y el número de su <obra> es el de `codigo_obra`; None en otro caso.
>     NN = f"{int(n):02d}". El <grupo> no entra en el nombre (Posventa no lo usa)."""
> ```
>
> `None` → 409 `unidad_sin_nombre_derivable` **solo si hay que crear** la
> unidad (R37). Las mayúsculas de `VILLA` son las medidas y no se relajan;
> un `con.cod` con otra palabra (`CHALET`, `PORTAL`) no se deriva: ampliar el
> patrón exige medir cómo lo nombra Posventa, y es otra enmienda.
>
> **Los 15 casos medidos de la 0677** (T2 y T3). Es la tabla que T6 convierte
> en test, fila a fila:
>
> | `con.cod` (Sigrid) | `con.res` (Sigrid) | Carpeta en Posventa hoy | Nombre derivado | Qué hará el sistema |
> |---|---|---|---|---|
> | `0677.03VILLA 1.` | `Viviendas Bloque Villa 1` | `VILLA 01` con `PARTES FIRMADOS` | `VILLA 01` (no hace falta: casa la existente) | resuelve; no crea nada |
> | `0677.03VILLA 2.` | `Viviendas Bloque Villa 2` | `VILLA 02` con `PARTES FIRMADO` | `VILLA 02` (no hace falta: casa la existente) | resuelve; archiva en `PARTES FIRMADO` (R49) |
> | `0677.03VILLA 3.` | `Viviendas Bloque Villa 3` | `VILLA 03` con `PARTES FIRMADOS` | `VILLA 03` (no hace falta: casa la existente) | resuelve; no crea nada |
> | `0677.03VILLA 4.` | `Viviendas Bloque Villa 4` | `VILLA 04` **sin subcarpetas** (142 ficheros sueltos) | `VILLA 04` (no hace falta: casa la existente) | resuelve la unidad; **crea `PARTES FIRMADOS`** (R48) |
> | `0677.03VILLA 5.` | `Viviendas Bloque Villa 5` | `VILLA 05` con `PARTES FIRMADOS` | `VILLA 05` (no hace falta: casa la existente) | resuelve; no crea nada |
> | `0677.03VILLA 6.` | `Viviendas Bloque Villa 6` | `VILLA 06` con `PARTES FIRMADOS` | `VILLA 06` (no hace falta: casa la existente) | resuelve; no crea nada |
> | `0677.03VILLA 7.` | `Viviendas Bloque Villa 7` | `VILLA 07` con `PARTES FIRMADOS` | `VILLA 07` (no hace falta: casa la existente) | resuelve; no crea nada |
> | `0677.03VILLA 8.` | `Viviendas Bloque Villa 8` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 08` | **crea** `VILLA 08` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
> | `0677.03VILLA 9.` | `Viviendas Bloque Villa 9` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 09` | **crea** `VILLA 09` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
> | `0677.03VILLA 10.` | `Viviendas Bloque Villa 10` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 10` | **crea** `VILLA 10` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
> | `0677.03VILLA 11.` | `Viviendas Bloque Villa 11` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 11` | **crea** `VILLA 11` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
> | `0677.03VILLA 12.` | `Viviendas Bloque Villa 12` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 12` | **crea** `VILLA 12` y su `PARTES FIRMADOS` al llegar el primer parte (9 reclamaciones hoy) |
> | `0677.03VILLA 13.` | `Viviendas Bloque Villa 13` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 13` | **crea** `VILLA 13` y su `PARTES FIRMADOS` al llegar el primer parte (213 reclamaciones hoy) |
> | `0677.03VILLA 14.` | `Viviendas Bloque Villa 14` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 14` | **crea** `VILLA 14` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
> | `0677.03VILLA 15.` | `Viviendas Bloque Villa 15` | no existe (humano: «no tienen carpeta, que se creen») | `VILLA 15` | **crea** `VILLA 15` y su `PARTES FIRMADOS` al llegar el primer parte (0 reclamaciones hoy) |
>
> Casos fuera del patrón, también en la tabla del test: `0677.03VILLA 13`
> (sin punto final), `0677.03Villa 13.` (minúsculas), `0677.03CHALET 3.`,
> `0680.03VILLA 13.` (otra obra), `0677.VILLA 13.` (sin grupo), `None` y
> `""` → `None`; `0677.03VILLA  13.` (dos blancos) → `VILLA 13`;
> `0677.03VILLA 100.` → `VILLA 100`; `00677.03VILLA 5.` con obra `0677` →
> `VILLA 05` (mismo número de obra).
>
> **`SHAREPOINT_NOMBRE_UNIDAD` sobra, y se retira** (R1, R3). Con una regla
> fija no hay nada que elegir; y la variable tenía un valor, `nombre`, que
> habría creado `Viviendas Bloque Villa 13` al lado de `VILLA 01` … `VILLA 07`.
> La condición de «si `con.res` trae nombres de persona, `nombre` queda
> descartado» deja de hacer falta: T3 midió que no los trae, y en todo caso
> ya no se usa para crear.
>
> **Y la propiedad de R39 pasa de demostrarse a comprobarse** (R46). Con la
> derivación, «lo creado casa consigo mismo» ya no es trivial: `VILLA 13`
> casa con la unidad 13 **porque** su `con.res` acaba en `Villa 13` (§4.3,
> regla 2), no porque salga de él. Una unidad cuyo `con.res` fuera
> `Villa 13 bis` recibiría `VILLA 13`, que ni casaría con ella ni dejaría de
> ser su parecida: la siguiente resolución daría 409 para siempre. Por eso el
> resolutor, antes de anotar cada creación, aplica la regla estricta del
> nivel al nombre compuesto con los mismos datos; si no casa, 409
> `nombre_no_casaria` y nada creado.

> **Enmienda del 2026-09-25 (F-049) · `VILLA` con al menos tres cifras.** El
> código de arriba decía, literal: *«`NN = f"{int(n):02d}".`»*, y la fila de
> la unidad, que T2 midió siete `VILLA 01` … `VILLA 07`, siempre dos cifras.
> **Qué lo invalidó**: el script 23, en el paso 2 del corte (2026-09-25),
> mostró que Posventa ha reorganizado sus unidades a `VILLA 001` …
> `VILLA 007`, `VILLA 012` y `VILLA 013` (§1); el humano decidió ese día
> «siempre con tres cifras», en todas las obras. Desde hoy:
>
> ```python
> return f"VILLA {int(encaje['n']):03d}"
> ```
>
> es decir, `NN = f"{int(n):03d}"`: `8` → `VILLA 008`, `13` → `VILLA 013`,
> `100` → `VILLA 100`, `1000` → `VILLA 1000`. En la tabla de los 15 casos, la
> columna «Nombre derivado» pasa a `VILLA 001` … `VILLA 015`, y la última
> columna de las villas 8 a 15, a «**crea** `VILLA 008` … y su `PARTES
> FIRMADOS`»; con la biblioteca reorganizada, las villas 12 y 13 ya **no** se
> crean: casan con `VILLA 012` y `VILLA 013`. Los casos fuera del patrón no
> cambian; los que se derivan, sí de ancho: `0677.03VILLA  13.` →
> `VILLA 013`, `00677.03VILLA 5.` → `VILLA 005`. **Lo que no cambia**: el
> patrón, el 409 `unidad_sin_nombre_derivable`, R46 (`VILLA 013` casa con la
> unidad 13 porque su clave es `(VILLA, 13)`, sufijo de la de su `con.res`) y
> R50.

### 4.7 · Números repetidos en Sigrid (R44, R50) — añadido el 2026-09-24

Casar por número tiene un precio que la regla literal no tenía: **todo** lo
que en Sigrid tenga el mismo número va a la misma carpeta de Posventa. Dos
comprobaciones puras sobre la segunda lectura (§3.3, §6.2):

```python
def obras_del_mismo_numero(filas: Iterable[UnidadDeObra], *, codigo_obra: str) -> frozenset[str]:
    """Los `obra_ref` distintos de las filas cuyo `obra_codigo` es la misma obra:
    mismo número (§4.1) o, si no es numérico, el mismo código normalizado."""

def unidades_que_casan(filas: Iterable[UnidadDeObra], *, carpeta: str) -> tuple[UnidadDeObra, ...]:
    """Las unidades de la obra con las que `carpeta` casa por la regla ESTRICTA de §4.3."""
```

- **R44 · la obra.** Si `obras_del_mismo_numero` no tiene **exactamente
  una**, 409 `obra_numero_no_unico` antes de listar nada. Hoy, medido: en la
  0677, **una** (T3 buscó `0677` y `677` con unidades de posventa); en
  general, 922 obras y 846 códigos en el maestro (§1), así que habrá obras en
  las que esto pare. Es lo correcto: Posventa tampoco podría distinguirlas por
  su carpeta. Si la lectura trae **1.000 filas** (el techo de `sigrid-api`),
  409 `unidades_sin_verificar`: con la respuesta posiblemente cortada no se
  puede afirmar ni R44 ni R50.
- **R50 · la unidad.** Elegida o compuesta la carpeta de unidad, con las
  filas de **esa** obra: `unidades_que_casan` tiene que dar **exactamente
  una**. Si dos unidades de Sigrid casan con `VILLA 05` —dos grupos con una
  villa 5 cada uno, `0677.03VILLA 5.` y `0677.04VILLA 5.`, que la derivación
  de R37 llevaría al mismo nombre porque ignora el grupo—, 409
  `unidad_carpeta_compartida`. En la 0677 hay un solo grupo (`03`) y quince
  números distintos **[MEDIDO, T3]**, así que no para nada.

**Por qué no se decide con la primera lectura**: la ubicación trae **una**
fila, la de la reclamación; saber si hay otra obra u otra unidad con el mismo
número exige mirar las demás. **Por qué una lectura y no dos**: las unidades
de las obras con ese número responden a las dos preguntas a la vez y son
pocas (15 en la piloto). **Decisión del spec-author, a validar por el humano
sin bloquear** (`requirements.md` §0 ter): las dos fallan cerradas.

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

> **Enmienda del 2026-09-24 · el paso de hoy y la medición.** La firma, el
> algoritmo y la tabla de arriba se escribieron antes de que F-031, F-033 y
> F-034 se cerraran y desplegaran, y antes de medir. Tres cosas quedaron
> viejas: la fila 3 dice «L1 **inerte** hoy» y L1 está activa desde F-033;
> falta el **1 bis** de F-031 (el cotejo de los códigos declarados); y el
> resolutor recibía `ctx`, que le habría dado acceso a `ctx.extraccion` y a
> `ctx.situacion` por la puerta de atrás. Esto es lo que manda:
>
> **La firma.** Sin contexto; los códigos, como cadenas, y ya guardados:
>
> ```python
> def resolver_destino_posventa(
>     *, codigo_obra: str, numero_incidencia: str, nombre_fichero: str,
>     explorador: ExploradorBibliotecaPort, ubicaciones: UbicacionPort,
>     base: str, incidencias: str, firmados: str, firmados_alternativa: str,
>     crear_carpetas: bool,
> ) -> DestinoResuelto:
> ```
>
> El borde fija con `functools.partial` todo menos los tres primeros y lo
> pasa como `resolver_destino`; el paso lo llama con
> `guardados.codigo_obra`, `guardados.numero_incidencia` y el nombre del
> fichero. Así `codigos_guardados` sigue viviendo solo donde dicen las tablas
> de F-031 y F-034 (§2.3), y el resolutor no puede leer lo que no le llega.
>
> **El algoritmo** (sustituye a los pasos 1–5 de arriba):
>
> 1. `leer_ubicacion(a_codigo_de_sigrid(numero_incidencia))` → R7. Fallo de
>    red o configuración → sube tal cual (503, R41).
> 2. R8 con `normalizar_codigo` a los dos lados (no `es_el_mismo_codigo`, §2.3).
> 3. `leer_unidades_del_numero(codigo_obra)` → R44 (`obra_numero_no_unico`,
>    `unidades_sin_verificar`). Fallo de red → 503 (R41).
> 4. Por nivel, en orden (obra, `INCIDENCIAS`, unidad, `FIRMADOS`):
>    `listar_carpetas(padre)` → casan / parecidas (§4.1, §4.2 con la
>    alternativa en la hoja, §4.3, §4.5): 1 casa → se baja; >1 →
>    `<nivel>_ambigua`; 0 y ≥1 parecida → `<nivel>_parecida`; 0 y 0 → si
>    `crear_carpetas`, se **compone** el nombre de ese nivel (R36, R37 →
>    `unidad_sin_nombre_derivable`), se comprueba (R38 →
>    `nombre_carpeta_imposible`; R46 → `nombre_no_casaria`) y se **anota**; los
>    niveles de debajo se componen, comprueban y anotan **sin listar**; si no,
>    `sin_carpeta_<nivel>` (R16).
> 5. En cuanto la unidad está elegida o anotada, R50 con las filas de su obra
>    (`unidad_carpeta_compartida`).
> 6. Nada se crea aquí; devuelve `DestinoResuelto`. Los nombres se componen
>    **cuando hacen falta** (precisión de R38): la garantía de «ningún nombre
>    imposible deja una carpeta a medias» la da que el paso solo ejecuta
>    `carpetas_por_crear` tras una resolución completa.
>
> Lecturas por parte: **dos** de Sigrid y **hasta cuatro** listados; con 22
> partes, ~130 llamadas, todas lecturas. Sin caché, por lo mismo que antes.
>
> **El orden en el paso** (sustituye a la tabla de arriba, que se conserva).
> Es el de `paso_archivo` hoy (`application/pipelines/paso_archivo.py`,
> líneas 273–311) con el resolutor insertado:
>
> | # | Paso | `por_obra` (hoy, sin tocar) | Con `posventa` |
> |---|---|---|---|
> | 1 | Puerta de estado `aprobado` (`_exigir_admitido`) | igual | igual |
> | 1 bis | Cotejo de los declarados con los guardados (`exigir_codigos_declarados`, F-031) | igual | igual |
> | 2 | Nombre del fichero desde **lo guardado** (`codigos_guardados`, F-031) | `componer_destino(carpeta_base, …)` | `nombre_de_archivo(…)` —el mismo nombre; la carpeta aún no se conoce |
> | 3 | **L1** desde el almacén (`situacion_leida(...).archivo`, F-033) | igual | igual, y **antes** de resolver (R45): el aviso de otro destino compara nombre y biblioteca, no carpeta |
> | 4 | **Resolver destino** | — | §5 arriba. `DestinoNoResuelto` → log de R47 si la traza guardada es `pendiente` → traza `error` con motivo (R18) → se relanza |
> | 5 | Aviso del intento anterior (F-033 R20) | igual | igual, contra la carpeta **resuelta** |
> | 6 | Traza previa `pendiente` (F-019); `SIN_CAMBIOS` → la de la otra petición (F-033 R18) | igual | igual, con la carpeta resuelta |
> | 7 | Carpeta | `asegurar_carpeta` | `crear_subcarpeta` por cada `carpetas_por_crear`, en orden; aviso y log por carpeta (R40); **nunca** `asegurar_carpeta` (R15) |
> | 8–10 | `buscar`, `subir` (replace), traza final (F-033 R19) | igual | igual |
>
> **Por qué entre L1 y el aviso, y no en otro sitio.** Antes de L1, un parte
> ya archivado —los 133 de IT, por ejemplo— llamaría a Sigrid y listaría la
> biblioteca de Posventa por nada, contra R25 y R45. Después del aviso, el
> aviso compararía la traza `pendiente` con una carpeta que aún no se conoce.
> Y antes de la traza previa por R22.
>
> **Cómo L1 decide «otro destino» sin carpeta (R45).** `_en_otro_destino` de
> F-033 compara nombre, carpeta y biblioteca, y no se cambia su firma (la
> fijan los tests de F-033). En `posventa`, el paso le da en el punto 3 un
> `DestinoArchivo` cuya carpeta es **la de la propia traza guardada**: la
> carpeta no puede discrepar y decide lo demás. Un test de F-013 lo fija:
> un parte `archivado` en IT (otro `drive_id`) corta con los dos avisos de
> F-033 y **cero** llamadas a ubicaciones y al explorador.

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

> **Añadido el 2026-09-24 · la segunda lectura (R44, R50).** Dos sentencias
> más en `consultas_ubicacion.py`, **una** de las cuales se usa por parte
> según el código de obra sea numérico o no. Preseleccionan; decide el
> dominio (§4.7):
>
> ```sql
> -- SQL_UNIDADES_DEL_NUMERO  (código numérico; parámetros ('%677', '%[^0]%677'))
> SELECT v.obride, o.cod, u.cod, u.res
> FROM dbo.upv v
> JOIN dbo.con o ON o.ide = v.obride
> JOIN dbo.con u ON u.ide = v.ide
> WHERE LTRIM(RTRIM(o.cod)) LIKE ? AND LTRIM(RTRIM(o.cod)) NOT LIKE ?
>
> -- SQL_UNIDADES_DEL_CODIGO  (código no numérico; parámetro (código normalizado,))
> SELECT v.obride, o.cod, u.cod, u.res
> FROM dbo.upv v
> JOIN dbo.con o ON o.ide = v.obride
> JOIN dbo.con u ON u.ide = v.ide
> WHERE LTRIM(RTRIM(o.cod)) = ?
> ```
>
> - El primer patrón es el número **sin ceros a la izquierda** con `%`
>   delante (`%677`); el segundo quita lo que acaba igual pero lleva otra cifra
>   o letra delante (`1677`, `X677`): así el techo de 1.000 filas lo consumen
>   solo las obras con ese número. Los dos parámetros los compone el adaptador
>   a partir de `numero_de_obra` (dominio); solo cifras, así que no hay nada que
>   escapar en el `LIKE`. Aunque el SQL dejara pasar de más, el dominio vuelve
>   a filtrar por número (§4.7).
> - `v.obride` sale como `obra_ref` en texto y **no** se loguea (§3.3).
> - Mismo adaptador, mismo `sql/read`, misma política de reintentos y de
>   errores que la primera; misma prohibición de `sql/write`.
> - **[NO MEDIDO]**: el tiempo de esta lectura contra el ERP real (el `LIKE`
>   con `%` delante recorre las obras con unidades de posventa). Se espera
>   pequeño —`upv` y el maestro de obras son tablas de miles de filas— y lo
>   mide el primer archivado real (§7.3); si pasara de unos segundos, se
>   enmienda con la medición delante, no a ojo.
> - `LTRIM(RTRIM())` y `LIKE` con clase de caracteres son T-SQL de cualquier
>   versión; no se usa `TRY_CAST` (la versión del SQL Server de Sigrid no está
>   en `azure-apps/sigrid_api.md`).

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

> **Precisión del 2026-09-24 · cómo quedó en T1 y qué le toca en T14.**
>
> - **Parámetros que T1 añadió** y que esta spec no nombraba, aceptados:
>   `-MostrarNombres` (por defecto los nombres salen enmascarados,
>   `VILLA 05 - <txt>`), `-DesdeKeyVault` (lee las `GRAPH_*` del vault en
>   memoria, para no teclear el secreto), `-CarpetaObra` (fuerza el literal de
>   la carpeta de obra), `-MaxCarpetasObra`, y `-CarpetaBase`,
>   `-CarpetaIncidencias` y `-CarpetaFirmados` (`progress/impl_F-013.md` §2
>   y §3).
> - **Sin BOM**: los dos scripts son ASCII + CRLF, como los otros 25 de
>   `infra/`. Con BOM, `tests/test_f010_prompt_keys_infra.py` (lee todo
>   `infra/` como `ascii`) tumbaba la suite. Es la excepción documentada que
>   admite `docs/CONVENTIONS.md`; §11 y T1 se enmiendan igual.
> - **El defecto del resumen** (`progress/explore_F-013.md`): la tabla final
>   cuenta unidades, `PARTES INCIDENCIAS` y hojas **solo** bajo una carpeta de
>   obra que **case**. Como en la medición la 0677 solo era «parecida», el
>   resumen salió con ceros aunque el árbol de arriba traía los datos. La
>   medición es buena; el resumen engaña. T14 lo corrige: el resumen cuenta lo
>   que cuelga de la carpeta de obra que **resuelve la regla del dominio**
>   (que ya casa `677  MIRASIERRA`) y, si no resuelve ninguna, lo dice en una
>   línea propia («resumen sin obra resuelta: se muestran las parecidas») en
>   vez de dar ceros; con `-CarpetaObra`, cuenta la forzada y lo rotula.
> - **La regla, del dominio**: T14 sustituye `Test-ObraCasa`,
>   `Test-ObraParecida`, `Test-TramoCasa` y `Test-TramoParecido` (copias
>   provisionales en PowerShell) por el dominio, ejecutado por fichero con
>   `Invoke-PythonDelServicio`. Así el 23 casa por número (§4.1), admite la
>   hoja alternativa (§4.2), usa las amplias enmendadas (§4.5), deriva
>   `VILLA NN` (§4.6) y comprueba R46 y R50: lo que dice «resolvería» o
>   «crearía» es lo que hará el sistema.
> - **Las unidades de Sigrid entran por fichero**: `24_ubicacion_sigrid.ps1`
>   gana `-SalidaCsv <ruta>` (fuera del repositorio; `con.cod`, `con.res`,
>   `v.obride` **no**) y el 23, `-UnidadesCsv <ruta>`. Sin él, el 23 hace lo de
>   hoy (árbol y casan / parecidas) y lo dice.

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
3. ~~Consulta de solo lectura de lo archivado en IT (R26) y anotación del
   recuento, sin identificadores.~~ **Hecho ya, y fuera del corte**
   (2026-09-22): el recuento se midió el 2026-09-18 con
   `infra/25_mediciones_despliegue.ps1` —**133**, todas `archivado`, todas en
   la biblioteca de IT—. No hay que repetirlo ni hacer nada con esas trazas
   (§9 bis). Si se quiere confirmar que no han crecido, la misma medición, de
   solo lectura.
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

> **Enmienda del 2026-09-24 · T4-3: «crear desde el principio», con las
> ventanas abiertas.** El runbook de arriba se conserva como se escribió. Da
> por hecho que tras desplegar con `posventa` la ventana `ARCHIVO_HABILITADO`
> está **cerrada** y se abre «solo para el parte autorizado» (paso 6). Desde
> el 2026-09-23 `desplegar_backend.ps1` la deja **abierta** por defecto
> (decisión del humano: Posventa ya usa el servicio en real), y el humano
> decidió en T4 que `SHAREPOINT_CREAR_CARPETAS` va **activo desde el primer
> despliegue**. Consecuencia: el primer archivado en Posventa, y la primera
> carpeta creada, los provoca **quien archive primero**. No hay «parte
> autorizado único» que prometer. Este es el runbook que manda (va a
> `docs/DESPLIEGUE.md` en T17):
>
> **Antes de desplegar** (solo lecturas, el humano):
>
> 1. F-033, F-031 y F-034 desplegadas. **Ya lo están** (2026-09-23).
> 2. Relanzar el 24 y el 23 **ya con T14** para la 0677
>    (`24_ubicacion_sigrid.ps1 -CodigoObra 0677 -SalidaCsv <fuera del repo>` y
>    `23_destino_posventa.ps1 -UrlSitio … -CodigoObra 0677 -DesdeKeyVault
>    -UnidadesCsv <el mismo>`). Tiene que salir **exactamente** lo de R31:
>    obra, `PARTES INCIDENCIAS` y VILLA 01, 02, 03, 05, 06, 07 «resolvería»;
>    VILLA 04 «crearía `PARTES FIRMADOS`»; VILLA 08–15 «crearía `VILLA NN`» y su
>    hoja; ninguna «bloquearía». Si no, **no se despliega** y vuelve al líder.
> 3. **Avisar a Posventa antes de desplegar**, por escrito: desde el
>    despliegue, lo archivado va a su biblioteca; el sistema **creará** las
>    carpetas que falten (en la 0677, `VILLA 08` … `VILLA 15` según lleguen sus
>    partes —la 12 y la 13 tienen reclamaciones— y `PARTES FIRMADOS` dentro de
>    `VILLA 04`); en `VILLA 02` archivará en su `PARTES FIRMADO`; convivirá con
>    sus ficheros manuales (§9, nota final); y si ven una carpeta que no
>    quieren, **que no la borren**: nos avisan y se sigue R43.
>
> **El despliegue:**
>
> 4. Cargar en Key Vault los IDs de Posventa (`cargar_secretos_postventa.ps1
>    -Solo`), igual que antes.
> 5. `00_vars_postventa.ps1`: `$EstructuraArchivo = "posventa"`,
>    `$CarpetaBaseArchivo = ""` (D-1), `$CrearCarpetasArchivo = "true"`.
>    `desplegar_backend.ps1` **sin** `-VentanasCerradas`. Desde este momento
>    cualquier archivado va a Posventa y puede crear carpetas.
>
> **Justo después** (solo lecturas, el humano, en el mismo rato):
>
> 6. Comprobar la configuración desplegada: `22_ventana_archivo.ps1` sin
>    parámetros dice «abierta», y los App Settings `SHAREPOINT_ESTRUCTURA`,
>    `SHAREPOINT_CARPETA_BASE` y `SHAREPOINT_CREAR_CARPETAS` valen `posventa`,
>    vacío y `true` (mirándolos en el portal de Azure, sin cambiar nada; T17
>    decide si el runbook lo hace con un `az … appsettings list` de solo
>    lectura).
>
> **El mismo día, cuando haya archivados** (solo lecturas + Posventa):
>
> 7. **R33**: `25_mediciones_despliegue.ps1` cuenta ya trazas `archivado` en
>    una **segunda** biblioteca (la de Posventa; sin imprimir su ID). Con
>    Posventa, sobre uno de esos partes de una ruta que ya existía: está en su
>    carpeta y en su OneDrive. Resultado a `progress/`, sin identificadores.
> 8. **R42**: en cuanto aparezca la primera carpeta creada —aviso en la
>    respuesta de `/api/archivar` y `F-013 carpeta creada: <ruta>` en el log
>    (R40)—, relanzar el 23 (solo lectura): esa unidad pasa a «resolvería». Con
>    Posventa: el nombre les sirve y no hay duplicado.
>
> **Frenos**, de más rápido a más completo, todos sin tocar datos:
>
> - `22_ventana_archivo.ps1 -Cerrar`: para **todo** el archivado en el acto,
>   sin redesplegar (la ventana del ERP no se toca).
> - `$CrearCarpetasArchivo = "false"` y redesplegar: sigue archivando donde la
>   ruta existe y da 409 `sin_carpeta_<nivel>` donde falta.
> - `$EstructuraArchivo = "por_obra"`, IDs de IT de vuelta en Key Vault y
>   redesplegar: la vuelta atrás de siempre.
>
> Si una carpeta creada no le sirve a Posventa: freno 1, R43 (lo deshace una
> persona), enmienda de R36/R37 y solo entonces se vuelve a abrir.
>
> **Riesgo aceptado por el humano, con nombre**: entre el paso 5 y el 8
> pueden crearse varias carpetas sin que nadie las haya visto. Lo contienen la
> medición de la obra piloto (paso 2), el aviso previo (paso 3) y que el freno
> es inmediato. El punto 1 del informe de T1 (`progress/impl_F-013.md` §8: «el
> primer archivado en Posventa no sería el autorizado de R33, y podría crear
> carpetas antes de R42») queda **cerrado por esta decisión**, no por un
> arreglo técnico.

> **Enmienda del 2026-09-25 (F-049) · el paso 2 y el aviso del paso 3, con
> la biblioteca reorganizada.** El paso 2 decía, literal: *«VILLA 08–15
> «crearía `VILLA NN`» y su hoja»*; el 3, *«en la 0677, `VILLA 08` …
> `VILLA 15` según lleguen sus partes»*. **Qué lo invalidó**: el propio paso
> 2, lanzado el 2026-09-25, mostró la biblioteca reorganizada (`VILLA 001` …
> `VILLA 007`, `VILLA 012`, `VILLA 013`, §1), y el humano decidió ese día
> «siempre con tres cifras» (§4.6). Lo que tiene que decir el 23 es lo de
> `requirements.md` R31, enmendado con esta fecha: obra, `PARTES
> INCIDENCIAS` y las unidades 1–7, 12 y 13 «resolvería» (o «crearía `PARTES
> FIRMADOS`» dentro de una carpeta sin hoja); las 8–11, 14 y 15 «crearía
> `VILLA 008`» … `VILLA 015` y su hoja; ninguna «bloquearía». El aviso a
> Posventa (paso 3) nombra `VILLA 008` … `VILLA 011`, `VILLA 014` y
> `VILLA 015`.

## 8 · Relación con F-033, F-031 y F-018

### 8.1 F-033 (L1 inerte) — **D-2**

> **Título precisado el 2026-09-24**: «L1 inerte» describe cómo estaba
> antes de F-033. F-033 está **desplegada** y L1 es activa desde el almacén;
> la nota del 2026-09-22 de abajo lo matizaba, el título no.

Hoy `/api/archivar` sube siempre; lo que evitaba el duplicado era reemplazar
el homónimo **en la misma carpeta**. Con F-013 la carpeta cambia de biblioteca
entera, así que re-archivar un parte ya archivado en IT: (a) lo sube a
Posventa, contra H4; y (b) `upsert` de `postventa.archivos` por `hash_parte`
**pisa** `drive_id`, `carpeta` y `web_url`, y el puntero a IT se pierde, contra
R26. Y re-archivar no es raro: el circuito de F-025 re-archiva al reintentar.

> **Precisión del 2026-09-22.** F-033 está implementada, aprobada y mergeada
> en `dev`, así que este escenario ya está cerrado. Lo que su **D-1** decidió
> —cortar siempre por `hash` + estado— tiene una consecuencia que **el humano
> ha aceptado expresamente** y que ya no es una decisión abierta: los **133**
> partes archivados en IT **nunca se subirán a Posventa**. Ver §9 bis.

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

> **Enmienda del 2026-09-24 · F-031 está cerrada y desplegada.** El primer
> párrafo de §8.2 decía que F-013 usa los códigos «tal y como llegan al paso
> (`ctx.extraccion`), igual que hoy». Ya no es así, y hacerlo **rompería la
> suite**: desde F-031 el paso los toma de `codigos_guardados(ctx)`
> (`paso_archivo.py`, línea 276) y
> `test_f031_alcance_cerrado.py::test_f031_r29_el_paso_de_archivo_ya_no_lee_la_extraccion`
> —que se comprueba **siempre**, sin git— prohíbe cualquier acceso a
> `.extraccion` en `paso_archivo.py`. El resolutor recibe los códigos
> **guardados**, como dos cadenas (§5). El riesgo residual que se describía
> («un cuerpo que mienta en los dos de forma coherente») **lo cerró F-031**:
> los códigos del cuerpo ya solo se cotejan. Y la recomendación de orden **ya
> se cumplió** (F-033 → F-031 → F-034 → F-013). R8 sigue valiendo: ahora
> compara lo **guardado** con lo que dice Sigrid, que son dos fuentes
> independientes.

### 8.3 F-018 (mínimo privilegio)

Hoy la app tiene `Sites.ReadWrite.All` y `Sites.FullControl.All`, así que
**escribirá en el sitio de Posventa sin que nadie le conceda nada**. Al
recortar a `Sites.Selected`, habrá que conceder **el sitio de Posventa**
(`write`) —y, si se conserva la lectura de lo de IT, el de IT (`read`)—.
Se anota en la ficha de F-018 (T18); no se hace aquí.

> **Precisión del 2026-09-22.** Con la premisa de localizar lo de IT derogada
> (§9 bis), el `read` sobre el sitio de IT **ya no lo pide F-013**: si se
> concede, será por otro motivo. Que no se conceda **no borra nada** —los
> ficheros siguen en su biblioteca—; es exactamente «olvidar sin borrar».

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

## 9 bis · Enmienda del 2026-09-22 · lo de IT se olvida, pero no se borra

> **La premisa original no se borra, se cita.** H4 del 2026-09-18: *«Lo ya
> archivado en IT se queda en IT, sin migración, y se documenta que sigue
> allí»*. De ahí salían R24–R26 y, en el diseño, el paso 3 del corte (§7.3) y
> el `read` sobre el sitio de IT (§8.3).

Dos frases del humano la enmiendan, y hay que leerlas juntas:

| Fecha | Literal | Qué hace |
|---|---|---|
| **2026-09-18** | *«lo que esta en IT eran pruebas, se puede olvidar»* | **Deroga** la parte de H4 que obligaba a documentar **cómo localizar** lo archivado en IT. Si eran pruebas, no hay inventario que mantener |
| **2026-09-22** | *«los partes en IT se pueden olvidar, pero no borrar»* | **Precisa** la anterior y pone el límite: olvidar **no** es borrar |

**Qué significa «no borrar», en concreto.** No se borra ni se toca **nada** de
estas tres cosas:

1. Los **ficheros** de la biblioteca de IT. Siguen donde están.
2. Las **filas de `postventa.archivos`** de esos partes. Ninguna sentencia del
   corte ni del despliegue de F-013 las toca.
3. La **traza `archivado`** con su `drive_id` de IT. **No** se retira para
   permitir re-archivarlos en Posventa. Era la alternativa que quedó apuntada;
   queda descartada.

**La contrapartida, que es la razón de escribir esto.** Con **D-1 de F-033**
—cortar siempre por `hash` + estado— una traza `archivado` impide volver a
subir ese parte. Al no tocar las trazas, los **133 partes** de IT **nunca se
subirán a la biblioteca de Posventa**. Es lo aceptado. F-013 archiva allí
**solo lo que se archive a partir de su despliegue**.

**La cifra, medida.** **133** trazas, todas `archivado` y todas con biblioteca,
en **una sola** biblioteca —la de IT—, fechadas del 2026-08-26 al 2026-09-18;
`pendiente`: **0**. **[MEDIDO]** el 2026-09-18 con
`infra/25_mediciones_despliegue.ps1`, de solo lectura. Fuente:
`progress/cierre_verificaciones_F-033.md`.

**Decisión abierta que se cierra.** La que dejaron apuntada el implementer de
F-033 y su review (**O-2**: *«F-013 tendrá que decidir qué hace con esas
trazas»*), repetida en el acta de cierre de F-033 como *«falta decidir si se
olvidan del todo o si al desplegar F-013 se les retira la traza»*. **Cerrada**:
no se les retira la traza, no se hace nada con ellas.

**H-3 de F-034 (añadido el 2026-09-24).** La puerta de archivo del gráfico
y del cierre (`exigir_parte_archivado`, `puerta_de_estado.py`) mira el
**estado** de la traza y **no su biblioteca**: un parte archivado en IT pasa
esa puerta igual que uno de Posventa, y se puede adjuntar y cerrar en Sigrid.
Esta spec lo lee como coherente con «olvidar sin borrar» —esos partes **están**
archivados— y **no toca la puerta** (§2.3). Anotado para que el humano lo
valide sin bloquear.

**Qué cambia en esta spec, y qué no.** Cambia el texto de H4, R24 y R26
(`requirements.md` §0 y §8), el paso 3 del corte (§7.3), la fila de riesgo de
§0.1, la nota de §8.1 y la de §8.3, y la tarea de documentación T17
(`tasks.md`). **No cambia** ni una línea de diseño ejecutable: ningún módulo,
ninguna sentencia, ningún test de comportamiento. Es una enmienda documental.

## 9 ter · La parada T4, cerrada por el humano el 2026-09-24

Con `progress/explore_F-013.md` delante. Literales en `requirements.md` §0
ter; aquí, qué toca cada una del diseño.

| Id | Decidido | Diseño |
|---|---|---|
| **T4-1** | Unidad `VILLA NN` derivada del `con.cod`; obra `<cod> <con.res>` literal | §4.6; `SHAREPOINT_NOMBRE_UNIDAD` retirada |
| **T4-2** | Unidad sin subcarpetas → se crea `PARTES FIRMADOS`; lo antiguo no se toca | §3.2 (dos métodos y ninguno más), §4.2 |
| **T4-3** | «Crear desde el principio», ventanas abiertas | §7.3 (runbook enmendado), §2.2 (`$CrearCarpetasArchivo`) |
| **T4-4** | Obra por número, ignorando el resto del nombre | §4.1, §4.5, §4.7 |
| **T4-5** | Villas 8–15 sin carpeta en ningún sitio: «que se creen» | §4.6 (tabla de 15) |
| **T4-6** | `PARTES FIRMADO` (VILLA 02) cuenta como hoja | §4.2 (una alternativa y ninguna más; con las dos → ambigua) |

Y las dos del spec-author que fallan cerradas, a validar sin bloquear: R44 y
R50 (§4.7). Con esto **no queda ninguna pregunta abierta de la medición**.

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

> **Enmienda del 2026-09-24 · lo que la medición cambia en los riesgos.**
> Los catorce de arriba se conservan; estos cinco los precisan o se añaden.
>
> - **10 (precisado)**: con el casado por número, dos obras de Sigrid con el
>   mismo número —no solo el mismo código— irían a la misma carpeta. Ya no es
>   «no molestan mientras la carpeta sea una»: lo para R44 (§4.7). En la 0677
>   hay una.
> - **11 (precisado)**: la regla amplia de tramo tenía un hueco medido —el
>   singular `PARTES FIRMADO` no era parecida—. Se ensancha (§4.5). Sigue el
>   residual de las grafías sin número (`VILLA CINCO`): T2 no encontró
>   ninguna en la 0677.
> - **12 (resuelto)**: el nombre de la obra creada sigue siendo largo, pero en
>   la 0677 no se crea; el de la unidad, `VILLA NN`, es el de Posventa (T4-1).
> - **15 (nuevo) · crear desde el principio**: entre el despliegue y la
>   comprobación con Posventa pueden crearse varias carpetas (§7.3). Aceptado
>   por el humano (T4-3); frenos en §7.3.
> - **16 (nuevo) · el literal de VILLA 02 no cuadra del todo con la
>   medición.** El script 23 marcó la hoja de VILLA 02 como «parecida» con su
>   regla provisional, que exigía la palabra `FIRMADOS` **exacta**; `PARTES
>   FIRMADO` no la contiene, así que con ese literal el script **no** la habría
>   marcado. O el literal lleva algo más de lo que se ha transcrito, o hay otra
>   carpeta. No bloquea: si el literal es otro, la regla nueva da 409
>   `firmados_parecida` (o `ambigua`), que es fallar cerrado. Se verifica en el
>   paso 2 del runbook (§7.3): VILLA 02 tiene que decir «resolvería»; si no,
>   vuelve al humano con el literal a la vista (`-MostrarNombres`).
> - **17 (nuevo) · el número de la obra ya no distingue `0677` de `677`**.
>   Aceptado por T4-4; lo cubre R44.

> **Añadido el 2026-09-25 (líder), de la review de F-013** (`progress/review_F-013.md` §8).
>
> - **18 (nuevo) · dos fuentes para la carpeta final (H-3).**
>   `destino_archivo.py` compone la carpeta final con `unir_ruta(base, …)` y los
>   padres de las creaciones con `camino.ruta`. Coinciden con toda configuración
>   real; divergen solo con una base cuyo primer tramo, recortado, empiece por
>   `/` (p. ej. `"/ /x"`). Es lo que deja vivo al mutante a mano M19, aceptado
>   por el humano como equivalente el 2026-09-25. **Mejora pendiente**, sin
>   cambio de comportamiento: `DestinoArchivo(carpeta=camino.ruta, …)`.
> - **19 (nuevo) · el `LIKE` de las unidades es más estrecho que «mismo
>   número» (H-4).** `SQL_UNIDADES_DEL_NUMERO` filtra con
>   `LTRIM(RTRIM(o.cod)) LIKE '%677'`, pero `numero_de_obra` quita **todos** los
>   blancos: una segunda obra con código `06 77` sería invisible a R44. Medido
>   que no ocurre en la 0677 (T3: una sola obra) e improbable en `con.cod`. Si
>   aparece, enmienda con medición.

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

> **Enmienda del 2026-09-24 · qué añade la medición a cada fichero.**
>
> | Fichero | Añade |
> |---|---|
> | `test_f013_destino_dominio.py` | Tabla de §4.1 enmendada entera (`677  MIRASIERRA` casa; `06770 X`, `0677-MIRASIERRA`, `677MIRASIERRA`, `OBRA 0677` no; código no numérico, literal); tabla de §4.2 (alternativa, ambigua con las dos, sin alternativa configurada); tabla de §4.5 enmendada (partición casan/parecidas; `VILLA 03` no es parecida de la 13); **los 15 casos de §4.6** y los de fuera del patrón (`nombre_derivado_de_unidad`); `obras_del_mismo_numero` y `unidades_que_casan` (§4.7) con dos obras `0677`, con `0677` y `677`, y con dos grupos que comparten villa |
> | `test_f013_resolver_destino.py` | R44 (dos obras → 409 **sin listar**; 1.000 filas → 409), R46 (un `con.res` que no acaba en la villa → `nombre_no_casaria`, cero creaciones), R48 (VILLA 04: solo se anota `PARTES FIRMADOS`), R49 (VILLA 02), R50 (dos unidades casan → 409), R37 (`unidad_sin_nombre_derivable` **solo** si hay que crear la unidad), la firma sin `ctx` y **el árbol medido de la 0677 entero**: las 15 unidades dan lo de la tabla de §4.6 |
> | `test_f013_paso_archivo_posventa.py` | El orden de §5 enmendado (registro de llamadas): el 1 bis antes de todo, L1 antes de la primera llamada a ubicaciones, el aviso de F-033 R20 contra la carpeta resuelta; R45 (un parte `archivado` en IT: dos avisos de F-033 y cero llamadas al resolutor); R47 (traza `pendiente` + destino no resuelto → línea de log antes de la traza `error`) |
> | `test_f013_arquitectura.py` | `destino_archivo.py` y `destino_posventa.py` no nombran `ContextoParte`, `extraccion`, `codigos_guardados`, `CodigosDelParte`, `es_el_mismo_codigo` ni `drive_id_vigente` (§2.3); `ExploradorBibliotecaPort` tiene **exactamente** `listar_carpetas` y `crear_subcarpeta` (R48); `obra_ref` no aparece en ningún `log.`/`logger.` ni en `DestinoNoResuelto` |
> | `test_f013_fabricas.py` | `settings.py` **no** tiene `sharepoint_nombre_unidad` (R3); `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` con su defecto y vacía |
> | `test_f013_ubicacion_sigrid.py` | Las dos sentencias nuevas carácter a carácter; los parámetros (`%677`, `%[^0]%677`) compuestos desde `numero_de_obra`; `obra_ref` en texto |
> | `test_f013_scripts_infra.py` | **Sin BOM** (ya lo dice el de T1: `test_f013_t1_sin_bom_como_el_resto_de_infra`), no «UTF-8 con BOM» como decía la fila de arriba; y en T14: el 23 ya no contiene `Test-ObraCasa` ni las otras tres copias; el resumen no filtra por `Marca -ne "parecida"`; `-UnidadesCsv` y `-SalidaCsv`, y el CSV del 24 sin `obride` |
>
> Y los que **no son de F-013 y tienen que seguir en verde sin tocarlos** en
> cada tarea que cambie `paso_archivo.py`, `archivar.py`, `graph.py` o
> `function_app.py`: `test_f006_*`, `test_f019_*`, `test_f031_*`,
> `test_f032_alcance_cerrado.py`, `test_f033_*` y `test_f034_*` (§2.3).

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
