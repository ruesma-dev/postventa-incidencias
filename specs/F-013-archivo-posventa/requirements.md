<!-- specs/F-013-archivo-posventa/requirements.md -->
# F-013 · Mudar el archivo a la biblioteca de Posventa — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f013_rN_*`, salvo los marcados **MANUAL**, que se
> verifican a mano por el humano y tienen su comando en `tasks.md`.
>
> **Rigor: `critico`**, decidido por el humano el 2026-09-18 (D-R; la ficha
> decía `estandar` y la actualiza el líder). Motivo en `design.md` §0.3: esta feature pasa a escribir en la **biblioteca real de
> negocio** de Posventa, sincronizada por OneDrive en sus equipos, con PDFs que
> llevan el **DNI manuscrito** de clientes, y el fallo típico —el parte en la
> carpeta de otra vivienda u otra obra— **no se ve** desde nuestro lado. Es la
> misma clase de riesgo por la que F-006 se hizo `critico`.
>
> Convención de la spec: lo medido va marcado **[MEDIDO]** con su fuente; lo
> que no se ha podido medir, **[NO MEDIDO]**, y tiene su verificación manual.
> Ni un identificador de sitio, biblioteca, tenant ni suscripción en esta
> carpeta: el destino entra por configuración (F-006 R29).

## 0 · Las decisiones del humano del 2026-09-18 (no se reabren)

| # | Decisión, literal en lo esencial | Dónde se traduce |
|---|---|---|
| **H1** | Destino: el sitio de **Posventa**, biblioteca **«Documentos compartidos»**. Se abandona la biblioteca temporal del sitio de IT | R1, R2; configuración, `design.md` §6 |
| **H2** | Estructura: **la que ya usa Posventa**, `<cod> <OBRA> / PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS / <fichero>`. El nombre del fichero **no cambia** | R3–R16 |
| **H3** | «PARTES FIRMADOS (sistema)» como carpeta base de la estructura propia: con la estructura de Posventa probablemente no aplica. Se dejó abierto y **se cerró el mismo día como D-1**: raíz de la biblioteca | D-1; R17 |
| **H4** | **Lo ya archivado en IT se queda en IT**, sin migración, y se documenta que sigue allí | R24–R26 |

### 0 bis · Las decisiones abiertas, cerradas por el humano el 2026-09-18

Respuesta del humano a `design.md` §9, literal: *«si, pero quiero que tenga
permiso para crear todas las carpetas no solo partes firmados.»* Acepta todas
las recomendaciones **salvo D-4**, que cambia.

| Id | Decisión | Dónde se traduce |
|---|---|---|
| **D-1** | Base = **raíz** de la biblioteca (`SHAREPOINT_CARPETA_BASE=""`) | R17 |
| **D-2** | **F-033 antes** que F-013: dependencia dura del corte | R25, `tasks.md` bloque 5 |
| **D-3** | Orden **F-033 → F-031 → F-013** | `design.md` §8.2 |
| **D-4** | **CAMBIA** respecto a la recomendación: el sistema **puede crear toda la ruta que falte** —`<cod> <OBRA>`, `PARTES INCIDENCIAS`, `<UNIDAD>` y `PARTES FIRMADOS`—, no solo la hoja | R9, R13–R16 enmendados; R34–R40 |
| **D-5** | Cola humana = el 409 con motivo y candidatas; vista de front o mapa, fichas aparte | R19 |
| **D-6** | Regla de casado de la unidad, la propuesta, **condicionada a T2/T3** | R11, `design.md` §4.3 |
| **D-7** | Sigrid caída al archivar → 503, no se sube, no se cae al dato del papel | R41 |
| **D-R** | Rigor `critico` | cabecera |

## Por qué esta feature no es «cambiar tres variables»

F-006 (`design.md` §7) escribió que F-013 sería cambiar `SHAREPOINT_SITE_ID`,
`SHAREPOINT_DRIVE_ID` y `SHAREPOINT_CARPETA_BASE`. Era cierto **para el
destino** y deja de serlo **para la estructura**, por tres hechos:

