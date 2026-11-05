<!-- specs/F-071-plantilla-desde-sigrid/design.md -->
# F-071 · La plantilla de incidencias saca todos sus desplegables de Sigrid al descargarla — Diseño

> **APROBADA POR EL HUMANO el 2026-11-05.** Decisiones D-1 a D-21 en §13; las
> respuestas a Q-1..Q-13 (versión 1, 2026-11-05) en §13.1 y en
> `progress/spec_F-071.md`. **D-1 queda pendiente** del resultado de la prueba
> manual del Bloque 0.
> Requisitos en `requirements.md`. Ejemplos siempre ficticios.
>
> **Hereda el diseño de F-058** (`git show feature/F-058-plantilla-ubicaciones-sigrid:specs/F-058-plantilla-ubicaciones-sigrid/design.md`),
> que el humano aprobó el 2026-10-09 y nunca se implementó: §4 (el desplegable
> dependiente), §5.1 (agrupar las listas) y §7.1–§7.3 (generador y YAML) se
> copian aquí con lo que cambia. F-058 no se mergea: la absorbe esta ficha.

## 1 · Qué cambia, en una frase por punta

- **Plantilla** (`GET /api/plantilla`): además del catálogo, la lectura de
  ubicaciones de F-056; `Ubicación` pasa a **desplegable dependiente** de la
  `Unidad` de la fila; `Oficio` y `Proveedor` pasan a **una entrada por código
  / por fila de `obrofc`**, con el código en la etiqueta, **sin grupos de
  equivalencia**; deja de leer PostgreSQL. Versión 2.
- **Importación** (`POST /api/importaciones`): rechaza la v1; lee catálogo y
  ubicaciones de Sigrid en el momento; valida la ubicación contra la unidad de
  su fila; resuelve oficio y proveedor a un código sin ambigüedad; tolera
  mayúsculas en todas las columnas tasadas con la clave de F-060; el Excel de
  errores sale v2 con las mismas listas.
- **Configuración**: la lista de ubicaciones sale del YAML; urgencias y
  listados se quedan (no hay catálogo de Sigrid que los sustituya, §8).

Encaje en `docs/ARCHITECTURE.md`: la misma hexagonal de F-036. El dominio puro
calcula opciones, agrupa listas y valida; la aplicación compone las lecturas;
el único módulo con `openpyxl` escribe el libro; los bordes componen los
adaptadores. **Ningún puerto nuevo**: se reutiliza `UbicacionesValidasPort` de
F-056 y su adaptador; `GeneradorPlantillaPort` cambia de firma.

## 2 · Límite de servicio

Todo es de `services/postventa-api` y de su dominio (la entrada de
incidencias de F-036). Las tres lecturas de Sigrid ya existen en este
servicio y van por `sigrid-api` (`sql/read`). **No** hace falta otro
microservicio, ni tocar `sigrid-api`, ni el front: la descarga y la subida no
cambian de forma (mismas rutas y códigos HTTP; un código nuevo de 400,
`version_anterior`, que el front enseña por su texto como los demás —
`js/importacion.js` no filtra códigos—). No se parte.

Lo que **sí** sería de otro sitio y se deja fuera: dar de alta en Sigrid una
ubicación que falta en una tipología (p. ej. «Escalera» en una villa con
escalera) es un dato de Sigrid que mantiene Posventa en su UI; este servicio
**nunca** escribe `prmtpl` (Q-8). Mandar la urgencia a Sigrid exigiría un
campo nuevo en `sigrid-api` §8.9 (`rcp.texurg`), en **su** repositorio (Q-2).

## 3 · Ficheros

### 3.1 · A crear

| Ruta | Qué |
|---|---|
| `services/postventa-api/domain/models/casado_con_lista.py` | Hoja del grafo de imports: `Coincidencia`, `UbicacionDeSigrid`, `clave_de_ubicacion`, `ubicacion_de_sigrid` **movidos tal cual** desde `normalizacion.py` (§5.5), más `casar_con_lista` para las demás columnas tasadas (R36) |
| `services/postventa-api/tests/test_f071_dominio_opciones.py` | R8, R12–R15, R17, R22 (opciones de oficio y pares, `ubicaciones_de_la_plantilla`, versión) |
| `services/postventa-api/tests/test_f071_dominio_importacion.py` | R23, R26–R39, R41 |
| `services/postventa-api/tests/test_f071_casado_con_lista.py` | §5.5: lo movido sigue igual (`normalizacion` lo reexporta) y `casar_con_lista` |
| `services/postventa-api/tests/test_f071_generador.py` | R5–R11, R13–R20, R40 sobre el `.xlsx` generado (abierto con `openpyxl` en el test) |
| `services/postventa-api/tests/test_f071_configuracion.py` | R16, R18, R19, R21 sobre el YAML real y YAML rotos en `tmp_path` |
| `services/postventa-api/tests/test_f071_pipelines.py` | R1, R3, R24, R25, R40, R44 con dobles (orden y número de lecturas, sin equivalencias) |
| `services/postventa-api/tests/test_f071_http.py` | R1–R3, R23–R25 por los handlers con puertos inyectados |
| `services/postventa-api/tests/test_f071_alcance_cerrado.py` | R42, R43, R45 (patrón de `test_f060_alcance_cerrado.py`: base fija y guardas de ficheros intocables) |
| `services/postventa-api/tests/test_f071_documentacion.py` | R46 |

### 3.2 · A modificar