1. **La carpeta ya no sale de un dato que tengamos.** Hoy es
   `<base>/<cod obra>`. La de Posventa necesita el **nombre** de la obra y el
   de la **unidad**, y ninguno coincide con lo que tenemos:
   - el nombre de la obra en Sigrid (`con.res`) para la `0677` es
     «15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)» **[MEDIDO,
     `maestro.obras` del datamart, build del 2026-09-17]**, no el `<OBRA>`
     corto de una carpeta;
   - la unidad que imprime el parte es «Viviendas Bloque Villa 5»
     **[MEDIDO, `docs/referencia/02_parte_de_trabajo.md`]**, y la carpeta de
     Posventa es **`VILLA 05`** (decisión del humano, memoria de decisiones del
     2026-08-18): cambia el texto y cambian los ceros;
   - y el código de obra **no es único** en Sigrid: `0677` tiene **dos** filas
     en el maestro de obras, y en total hay **922 obras con 846 códigos
     distintos** (134 filas comparten código) **[MEDIDO, `maestro.obras`,
     2026-09-18]**.
2. **Las carpetas de obra y de unidad las crea Posventa a mano**, así que
   cuando no casen no se pueden inventar: una carpeta `0677 15 VIVIENDAS...`
   creada por nosotros al lado de la suya partiría su archivo en dos, y lo
   verían al instante porque la biblioteca está **sincronizada por OneDrive**.
3. **Casar exige listar carpetas**, y `docs/INTEGRACION.md` §3 dice hoy «sin
   listados de carpeta». Esa premisa se enmienda (R12, R29).

Por eso el diseño **resuelve** la carpeta contra lo que ya existe y, si no la
encuentra sin ambigüedad, **no archiva**: el parte espera a una persona.

## Alcance

**Entra**: la estrategia de destino configurable (`por_obra` de F-006 y
`posventa` de F-013); la resolución de las carpetas de obra y de unidad contra
las existentes **y su creación cuando no hay ninguna, ni parecida** (D-4);
la lectura de la ubicación de la reclamación en Sigrid (solo lectura, por
`sigrid-api`); el estado de «destino no resuelto» con su motivo;
el script de solo lectura que resuelve sitio y biblioteca desde la URL y
comprueba permisos; y la documentación.

**No entra**, y cada cosa tiene su dueña:

| Fuera | Por qué | Dónde |
|---|---|---|
| Activar la capa L1 contra el duplicado | Es un defecto propio con su ficha; F-013 **depende** de él | **F-033** (D-2, `design.md` §8.1) |
| Que carpeta y nombre salgan de lo persistido y no del cuerpo | Ficha propia, toca el front | **F-031** (D-3, `design.md` §8.2) |
| Recortar permisos a `Sites.Selected` y conceder el sitio de Posventa | Lo ejecuta el humano en el tenant | **F-018** (se le anota, T-doc) |
| Migrar lo archivado en IT | Decisión H4 | — |
| Pintar la cola de «destino no resuelto» en el front | Es circuito de front | propuesta de ficha nueva (D-5) |

## Vocabulario

| Término | Qué es |
|---|---|
| **Estrategia de destino** | Cómo se compone la carpeta: `por_obra` (F-006: `<base>/<cod obra>`) o `posventa` (F-013). Configuración `SHAREPOINT_ESTRUCTURA` |
| **Carpeta de obra** | La carpeta de primer nivel bajo la base cuyo nombre es `<cod obra>` seguido de un blanco y el nombre de la obra. La crea Posventa o, si no hay ninguna ni parecida, el sistema (R34) |
| **Carpeta de unidad** | La carpeta bajo `<obra>/PARTES INCIDENCIAS/` de una unidad de posventa (`VILLA 05`). La crea Posventa o, si no hay ninguna ni parecida, el sistema (R34) |
| **Candidata que casa** | Carpeta que cumple la regla **estricta** de su nivel (R10, R11, `design.md` §4) |
| **Carpeta parecida** | Carpeta que **no** casa pero cumple la regla **amplia** de su nivel (`design.md` §4.5): el mismo código de obra, el mismo número de unidad o la misma palabra clave del tramo fijo, con otra grafía. Su existencia **impide crear** (R35) |
| **Hoja** | `PARTES FIRMADOS`, la carpeta final dentro de la unidad |
| **Ubicación de la reclamación** | Lo que Sigrid dice de la reclamación: código de la obra y código y nombre de su **unidad de posventa** (`rcp.upvide → upv`, y `upv.obride → obr`), leído por `sigrid-api` |
| **Clave de unidad** | La forma canónica con la que se compara una unidad: mayúsculas, sin tildes, blancos colapsados y **los números comparados como enteros** (`05` = `5`) — ver `design.md` §4.3 |
| **Destino no resuelto** | Resultado del archivado que **no sube nada** porque una carpeta del camino es ambigua, solo hay parecidas o no se puede crear. Lleva motivo y candidatas |

---

## 1 · El destino es configuración

**R1.** El sistema debe leer de configuración la estrategia de destino
(`SHAREPOINT_ESTRUCTURA`, valores `por_obra` y `posventa`) y los nombres
literales de los dos tramos fijos de la estructura de Posventa
(`SHAREPOINT_CARPETA_INCIDENCIAS`, por omisión `PARTES INCIDENCIAS`, y
`SHAREPOINT_CARPETA_FIRMADOS`, por omisión `PARTES FIRMADOS`), si se pueden
crear carpetas (`SHAREPOINT_CREAR_CARPETAS`, por omisión encendido, D-4) y de
qué campo de la unidad de Sigrid sale el nombre de una unidad creada
(`SHAREPOINT_NOMBRE_UNIDAD`, `codigo` o `nombre`, R37). Cambiar de
estrategia o de nombres **no debe tocar** el dominio, la aplicación ni el
pipeline (criterio de aceptación 1 de la ficha).

**R2.** MIENTRAS `SHAREPOINT_ESTRUCTURA` valga `por_obra` —que es el valor por
omisión— y la base no esté vacía (R17), el sistema debe componer la carpeta y
el nombre **exactamente** como hoy (F-006 R1–R12), sin llamar a Sigrid ni listar ninguna carpeta. Los tests
de F-006 siguen en verde sin tocarlos.

**R3.** SI `SHAREPOINT_ESTRUCTURA` trae un valor que no es ninguno de los dos,
o `SHAREPOINT_NOMBRE_UNIDAD` uno que no es `codigo` ni `nombre`,
ENTONCES la construcción del archivador debe fallar con
`ConfiguracionSharePointIncompleta` nombrando la variable y los valores
admitidos, **antes** de pedir ningún token.

## 2 · La ruta con la estructura de Posventa

**R4.** DONDE la estrategia sea `posventa`, el sistema debe archivar el parte
en `<base>/<carpeta de obra>/<INCIDENCIAS>/<carpeta de unidad>/<FIRMADOS>/`,
con `<base>` la de `SHAREPOINT_CARPETA_BASE` (vacía = raíz de la biblioteca,
R17) y los nombres de la carpeta de obra y de unidad **tal y como existen** en
la biblioteca, sin reescribirlos.

**R5.** El nombre del fichero debe seguir siendo
`<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`, compuesto por
`nombre_de_archivo` de `domain/models/nombrado.py` **sin cambios**, en las
dos estrategias (H2).

## 3 · De dónde salen la obra y la unidad

**R6.** DONDE la estrategia sea `posventa`, CUANDO se archive un parte, el
sistema debe leer de Sigrid, por `sigrid-api` y **solo con lectura**, la
ubicación de la reclamación cuyo código es el número de incidencia del parte
(en forma de ERP, `RS26.08/0123`): código y **nombre** de la obra, y código y
nombre de la unidad de posventa. Una sola consulta parametrizada, acotada por el tipo de
concepto de la reclamación.

**R7.** SI la consulta de ubicación devuelve **cero** filas, ENTONCES el
sistema no debe archivar y debe responder «destino no resuelto» con motivo
`reclamacion_no_localizada`. SI devuelve **más de una**, lo mismo con motivo
`reclamacion_ambigua`. SI devuelve una pero **sin unidad de posventa** o sin
obra (la reclamación no cuelga de ninguna `upv`, o la `upv` de ninguna obra),
motivo `reclamacion_sin_unidad`.

**R8.** SI el código de obra de la ubicación, normalizado con
`normalizar_codigo`, **no es igual** al código de obra del parte, ENTONCES el
sistema no debe archivar y debe responder «destino no resuelto» con motivo
`obra_no_coincide`. Es la defensa contra el PDF con DNI en la carpeta de otra
obra: dos fuentes independientes tienen que decir la misma obra.