| Ruta | Qué cambia |
|---|---|
| `services/postventa-api/domain/models/plantilla_incidencias.py` | `VERSION_PLANTILLA = 2`, `VERSIONES_SOPORTADAS = {2}`, `VERSION_ANTERIOR = 1`; `ListasCerradas` **sin** `ubicaciones`; nuevos `OpcionOficioSigrid`, `ParSigrid`, `oficios_del_desplegable`, `pares_del_desplegable` (§5.1), `UbicacionesPorUnidad`, `UbicacionesDeLaPlantilla`, `ubicaciones_de_la_plantilla` (§5.2). `opciones_de_oficio` y `opciones_de_proveedor` **se quedan** (las usa la revisión, §6.3) |
| `services/postventa-api/domain/models/importacion.py` | `reconocer_plantilla`: `version_anterior` (R23); `validar_filas` recibe `oficios`, `pares` y `ubicaciones_por_unidad`; `_Fila.tasado` con el casado (R36); la ubicación por unidad (§5.3); oficio y proveedor resueltos por opción (§5.4); textos nuevos; `resolver_oficio_y_proveedor` y `Elegido` **se quedan** (los usa el modelo de la bandeja) |
| `services/postventa-api/domain/models/normalizacion.py` | Solo los imports: lo movido a `casado_con_lista.py` se importa y se reexporta con los mismos nombres; ni una regla cambia (§5.5) |
| `services/postventa-api/domain/models/errores.py` | `version_anterior` en `CODIGOS_FICHERO_NO_ES_PLANTILLA` |
| `services/postventa-api/domain/ports/hoja_calculo.py` | `GeneradorPlantillaPort.generar(catalogo, oficios, pares, ubicaciones, listas, textos, generada_at, filas, importacion_origen)` |
| `services/postventa-api/application/pipelines/plantilla.py` | `generar_plantilla` sin `equivalencias` y con `ubicaciones` (§6.1); `opciones_de_la_obra` **se queda** para la revisión |
| `services/postventa-api/application/pipelines/contexto_importacion.py` | fuera `grupos_oficio`, `grupos_proveedor`, `opciones_oficio`, `opciones_proveedor`; dentro `oficios`, `pares`, `ubicaciones_por_unidad` (fuera del `repr`) |
| `services/postventa-api/application/pipelines/paso_importacion.py` | `paso_catalogo(contexto, catalogo_obra, ubicaciones)`; `paso_validacion` y `paso_excel_errores` con lo nuevo (§6.2) |
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | `_catalogos` sin `lista_ubicaciones`, con la tabla y las listas por unidad; la validación dependiente; etiquetas de oficio y pares (§7.1) |
| `services/postventa-api/infrastructure/documentos/plantilla_yaml.py` | sin `_ubicaciones` ni `ubicaciones_por_revisar`; la clave `ubicaciones` es error (R21); `_ejemplos` sin validar `Ubicación` contra lista (§7.2) |
| `services/postventa-api/config/plantilla_incidencias.yaml` | fuera la sección `ubicaciones` y su cabecera; mensajes de `Ubicación`, `Oficio` y `Proveedor`; un párrafo de instrucciones; ejemplos (§7.3) |
| `services/postventa-api/interface_adapters/api/plantilla.py` | sin `equivalencias`; compone `ubicaciones=` (por defecto `construir_fuente_de_ubicaciones(obtener_ajustes())` de `interface_adapters/api/revision.py`, la misma que usa la importación desde F-060) |
| `services/postventa-api/interface_adapters/api/importar.py` | sin `equivalencias` en la importación; la fuente de ubicaciones construida **solo** si el fichero se reconoció y no estaba importado (R24) |
| `services/postventa-api/function_app.py` | solo si pasa `equivalencias=` a los dos handlers (hoy no; se comprueba) y el docstring de la ruta de importación (`version_anterior`) |
| Tests de F-036, F-056 y F-060 que construyen `ListasCerradas(ubicaciones=…)`, llaman a `generar`/`validar_filas`/los pasos con la firma vieja, fijan `lista_ubicaciones`, la versión 1, la lista del YAML o los grupos en la plantilla (`tests/utiles_plantilla.py`, `tests/utiles_revision.py`, `test_f036_plantilla_dominio.py`, `test_f036_importacion_dominio.py`, `test_f036_excel_generador.py`, `test_f036_excel_lector.py`, `test_f036_configuracion_plantilla.py`, `test_f036_pipeline_importacion.py`, `test_f036_plantilla_http.py`, `test_f036_importar_http.py`, `test_f036_arquitectura.py`, `test_f036_documentacion.py`, `test_f060_*` que importen de `normalizacion`, y los que salgan) | cada aserción que cambie se **cita** en `progress/impl_F-071.md` con el R de F-071 que la sustituye; ninguna se borra sin sustituta salvo las de la lista del YAML (R21), las de agrupar en la plantilla (R12) y las de la migración (R45) |
| `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md` | R46 (§12) |
| `C:\Users\pgris\PycharmProjects\azure-apps\postventa_incidencias.md` | R46, **del líder al desplegar** |

### 3.3 · A retirar (D-6, R45)

`services/postventa-api/scripts/migrar_excel_f036.py`,
`scripts/migracion_f036.py`, `scripts/migracion_f036_correcciones.yaml`,
`tests/test_f036_migracion.py`, `tests/test_f036_migracion_contenido.py`, y
las menciones que los exijan en otros tests. `scripts/medir_catalogos_f036.py`
y `scripts/contar_elementos_xml_f036.py` **se quedan**.

### 3.4 · Que NO se tocan (R43)

- La revisión: `domain/models/revision.py`, `application/pipelines/revision.py`
  (se **importa** `fuente_de_ubicaciones` desde el borde, no se mueve),
  `interface_adapters/api/revision.py` (se importa
  `construir_fuente_de_ubicaciones`), `domain/ports/revision.py`.
- El volcado: `domain/models/volcado.py`, `situacion_volcado.py`,
  `application/pipelines/volcado*.py`, `infrastructure/sigrid/volcado.py`.
- Sigrid: `infrastructure/sigrid/**` entero (las tres consultas, sin una
  letra cambiada).
- Equivalencias: `domain/models/equivalencias.py`,
  `application/pipelines/equivalencias.py`, `interface_adapters/api/equivalencias.py`,
  `domain/ports/equivalencias.py`, la tabla y `oficios.html`.
- Persistencia: `infrastructure/persistencia/**` y el DDL (`sql/`).
- `infrastructure/documentos/lector_aislado.py`, `ejecutor_aislado.py` y la
  parte lectora de `excel_openpyxl.py` (no lee validaciones ni `_catalogos`).
- `services/postventa-front/**`.

## 4 · El desplegable dependiente (de F-058 §4)

### 4.1 · Opciones

| | (a) Dependiente con nombres e `INDIRECT` | (b) Pares «Unidad · Ubicación» | (c) Unión de la obra y validar al importar |
|---|---|---|---|
| Qué ve quien rellena | Solo las de su unidad (31–37 en la 0677) | 500+ entradas, con la unidad repetida | 58 en la 0677; puede elegir una de otra unidad |
| Cumple la petición | **Sí** | Sí, pero duplica `Unidad` y puede contradecirla | **No**: es lo que pasa hoy con «Escalera» |
| Contrato | igual cabecera; cambia `_catalogos` y una validación | cambia el significado de una columna | igual |
| Riesgo | que `INDIRECT` no funcione igual en Excel web | usabilidad | ninguno técnico |

**Recomendación (D-1): (a)**, variante a1 (`INDIRECT`), confirmada antes de
escribir código por la prueba manual del Bloque 0 con los **prototipos que
F-058 ya generó** (`C:\Users\pgris\Downloads\f058_prototipos\prototipo_f058_a1.xlsx`
y `_a2.xlsx`, datos ficticios, siguen en disco) en Excel de escritorio y Excel
web (Q-7 de F-058). Si a1 falla y a2 (`OFFSET`) vale, a2; si fallan las dos,
**parar** y volver al humano con (c). Sea cual sea, **manda la importación**
(§5.3): pegar se salta la validación de Excel. **El humano hará la prueba
antes del Bloque 1** (Q-1, 2026-11-05); D-1 queda pendiente de su resultado.

### 4.2 · La forma recomendada (a1)

En `_catalogos`, a la derecha de las cinco listas fijas (`lista_unidades`,
`lista_oficios`, `lista_proveedores`, `lista_urgencias`, `lista_listados`) y
con una columna en blanco de separación:

- **Una tabla de dos columnas** con nombre `tabla_ubicaciones_de_unidad`: la
  etiqueta de cada unidad (la de `etiquetas_de_unidades`) y el **nombre** del
  rango de su lista (`ubicaciones_<k>` o `ubicaciones_ninguna`).
- **Una celda vacía** con nombre `ubicaciones_ninguna`.
- **Una columna por lista distinta** (`ubicaciones_<k>`, `k` = 1, 2… en el
  orden de §5.2), con su nombre en la fila 1 y las ubicaciones desde la 2.

La validación de `Ubicación`, una sola para `B2:B1001`, tipo lista,
`allowBlank`, estilo «detener»:

```
INDIRECT(IFERROR(VLOOKUP($A2,tabla_ubicaciones_de_unidad,2,FALSE),"ubicaciones_ninguna"))
```

(89 caracteres, medidos en T0 de F-058; Excel en español lo enseña como
`INDIRECTO(SI.ERROR(BUSCARV(…)))`.) Unidad vacía o desconocida → `IFERROR` →
`ubicaciones_ninguna` → nada que elegir.

**Riesgo anotado en T0 de F-058**: Excel puede **aceptar cualquier texto** si
el origen de la lista es una celda vacía y `allowBlank` está marcado. Lo miden
los puntos 3 y 4 de la prueba; si pasa, se acepta (la importación lo rechaza
con R29–R31) o se cambia `ubicaciones_ninguna` por una celda con un texto
imposible de elegir («—»), a decidir con el resultado (Q-1).

### 4.3 · La variante de reserva (a2)

```
OFFSET(inicio_ubicaciones,0,IFERROR(VLOOKUP($A2,tabla_ubicaciones_de_unidad,2,FALSE),0),IFERROR(VLOOKUP($A2,tabla_ubicaciones_de_unidad,3,FALSE),1),1)
```

(150 caracteres; tabla de tres columnas: etiqueta, columna relativa, número de
ubicaciones; la columna 0 vacía para «ninguna».)

### 4.4 · La prueba (Bloque 0, MANUAL)

Los nueve puntos de F-058 §4.4 en Excel de escritorio y Excel web (OneDrive
**personal**, nunca el SharePoint de Posventa), con la tabla de
`progress/impl_F-058.md` («T1 · Guía para el humano»), copiada a
`progress/impl_F-071.md` y rellenada allí.

### 4.5 · Lo que el desplegable no hace