**R9.** El sistema no debe usar el campo `unidad` extraído del papel ni para
casar ni para componer ninguna carpeta. Los nombres de Sigrid sirven para
**casar** con las existentes (R10–R14) y, **solo cuando no hay ninguna ni
parecida**, para **componer** la carpeta que se crea (R36, R37).

> **Enmienda del 2026-09-18 · D-4.** R9 decía, literal: *«El sistema no debe
> usar el nombre de la obra de Sigrid ni el campo `unidad` extraído del papel
> para **componer** ninguna carpeta: solo para **casar** con las existentes
> (R10–R14).»* Lo invalidó la decisión del humano del mismo día de que el
> sistema pueda crear toda la ruta: crear exige un nombre, y el único origen
> que no es lectura de IA es Sigrid.

## 4 · Casar con las carpetas que existen

**R10.** Para localizar la carpeta de obra, el sistema debe listar las
**carpetas** (no los ficheros) hijas de `<base>` y quedarse con las que cumplen
que su nombre, recortado, **empieza por el código de obra seguido de un
blanco** (o es exactamente el código). La comparación del código es literal y
conserva los ceros: `0677` no casa con `677 ...` ni con `06770 ...`.

**R11.** Para localizar la carpeta de unidad, el sistema debe listar las
carpetas hijas de `<carpeta de obra>/<INCIDENCIAS>` y quedarse con las que
cumplen la regla de casado de la **clave de unidad** (`design.md` §4.3) contra
el código **o** el nombre de la unidad de Sigrid.

**R12.** Los listados deben pedir **solo carpetas** y deben seguir la
paginación del proveedor hasta el final: una biblioteca con cientos de obras
no puede resolver mal porque la obra buscada estuviera en la segunda página.

**R13.** SI hay **más de una** candidata que casa a carpeta de obra, ENTONCES
«destino no resuelto», motivo `obra_ambigua`, con los nombres de las
candidatas en el resultado. (Cero candidatas: R34, R35.)

**R14.** Para cada uno de los otros tres niveles —`<INCIDENCIAS>`, unidad y
`<FIRMADOS>`— SI hay **más de una** que casa, ENTONCES «destino no resuelto»
con motivo `incidencias_ambigua`, `unidad_ambigua` o `firmados_ambigua`, con
las candidatas. (Cero: R34, R35.)

> **Enmienda del 2026-09-18 · D-4.** R13 y R14 decían además, literal: *«SI hay
> **cero** candidatas a carpeta de obra, ENTONCES «destino no resuelto», motivo
> `obra_sin_carpeta`»* y *«SI no existe `<carpeta de obra>/<INCIDENCIAS>`,
> ENTONCES «destino no resuelto», motivo `sin_carpeta_incidencias`. SI hay
> **cero** candidatas a carpeta de unidad, motivo `unidad_sin_carpeta`»*. Con la
> decisión del humano de ese día, «cero» deja de ser por sí solo un destino no
> resuelto: se crea, salvo que haya parecidas (R35). Los motivos de
> ambigüedad se renombran a `<nivel>_ambigua` para que los cuatro niveles
> sigan el mismo patrón.

**R15.** DONDE `SHAREPOINT_CREAR_CARPETAS` esté encendido (por omisión,
**encendido**, D-4), el sistema puede crear cualquiera de los cuatro niveles
que falte —obra, `<INCIDENCIAS>`, unidad, `<FIRMADOS>`—, **de uno en uno,
dentro de un padre que ya existe o que acaba de crear en esa misma
resolución**, y nunca por otro camino: ni `asegurar_carpeta` de F-006 (que
crea tramos a ciegas), ni una ruta completa de una vez.

**R16.** SI un nivel no existe y `SHAREPOINT_CREAR_CARPETAS` está apagado,
ENTONCES «destino no resuelto», motivo `sin_carpeta_<nivel>` (`obra`,
`incidencias`, `unidad`, `firmados`), y no se crea nada.