- **No borra la ubicación al cambiar la unidad** (sin macros). La importación
  la rechaza si ya no es de la unidad (R29) y el mensaje de entrada lo avisa.
- **No marca en rojo** una ubicación que no casa con su unidad (D-10).
- **El proveedor no depende del oficio** (D-19): cada par ya lleva su oficio
  en la etiqueta y la importación comprueba que casen (R34).

## 5 · Dominio

### 5.1 · Oficios y pares, uno por código (`plantilla_incidencias.py`)

```python
@dataclass(frozen=True)
class OpcionOficioSigrid:
    etiqueta: str          # "<nombre> (<código>)" o "<código>"
    codigo: str            # auxofc.cod de obrofc de la obra
    nombre: str | None     # auxofc.res recortado: lo que se guarda (R32)

@dataclass(frozen=True)
class ParSigrid:
    etiqueta: str          # "<etiqueta oficio> · <nombre> (<código>)"
    oficio: OpcionOficioSigrid
    proveedor_codigo: str
    proveedor_nombre: str | None

def oficios_del_desplegable(catalogo: CatalogoObra) -> tuple[OpcionOficioSigrid, ...]: ...
def pares_del_desplegable(
    catalogo: CatalogoObra, oficios: tuple[OpcionOficioSigrid, ...]
) -> tuple[ParSigrid, ...]: ...
```

- `oficios_del_desplegable`: un código por entrada (`{o.codigo for o in
  catalogo.oficios}`), ordenados por código; el nombre es el primero no vacío
  de ese código recortado. **Sin grupos**: no recibe `GruposVigentes` (R12).
- `pares_del_desplegable`: por cada pareja distinta `(oficio_codigo,
  proveedor_codigo)` de `catalogo.proveedores` con proveedor y con un oficio
  del desplegable; el nombre del proveedor, el primero no vacío; orden por la
  posición del oficio y luego por `(plegar(nombre), código)` (R14).
- Las dos llaman a `_exigir_distintas` (R15).
- **Por qué el código siempre en la etiqueta** (D-11, D-12): (1) dos oficios
  de Sigrid casi iguales («Carpinteria de madera» y «Carpintería de madera»)
  se ven los dos y se distinguen; (2) la etiqueta de una opción **no cambia**
  si otro oficio con el mismo nombre entra en la obra entre la descarga y la
  importación (con el código «solo si choca», cambiaría y la fila volvería con
  error); (3) es lo que enseña Posventa en Sigrid.

### 5.2 · Las listas de ubicaciones (`plantilla_incidencias.py`, de F-058 §5.1)

```python
UbicacionesPorUnidad = Mapping[str, tuple[str, ...]]  # unidad_codigo → ubicaciones

@dataclass(frozen=True)
class UbicacionesDeLaPlantilla:
    listas: tuple[tuple[str, ...], ...]       # distintas y no vacías, en orden
    lista_de_unidad: Mapping[str, int | None]  # unidad_codigo → índice, o None
    def union(self) -> tuple[str, ...]: ...

def ubicaciones_de_la_plantilla(
    unidades: Iterable[UnidadPosventa], por_unidad: UbicacionesPorUnidad
) -> UbicacionesDeLaPlantilla: ...
```

Unidades ordenadas por código; índice por orden de primera aparición de cada
tupla no vacía distinta; tupla vacía o sin entrada → `None`; igualdad
**exacta** de tuplas (D-2); `ValueError` sin el texto si una ubicación viene
vacía, con blancos en los extremos o de más de `MAX_UBICACION`; una entrada de
una unidad ajena se ignora; `union()` sin repetidos exactos, en orden.

### 5.3 · La ubicación al importar (`importacion.py`, de F-058 §5.2)

Tras resolver la unidad, en el orden de columnas (R39):

1. Vacía → `None` (R26). Fórmula, fecha/booleano o número → errores de
   siempre (R38).
2. Unidad válida → `lista = ubicaciones_por_unidad.get(codigo, ())`:
   vacía → `UNIDAD_SIN_UBICACIONES` (R30); `ubicacion_de_sigrid(valor,
   lista)` `EXACTA` → el valor (R27); `NORMALIZABLE` → el texto de Sigrid y
   `aviso_ubicacion_ajustada(texto)` (R28); `AMBIGUA` o `SIN_COINCIDENCIA` →
   `UBICACION_FUERA_DE_LA_UNIDAD` (R29).
3. Unidad ausente o inválida → lo mismo contra `union()`, sin guardar nada;
   no casa → `UBICACION_FUERA_DE_LA_OBRA` (R31).

### 5.4 · Oficio y proveedor al importar (`importacion.py`)

```python
def validar_filas(filas, *, catalogo, oficios: tuple[OpcionOficioSigrid, ...],
                  pares: tuple[ParSigrid, ...], listas: ListasCerradas,
                  ubicaciones_por_unidad: UbicacionesPorUnidad) -> ...
```

- `Oficio` casa (R36) con una opción → `Elegido(etiqueta=<nombre de Sigrid o
  código>, codigo=opcion.codigo, ambiguo=False)` (R32). La `etiqueta` de
  `Elegido` es lo que acaba en `oficio_nombre` de la bandeja
  (`sentencias_bandeja._columnas_de`) y el front la pinta como «nombre
  (código)» (`js/importacion.js`, `conCodigo`): por eso va el **nombre**, no
  la etiqueta del desplegable, o saldría «Nombre (0039) (0039)».
- `Proveedor` casa con un par → oficio del par y proveedor del par, los dos
  con código y sin ambigüedad (R33); con `Oficio` elegido y distinto del del
  par → `PROVEEDOR_DE_OTRO_OFICIO` (R34).
- No hay rama ambigua: R35 se fija con un test que recorre todas las
  combinaciones de una obra ficticia con oficios de nombre repetido y
  proveedores en varios oficios.
- Si la etiqueta no casa con ninguna opción **de ahora** (R37):
  `ya_no_esta_en_sigrid(columna)` = «ese valor no está en Sigrid para esta
  obra (puede que haya cambiado desde que descargaste la plantilla): elígelo
  del desplegable de este fichero, que trae las listas de hoy».

### 5.5 · El casado, en una hoja del grafo (`casado_con_lista.py`)

`importacion.py` no puede importar `normalizacion.py`: esta importa
`revision.py`, que importa `importacion.py` (ciclo). Por eso
`Coincidencia`, `UbicacionDeSigrid`, `clave_de_ubicacion` y
`ubicacion_de_sigrid` se **mueven sin cambiar una letra** a
`domain/models/casado_con_lista.py`, que no importa nada del dominio, y
`normalizacion.py` los importa y los reexporta con el mismo nombre (sus tests
y sus usuarios no cambian; un test lo fija). Se añade:

```python
def casar_con_lista(valor: str, opciones: Iterable[str]) -> str | None:
    """La opción exacta, o la ÚNICA con la misma clave (`clave_de_ubicacion`), o None."""
```

que `_Fila.tasado` usa para `Unidad`, `Oficio`, `Proveedor`, `Urgencia` y
`Listado` (R36), con el aviso `aviso_valor_tomado(columna, opcion)` cuando no
es exacta. Es **la misma regla** de F-060 (D-3), no una segunda.

### 5.6 · Textos nuevos (constantes de `importacion.py`)

Lenguaje llano; sin el valor tecleado ni el nombre de la unidad:

- `UBICACION_FUERA_DE_LA_UNIDAD`: «esa ubicación no es de la unidad de esta
  fila: elígela del desplegable, que enseña solo las de su unidad (si has
  cambiado la unidad, vuelve a elegir la ubicación); si el sitio no está, deja
  la ubicación en blanco y explícalo en «Detalle»»
- `UNIDAD_SIN_UBICACIONES`: «esta unidad no tiene ubicaciones en Sigrid: deja
  la ubicación en blanco y explica el sitio en «Detalle»»
- `UBICACION_FUERA_DE_LA_OBRA`: «esa ubicación no es de ninguna unidad de la
  obra: elige primero la unidad y luego la ubicación del desplegable»
- `aviso_ubicacion_ajustada(texto)`: «la ubicación se ha ajustado al texto de
  Sigrid: «<texto>»»
- `aviso_valor_tomado(columna, opcion)`: «<columna>: se ha tomado «<opción>»»
- `ya_no_esta_en_sigrid(columna)` (§5.4)
- `FicheroNoEsPlantilla("version_anterior", …)` (R23)

## 6 · Aplicación

### 6.1 · `generar_plantilla` (`plantilla.py`)

```python
FuenteUbicacionesValidas = Callable[[CatalogoObra], UbicacionesPorUnidad]

def generar_plantilla(codigo_obra, *, catalogo_obra, ubicaciones: FuenteUbicacionesValidas,
                      generador, listas, textos, ahora) -> tuple[str, bytes]:
```

`normalizar_codigo_obra` → `leer_catalogo` → `ubicaciones(catalogo)` (una vez;
al techo o con fallo sube su error, R3) → `oficios_del_desplegable` →
`pares_del_desplegable` → `ubicaciones_de_la_plantilla` → `generador.generar`.
Log: obra, unidades, oficios, pares, `listas_ubicaciones`,
`unidades_sin_ubicaciones`, bytes (R44).

### 6.2 · La importación (`paso_importacion.py`, `contexto_importacion.py`)

- `paso_reconocimiento` no cambia: `reconocer_plantilla` ya rechaza la v1
  (R23) antes de Sigrid.
- `paso_catalogo(contexto, catalogo_obra, ubicaciones)`: `leer_catalogo` →
  `ubicaciones(catalogo)` → `oficios`, `pares` en el contexto. Con
  `ya_importado`, nada (R24).
- `paso_validacion(contexto, listas)`: `validar_filas` con lo nuevo.
- `paso_excel_errores`: `ubicaciones_de_la_plantilla(catalogo.unidades,
  contexto.ubicaciones_por_unidad)` y el mismo generador (R40).
- `paso_registro` no cambia (`plantilla_version` guarda 2).
- La normalización de F-060 tras importar (`interface_adapters/api/importar.py`)
  no cambia; con F-071 encontrará cero normalizables en lo recién importado,
  porque ya entra con el texto de Sigrid.

### 6.3 · Por qué un alias y no `FuenteDeUbicaciones` de F-056

`application/pipelines/revision.py` importa `opciones_de_la_obra` de
`plantilla.py`; si `plantilla.py` importara de `revision.py` habría ciclo. Por
eso `plantilla.py` declara su alias —el **mismo tipo**— y el borde pasa la
misma fuente de producción (`construir_fuente_de_ubicaciones` de
`interface_adapters/api/revision.py`, que ya usa la importación desde F-060).
`opciones_de_la_obra` se queda en `plantilla.py` sin cambios: la usa la
revisión para enseñar el grupo de las filas ya importadas como ambiguas.

## 7 · Infraestructura

### 7.1 · El generador (`excel_openpyxl.py`)