> **Enmienda del 2026-09-18 · D-4.** R15 decía, literal: *«El sistema **no debe
> crear nunca** la carpeta de obra, la de `INCIDENCIAS` ni la de unidad. La
> única carpeta que puede crear es la hoja `<FIRMADOS>` dentro de una carpeta
> de unidad **ya existente**, y solo DONDE `SHAREPOINT_CREAR_HOJA` esté
> encendido»*; y R16, *«SI la hoja no existe y `SHAREPOINT_CREAR_HOJA` está
> apagado, ENTONCES «destino no resuelto», motivo `sin_carpeta_firmados`»*.
> **Qué la invalidó**: la respuesta del humano del 2026-09-18, *«quiero que
> tenga permiso para crear todas las carpetas no solo partes firmados»*. La
> variable pasa de `SHAREPOINT_CREAR_HOJA` a `SHAREPOINT_CREAR_CARPETAS`. Lo
> que **no** cambia: crear es la salida de «no hay ninguna», nunca la de «hay
> alguna parecida» (R35).

## 5 · La carpeta base

**R17.** El sistema debe admitir una `SHAREPOINT_CARPETA_BASE` **vacía** como
«raíz de la biblioteca», sin producir rutas con barra inicial ni tramos vacíos
(`/0677 ...` o `//`). En la estrategia `por_obra`, en cambio, una base vacía
pasa a ser un **error de configuración** (`ConfiguracionSharePointIncompleta`,
como R3): hoy produce la ruta `/0677`, y dejaría las carpetas por código de
F-006 sueltas en la raíz de la biblioteca de Posventa, mezcladas con las suyas.

## 5 bis · Crear carpetas (D-4, 2026-09-18)

**R34.** CUANDO en un nivel hay **cero** candidatas que casan **y cero
parecidas**, el sistema debe crear la carpeta de ese nivel con el nombre de
R36/R37 y seguir resolviendo por debajo de ella (donde, por construcción, no
hay nada y se crea el resto del camino). Es la **única** situación en la que
se crea.

**R35.** SI en un nivel hay **cero** candidatas que casan pero **al menos una
parecida** (`design.md` §4.5: otra grafía del mismo código de obra, del mismo
número de unidad o de la misma palabra clave del tramo fijo), ENTONCES el
sistema **no debe crear** y debe responder «destino no resuelto» con motivo
`<nivel>_parecida` y las parecidas como candidatas. Crear al lado de una
carpeta que probablemente es la misma produce un duplicado en la biblioteca
real sincronizada por OneDrive; el 409 lo resuelve una persona renombrando la
suya o creando la buena. Tests obligatorios: `0677-MIRASIERRA` impide crear
`0677 ...`; `VILLA 05 - GARCIA` impide crear la unidad 5; `PARTES DE
INCIDENCIAS` impide crear `PARTES INCIDENCIAS`; y `VILLA 07` **no** impide
crear la unidad 5.

**R36.** El nombre de una carpeta de **obra** creada debe ser
`<código de obra> <nombre de la obra en Sigrid>`: el código normalizado (ceros
intactos) y el `con.res` **de esa obra** —la de `upv.obride`, no cualquiera con
el mismo código—, literal, recortado y con los blancos interiores colapsados a
uno. Ejemplo medido: `0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)`.
**Condicionado a T2** (`design.md` §4.6): si T2 muestra que Posventa usa otra
forma **derivable de forma determinista** de Sigrid, se enmienda con test antes
de implementar; si no es derivable, se queda esta.

**R37.** El nombre de una carpeta de **unidad** creada debe salir de la unidad
de posventa de Sigrid, del campo que fije `SHAREPOINT_NOMBRE_UNIDAD`
(`codigo` → `con.cod` de la `upv`; `nombre` → su `con.res`), literal,
recortado y con blancos colapsados. El valor por omisión **se fija en T4 con
T2/T3 delante** (`design.md` §4.6): `codigo` si `upv.cod` tiene ya la forma
corta de Posventa (`VILLA 05`), `nombre` en otro caso. El sistema **no
reformatea**: no rellena ceros ni abrevia, porque un `VILLA 05` fabricado a
partir de «Villa 5» sería una convención que nadie ha escrito. Los dos tramos
fijos se crean con el literal de `SHAREPOINT_CARPETA_INCIDENCIAS` y
`SHAREPOINT_CARPETA_FIRMADOS`.