- `LISTAS` pierde `"Ubicación"`. `_catalogos` escribe las cinco listas fijas
  y, a la derecha, la tabla, `ubicaciones_ninguna` y las listas (todo con
  `_texto`, R9).
- `_validacion` trata `Ubicación` aparte: siempre lista, con la fórmula de
  §4.2 (o §4.3), `allow_blank=True`, estilo «detener», mensajes del YAML.
  Nunca la rama «lista vacía → `textLength = 0`» para `Ubicación`.
- `Oficio` y `Proveedor` escriben `o.etiqueta` de las opciones nuevas.
- Nombres de rango fijos y válidos (`ubicaciones_1` no es referencia de
  celda); un test lo fija.
- Tamaño: R20 se mide en un test real (generar y leer con
  `LectorPlantillaOpenpyxl`); en la 0677, ~160 celdas más.
- **`Listado`, preparado para F-072 (D-21).** El generador no sabe de dónde
  sale la lista de `Listado`: la recibe como una lista de opciones más (como
  `Urgencia`) y la escribe en su rango `lista_listados`, igual que las demás.
  F-072 solo cambiará quién construye esa lista (de YAML a `auxtrcp`) sin
  tocar la hoja, la cabecera ni la validación. Nada más se diseña aquí.

### 7.2 · `plantilla_yaml.py`

Fuera `_ubicaciones`, `ubicaciones_por_revisar` y el campo; la clave
`ubicaciones` en la raíz → `ConfiguracionPlantillaInvalida` («`ubicaciones`:
la lista de ubicaciones ya no se configura aquí; sale de Sigrid, por unidad
(F-071)»). `_ejemplos` ya no comprueba `Ubicación` contra lista; sigue con
`Urgencia` y `Listado`.

### 7.3 · `plantilla_incidencias.yaml`, los textos

- Cabecera: fuera el párrafo UBICACIONES; una línea: «Las ubicaciones, los
  oficios y los proveedores no están aquí: salen de Sigrid al descargar la
  plantilla (F-071). Urgencias y listados sí, porque Sigrid no tiene catálogo
  de ellos que la bandeja use.»
- `mensajes.Ubicación.entrada` (≤ 255): «Elige primero la unidad: aquí salen
  solo las ubicaciones de esa unidad en Sigrid. Si cambias la unidad, vuelve a
  elegir la ubicación. Si el sitio no está, déjala en blanco y explícalo en
  «Detalle».»
- `mensajes.Ubicación.error`: «Ese valor no es una ubicación de la unidad de
  esta fila. Elige primero la unidad y luego la ubicación del desplegable.»
- `mensajes.Oficio.entrada`: «Opcional. Elige del desplegable el oficio que
  tiene que arreglarlo; cada uno lleva su código de Sigrid. Si no lo sabes,
  déjalo en blanco.»
- Instrucciones: un párrafo nuevo tras «Todo lo que tiene desplegable…»: «Las
  listas salen de Sigrid el día que descargas la plantilla. La de «Ubicación»
  depende de la unidad de la fila: elige primero la unidad. Si cambias la
  unidad, vuelve a elegir la ubicación. Si el sitio no está en la lista, deja
  la ubicación en blanco y explícalo en «Detalle».»
- Ejemplos: `Ubicación: "Estancia (elígela de la lista de su unidad)"`;
  ninguno con «General (toda la unidad)».

## 8 · Urgencia y listado: qué hay en Sigrid (D-15, D-16)

- **Urgencia.** En Sigrid es `rcp.texurg`, **texto libre** de 32 caracteres
  (`sigrid_tablas.md`, tabla `rcp`), sin tabla auxiliar. `sigrid-api` §8.9 no
  lo admite y el volcado no la manda (D-10 de F-059). No hay «lo que hay en
  Sigrid» que ofrecer: se queda la lista del YAML **de momento** (Q-2,
  2026-11-05). El humano pasará más adelante una **lista interna de
  prioridades** (no de Sigrid) que la sustituirá: fuera de alcance, sin
  diseñar aquí.
- **Listado.** En Sigrid el equivalente es el **tipo de reclamación**
  (`rcp.trcpide` → `auxtrcp`; `0002` «PRIMER LISTADO POSTVENTA»). Hoy el
  `listado` de la bandeja **no llega a Sigrid**: el volcado manda siempre
  `0002` (Q-1 de F-059). Ofrecer `auxtrcp` en la plantilla sin que la bandeja
  lo guarde por código y el volcado lo mande sería enseñar algo que no se usa.
  Hacerlo de punta a punta toca DDL (`CHECK (listado IN …)` en
  `13_bandeja_incidencias.sql` y `15_revisiones_bandeja.sql`), la revisión, la
  página de la bandeja y el volcado de F-040: por eso va en **ficha aparte,
  F-072** (Q-3, 2026-11-05: `auxtrcp` de punta a punta; en blanco, `0002`;
  orden F-071 → F-072 → retomar F-040). F-071 deja `Listado` en el YAML con el
  generador preparado (D-21, §7.1).

## 9 · Compatibilidad

- **Plantillas v1 ya repartidas** (D-4, decisión del humano en F-058): se
  rechazan enteras con `version_anterior` (R23). Aceptarlas no serviría: sus
  etiquetas de oficio son de grupo («Pintura») y las de la v2 llevan código
  («Pintura (0039)»), así que casi toda fila con oficio volvería con error.
  Quien tenga una v1 rellenada descarga la v2 y copia sus filas (Q-4).
- **Lo ya importado** no se toca: las filas con `oficio_ambiguo` o con una
  ubicación fuera de lista se resuelven en la bandeja como hoy (R43, Q-12).
- **Reimportar** un fichero ya importado no duplica (atajo por `sha256`; una
  v1 ya importada responde `ya_importado` antes de reconocer).

## 10 · SQL

Ninguno. Ningún DDL, ninguna consulta nueva (R42).

## 11 · Logs y datos (R44)

Ni `prmtpl.ubica`, ni una ubicación, ni un nombre de unidad, oficio o
proveedor en un log. Los avisos con el texto de Sigrid van en la respuesta y
en el Excel, nunca al log. Tests y documentos con datos ficticios.

## 12 · Documentación (R46)

- `docs/ARCHITECTURE.md`: «La plantilla» (todos los desplegables de Sigrid
  menos urgencia y listado; ubicación dependiente; oficio y proveedor por
  código); «La importación» (la v1 se rechaza; ubicación por unidad; casado de
  F-060 en las columnas tasadas; ya no hay `oficio_ambiguo` de entrada); «La
  agrupación de oficios casi duplicados» (enmienda: ya no se aplica a la
  plantilla; sirve a la revisión de lo ya importado); «Dónde vive cada pieza»
  (`casado_con_lista.py`; la migración retirada); «Lo que no hace la revisión»
  (la lista del YAML ya no existe).
- `docs/INTEGRACION.md` §1 (la lectura de ubicaciones también al descargar
  la plantilla; la plantilla ya no lee PostgreSQL) y los párrafos de la lista
  cerrada.
- `azure-apps/postventa_incidencias.md`: lo mismo, **el líder al desplegar**.

## 13 · Decisiones

| Id | Decisión | Opciones | Elegida (humano, 2026-11-05) |
|---|---|---|---|
| **D-1** | Cómo ofrecer la ubicación por fila | (a) dependiente; (b) pares; (c) unión + validar al importar | **(a) a1**, con la prueba del Bloque 0 sobre los prototipos de F-058; a2 de reserva; si fallan, parar y volver con (c). **Pendiente del resultado de T0** |
| **D-2** | Cómo se agrupan las listas | por tipología (pidiendo `obrtplide`) o por contenido | **Por contenido**: no cambia la consulta de F-056 |
| **D-3** | Ubicación que solo difiere en mayúsculas | normalizar con F-060 y avisar; exacta | **Normalizar** con `ubicacion_de_sigrid` (F-060 ya está en `dev`) |
| **D-4** | Plantillas v1 | rechazar; importar con reglas nuevas | **Rechazar** con `version_anterior` (decisión del humano en F-058, y la v1 no casaría por las etiquetas de oficio, §9) |
| **D-5** | «General» y «Otra» | quitarlas; mantenerlas | **Quitarlas**: no son de Sigrid; la revisión no las aprueba ni el volcado las puede mandar |
| **D-6** | Script de migración de F-036 | retirarlo; adaptarlo | **Retirarlo**: cumplió y usa la lista y los grupos que desaparecen |
| **D-7** | Versión | 2; 1 | **2** |
| **D-8** | Ubicación con la unidad mal | no validar; contra la unión | **Contra la unión** |
| **D-9** | Ubicación repetida con otras mayúsculas en una lista de Sigrid | ofrecer las dos; plegar | **Las dos** (es el dato); el casado no elige entre dos |
| **D-10** | Marcar en rojo la ubicación que ya no casa | sí; no | **No** en esta ficha |
| **D-11** | Etiqueta del oficio | nombre; nombre + código solo si choca; **siempre** nombre + código | **Siempre `<nombre> (<código>)`** (§5.1) |
| **D-12** | Proveedor | par por grupo de oficio (hoy); par por fila de `obrofc` con código | **Par por (oficio, proveedor), con los dos códigos** |
| **D-13** | Qué se guarda como nombre del oficio y del proveedor | la etiqueta del desplegable; el nombre de Sigrid | **El nombre de Sigrid** (el front ya añade el código) |
| **D-14** | Equivalencias de oficio (R86, R92 de F-036) | seguir agrupando en la plantilla; no agrupar | **No agrupar en la plantilla ni en la importación**; la tabla, `oficios.html`, sus rutas y la revisión no se tocan (Q-6) |
| **D-15** | Urgencia | YAML; inventar catálogo | **YAML de momento** (no hay catálogo en Sigrid, §8); la sustituirá una lista interna del humano, fuera de alcance |
| **D-16** | Listado / tipo de reclamación | YAML ahora y ficha aparte de punta a punta; dentro de F-071 | **YAML ahora, ficha aparte F-072** (Q-3) |
| **D-17** | Valores tecleados con otra mayúscula en las demás columnas tasadas | exacto (decisión 7 de F-036); casado de F-060 | **Casado de F-060** con aviso (R36): la importación no rechaza lo que Excel dio por bueno |
| **D-18** | Filas ya importadas ambiguas | arreglarlas en esta ficha; dejarlas a la bandeja | **A la bandeja**, como hoy |
| **D-19** | Proveedor dependiente del oficio | sí (otro `INDIRECT`); no | **No**: el par lleva su oficio y la importación comprueba (R34) |
| **D-20** | F-058 | mergear; absorberla | **Absorberla**: F-058 no se implementa; el líder la cierra como absorbida y retira su worktree (Q-11) |
| **D-21** | `Listado` frente a F-072 | dejarlo cableado al YAML; que el generador lo reciba como una lista más | **Una lista más** (§7.1): F-072 cambia el origen sin rehacer la plantilla |