**R38.** SI el nombre compuesto para crear una carpeta está vacío, lleva algún
carácter que SharePoint no admite (`" * : < > ? / \ |`), empieza o acaba en
blanco o acaba en punto, ENTONCES el sistema no debe sanearlo ni crear nada, y
debe responder «destino no resuelto» con motivo `nombre_carpeta_imposible`
(la misma regla que F-006 R7 aplica al fichero). Todos los nombres que la
resolución vaya a necesitar se componen y se comprueban **antes de crear la
primera carpeta**: un nombre de unidad imposible no puede dejar creada una
carpeta de obra vacía.

**R39.** Una carpeta creada por el sistema debe **casar** consigo misma en el
siguiente archivado: dos partes seguidos de la misma unidad nueva crean las
carpetas **una vez**, y la segunda resolución las encuentra por la regla
estricta sin que ninguna parecida la bloquee. Y dos partes concurrentes que
creen la misma carpeta acaban en **una**: se crea con
`conflictBehavior=fail`, el `409` cuenta como «ya existe» (F-006 R12) y el
nombre es determinista.

**R40.** CUANDO el sistema crea una o más carpetas, la respuesta de
`/api/archivar` debe llevar en `avisos` una línea por carpeta creada con su
ruta, y el log una línea `F-013 carpeta creada: <ruta>`. Quien archiva tiene
que ver que ha aparecido una carpeta nueva en la biblioteca de Posventa.

## 6 · El destino no resuelto

**R18.** CUANDO el destino no se resuelve, el sistema **no debe** pedir la
subida ni crear ninguna carpeta, y debe dejar la traza de archivo en estado
`error` con el motivo **en forma de código** (los de R7, R8, R13, R14, R16,
R35 y R38),
sin nombres de cliente ni contenido del PDF.

**R19.** CUANDO el destino no se resuelve, `POST /api/archivar` debe responder
**409** con el mismo cuerpo que ya pinta el front —`error`, un texto legible
que diga **qué tiene que hacer una persona** (crear la carpeta, desambiguar,
revisar el número de incidencia)— más dos claves nuevas: `motivo` (el código)
y `candidatas` (nombres de carpeta, nunca identificadores; lista vacía si no
hay). No es un 502: no ha fallado nadie, falta una decisión.

**R20.** Un parte con destino no resuelto debe poder **reintentarse** sin
intervención en la base: la traza en `error` no corta el reintento (F-006
R14), así que en cuanto Posventa cree o renombre la carpeta, el siguiente
archivado lo sube.

## 7 · Lo que no cambia

**R21.** El sistema debe conservar en la estrategia `posventa` todas las
garantías de F-006 y F-019 que no dependen de la carpeta: puerta de estado
`aprobado`, traza previa en `pendiente` antes de tocar el puerto, reemplazo del
homónimo con `conflictBehavior=replace`, aviso de reemplazo y traducción de
errores. El orden de los pasos pasa a ser el de `design.md` §5.

**R22.** La resolución del destino debe ocurrir **después** de la puerta de
estado y del nombrado y **antes** de la traza previa en `pendiente`: un parte
no aprobado no provoca ni la lectura de Sigrid ni los listados; y un destino no
resuelto no deja una traza `pendiente` colgada.

**R23.** El sistema no debe volcar en logs, errores ni respuestas: el DNI, las
observaciones, el contenido del PDF, el token, el secreto ni los identificadores
de sitio o biblioteca (F-006 R26). Los nombres de carpeta de obra y unidad
**sí** pueden registrarse: son de negocio y ya están en el nombre de la ruta.

**R41.** SI la lectura de la ubicación en Sigrid falla por red, tiempo o
configuración, ENTONCES el sistema no debe subir ni crear nada, debe responder
**503** y **no** debe recurrir al campo `unidad` del papel (D-7).

## 8 · Lo archivado en IT

**R24.** El sistema no debe mover, copiar, borrar ni volver a subir nada de la
biblioteca de IT (H4).

**R25.** MIENTRAS un parte conste `archivado` en `postventa.archivos` con el
`drive_id` de la biblioteca de IT, el sistema no debe volver a subirlo a la de
Posventa. **Esto no lo garantiza F-013: lo garantiza la capa L1 de F-033**, y
por eso F-033 es precondición de desplegar F-013 (D-2). Un test de F-013 lo
comprueba **desde el endpoint** una vez F-033 esté mergeada.