### 13.1 · Respuestas del humano (versión 1, 2026-11-05)

Todas según la recomendación de `progress/spec_F-071.md`, con estos matices:

| Q | Respuesta | Dónde queda |
|---|---|---|
| Q-1 | Sí: el humano hace la prueba manual de los prototipos **antes del Bloque 1** | T0; D-1 pendiente del resultado |
| Q-2 | La urgencia sigue en el YAML **de momento**; la sustituirá una lista **interna** de prioridades que pasará el humano (no viene de Sigrid) | D-15, §8, requirements §4.1; sin diseñar |
| Q-3 | Ficha aparte **F-072** (`auxtrcp` de punta a punta; en blanco = `0002`). Orden F-071 → F-072 → retomar F-040. F-071 deja `Listado` en el YAML con el generador preparado | D-16, D-21, §7.1, §8 |
| Q-4 | Rechazar la v1 | D-4, R23 |
| Q-5 | Etiquetas siempre con código | D-11, D-12 |
| Q-6 | Las equivalencias se quedan sin cambios | D-14 |
| Q-7 | Sí: casado de F-060 (una sola opción salvo mayúsculas, con aviso) en `Unidad`, `Oficio`, `Proveedor`, `Urgencia` y `Listado` | D-17, R36 |
| Q-8 | Ubicación en blanco y explicación en «Detalle» si el sitio no está | R18 |
| Q-9 | Retirar el script de migración de F-036 | D-6, R45 |
| Q-10 | Autorizada la fila de prueba «PRUEBA F-071 - DESCARTAR» en la bandeja de la 0677; la descarta el humano; nada en Sigrid | R47, T16 |
| Q-11 | F-058 absorbida (anotado por el líder en el backlog) | D-20, T17 |
| Q-12 | Lo ya importado se resuelve en la bandeja | D-18 |
| Q-13 | Hecho por el líder: F-040 `blocked` y la rama de F-071 rebasada sobre `dev` `ed935ad` (base fija) | R-6, T0 bis |

## 14 · Riesgos

- **R-1 · `INDIRECT` en Excel web.** Bloque 0 antes del código; salida D-1.
- **R-2 · Otro programa** (Google Sheets, Numbers): el desplegable
  dependiente puede no ir. La importación valida igual. El humano dijo en
  F-058 (Q-4) que se rellena en Excel.
- **R-3 · Comodines en una etiqueta de unidad** (`*`, `?`, `~` en `VLOOKUP`):
  solo afecta a la ayuda; la importación valida por unidad. Si pasa, se
  escapan con `SUBSTITUTE` en la fórmula (cabe en 255).
- **R-4 · Una lectura más** por plantilla e importación (0,1–0,3 s en F-056) y
  una menos de PostgreSQL en la plantilla: dentro de los 45 s.
- **R-5 · Muchos tests de F-036 cambian** (versión, lista, grupos, firma).
  Cada uno se cita con su sustituto (§3.2); el reviewer lo comprueba.
- **R-6 · Rama desde F-040 (resuelto).** La rama salió de
  `feature/F-040-volcado-sigrid`; el 2026-11-05 el líder la rebasó sobre
  `dev` `ed935ad` (base fija) y aparcó F-040 (`blocked`), así que el merge a
  `dev` no arrastra F-040 a medias (Q-13).
- **R-7 · Excel acepta lo tecleado con la lista vacía** (§4.2): lo mide el
  Bloque 0.
- **R-9 · Los `test_f0NN_alcance_cerrado.py` de F-036, F-056, F-059, F-060 y
  F-065** nombran ficheros que F-071 toca (`importacion.py`,
  `plantilla_incidencias.py`, `normalizacion.py`, `paso_importacion.py`,
  `excel_openpyxl.py`). Sus guardas de F-030 los limitan a su propia rama; el
  implementer lo comprueba en T2 y, si alguno se dispara, lo declara y lo
  para (sin relajarlo) antes de seguir.
- **R-8 · Etiquetas más largas** en `Oficio` y `Proveedor` (hasta ~150
  caracteres un par): el ancho de columna no cambia; se ve cortado en la
  celda, completo en el desplegable. Aceptable.

## 15 · Trazabilidad requisito → test

| R | Test |
|---|---|
| R1, R2, R3 | `test_f071_pipelines.py`, `test_f071_http.py` |
| R4 | `test_f071_generador.py` (sin cambio frente a F-036) |
| R5–R11 | `test_f071_generador.py`; R8 también `test_f071_dominio_opciones.py` |
| R12–R15 | `test_f071_dominio_opciones.py`, `test_f071_generador.py` |
| R16, R18, R19, R21 | `test_f071_configuracion.py`, `test_f071_generador.py` |
| R17, R22 | `test_f071_dominio_opciones.py` |
| R20 | `test_f071_generador.py` (obra grande por el lector real) |
| R23 | `test_f071_dominio_importacion.py`, `test_f071_http.py` |
| R24, R25 | `test_f071_pipelines.py`, `test_f071_http.py` |
| R26–R39, R41 | `test_f071_dominio_importacion.py`; R36 también `test_f071_casado_con_lista.py` |
| R40 | `test_f071_pipelines.py`, `test_f071_generador.py` |
| R42, R43, R45 | `test_f071_alcance_cerrado.py` |
| R44 | `test_f071_pipelines.py` (`caplog`) |
| R46 | `test_f071_documentacion.py` |
| R47 | MANUAL (humano), T16 |