**R26.** La documentación debe decir, con fecha, que los partes archivados
hasta el corte siguen en la biblioteca de IT, **cómo localizarlos** (consulta de
solo lectura sobre `postventa.archivos` por `drive_id`/`web_url`, sin
identificadores en el repo) y que el archivo de Posventa **no los contiene**
(criterio de aceptación 2 de la ficha, opción «localizable»).

## 9 · Infra y documentación

**R27.** `infra/` debe tener un script **de solo lectura** que, dada la URL del
sitio por parámetro, resuelva el identificador del sitio y el de la biblioteca
«Documentos compartidos», diga qué permisos de aplicación trae el token, y
compruebe **sin escribir** que la aplicación ve el sitio. No imprime el token,
el secreto ni los identificadores salvo que el humano pida
`-MostrarIdentificadores` para copiarlos a Key Vault, y avisa de que no se
pegan en ningún fichero del repo.

**R28.** El mismo script, con `-CodigoObra`, debe listar **solo carpetas** de
la estructura de esa obra (obra → `INCIDENCIAS` → unidades → hoja) y decir,
para cada unidad de posventa que Sigrid tenga en esa obra, si la **resolvería**
(casa), la **crearía** (y con qué nombre) o la **bloquearía** (parecida o
ambigua). Sin crear nada. Es la
verificación en seco de la regla contra el archivo real.

**R29.** `docs/INTEGRACION.md` §3, `docs/DESPLIEGUE.md`,
`docs/ARCHITECTURE.md` (paso 6 y fila de SharePoint) y la spec de F-006 deben
llevar un **recuadro fechado** que cite literal la premisa que se enmienda
(sitio de IT, carpeta por código de obra, «sin listados de carpeta», «F-013
sale casi gratis») y diga qué la invalidó y quién lo decidió. Nada se borra.

**R30.** Ningún fichero del repositorio debe contener el identificador del
sitio o de la biblioteca de Posventa, ni la URL completa del tenant: el barrido
de GUID de `test_f006_repo_sin_identificadores.py` sigue en verde y se le añade
el nombre de host del tenant.

## 10 · Verificaciones manuales (humano)

**R31. MANUAL.** Antes de encender la estrategia, el humano ejecuta el script
de R27–R28 contra el sitio de Posventa para la obra piloto y anota, **sin
identificadores**, qué unidades resuelve la regla, cuáles **se crearían** y con
qué nombre, y cuáles quedan bloqueadas por una **parecida** o una ambigüedad.

**R32. MANUAL.** La medición de la ubicación en Sigrid (`design.md` §4.2): qué
devuelven `con.cod` y `con.res` de las unidades de posventa de la obra piloto.
Sin ella, la regla de casado de R11 está **[NO MEDIDA]** contra el ERP.

**R33. MANUAL.** Primer archivado real en la biblioteca de Posventa, con un
parte **autorizado expresamente** por el humano, y comprobación con Posventa de
que el fichero aparece en su carpeta y en su OneDrive sincronizado, en el sitio
esperado y **sin ninguna carpeta nueva** (se elige un parte cuya ruta ya exista
entera, según T2).

**R42. MANUAL.** Primer archivado real que **crea** carpetas (una unidad u obra
sin carpeta ni parecida, elegida con el script de R28 que diga «se crearía:
…»), autorizado expresamente y con Posventa **avisada antes**; comprobación con
ellos de que el nombre creado les sirve y de que no ha aparecido ningún
duplicado. Si no les sirve, lo deshace una persona (R43) y se enmienda R36/R37
antes de volver a crear.

**R43. MANUAL / documental.** El sistema **no borra, no mueve ni renombra**
carpetas en ningún caso. `docs/INTEGRACION.md` debe llevar el procedimiento
para deshacer una carpeta creada por error —lo hace **una persona**: mueve el
PDF a la carpeta buena (dentro de la misma biblioteca el `item_id` de la traza
se conserva), y borra o renombra la carpeta sobrante; el borrado va a la
papelera del sitio y se propaga a los OneDrive sincronizados— y la consulta de
solo lectura que lista, desde `postventa.archivos`, los partes archivados en
una carpeta dada, para saber qué hay que mover antes de borrar.
