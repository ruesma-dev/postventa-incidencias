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

> **Enmienda del 2026-09-24 · la medición de T2/T3 y la parada T4.** Nada se
> borra: cada requisito que cambia conserva su texto original, citado, en un
> recuadro con esta fecha. La medición (`progress/explore_F-013.md`, commit
> `32ddd42`) **desmintió** la regla de casado de la obra: la carpeta real de la
> 0677 es `677  MIRASIERRA` —sin el cero y con dos blancos—, así que con R10 tal
> y como estaba **ningún parte de la 0677 se habría archivado**. El humano
> decidió en la parada T4 (§0 ter). Cambian **R1, R3, R6, R9, R10, R13, R14,
> R18, R22, R31, R33, R35, R36, R37, R38, R39 y R42**; se precisan R11, R25,
> R26, R28 y R32; entran **R44–R50**. Desaparece `SHAREPOINT_NOMBRE_UNIDAD`.

> **Enmienda del 2026-09-25 (F-049) · las villas que se crean, con tres
> cifras.** En el paso 2 del corte, el script 23 contra la biblioteca real
> mostró que Posventa ha **reorganizado** las carpetas de unidad de la 0677:
> ya no son `VILLA 01` … `VILLA 07`, sino `VILLA 001` … `VILLA 007`,
> `VILLA 012` y `VILLA 013`. El humano decidió ese día «**siempre con tres
> cifras**»: la unidad que crea el sistema es `VILLA 008`, `VILLA 013`; con
> 1.000 o más, tal cual (`VILLA 1000`). **Cómo se casa no cambia**: por número
> entero, así que `VILLA 001` y `VILLA 01` son la villa 1. Cambian **R37**, la
> fila **T4-1** y la **T4-5**, el vocabulario, **R31** y **R42**, cada uno con
> su recuadro de esta fecha; la spec de la enmienda es
> `specs/F-049-villa-tres-cifras/`. Donde este documento dice `VILLA NN`
> sin más, léase «`VILLA` y el número con al menos tres cifras».

## 0 · Las decisiones del humano del 2026-09-18 (no se reabren)

| # | Decisión, literal en lo esencial | Dónde se traduce |
|---|---|---|
| **H1** | Destino: el sitio de **Posventa**, biblioteca **«Documentos compartidos»**. Se abandona la biblioteca temporal del sitio de IT | R1, R2; configuración, `design.md` §6 |
| **H2** | Estructura: **la que ya usa Posventa**, `<cod> <OBRA> / PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS / <fichero>`. El nombre del fichero **no cambia** | R3–R16 |
| **H3** | «PARTES FIRMADOS (sistema)» como carpeta base de la estructura propia: con la estructura de Posventa probablemente no aplica. Se dejó abierto y **se cerró el mismo día como D-1**: raíz de la biblioteca | D-1; R17 |
| **H4** | **Lo ya archivado en IT se queda en IT**, sin migración, y se documenta que sigue allí | R24–R26. **Enmendada el 2026-09-22**: la segunda mitad («se documenta que sigue allí», en el sentido de documentar cómo localizarlo) decae; el «se queda en IT, sin migración» se refuerza a **no se borra nada**. Recuadro en §8 |

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
| **D-6** | Regla de casado de la unidad, la propuesta, **condicionada a T2/T3** (**sostenida** por la medición del 2026-09-24) | R11, `design.md` §4.3 |
| **D-7** | Sigrid caída al archivar → 503, no se sube, no se cae al dato del papel | R41 |
| **D-R** | Rigor `critico` | cabecera |

### 0 ter · La parada T4, cerrada por el humano el 2026-09-24

Con la medición de T2 y T3 delante (`progress/explore_F-013.md`). Respuestas
literales del humano, recogidas por el líder en `progress/current.md`:

| Id | Decisión, literal en lo esencial | Dónde se traduce |
|---|---|---|
| **T4-1** | **Nombre al crear**: «Unidad al estilo Posventa (Recomendado)». La unidad se crea como `VILLA NN`, derivada del `con.cod` de Sigrid (`0677.03VILLA 13.` → `VILLA 13`, dos cifras); la obra como `<cod> <con.res de Sigrid>`, que Posventa renombra si quiere: como se casa por número, el sistema la sigue encontrando | R36, R37; `SHAREPOINT_NOMBRE_UNIDAD` desaparece (R1, R3) |
| **T4-2** | **Unidad sin subcarpetas** (VILLA 04, 142 partes sueltos): «Crear PARTES FIRMADOS (Recomendado)». Lo antiguo se queda donde está | R48 |
| **T4-3** | **Arranque**: «Crear desde el principio». `SHAREPOINT_CREAR_CARPETAS` activo desde el primer despliegue contra Posventa, con las ventanas abiertas por defecto: el primer parte de una villa sin carpeta la creará | R33, R42; `design.md` §7.3 |
| **T4-4** | **Casar la obra por su número** (677 = 0677), ignorando el resto del nombre: propuesto por el líder como necesario y no discutido | R10, R13, R35 |
| **T4-5** | **Villas 8 a 15**: «no tienen carpeta, que se creen». Se crean bajo `677  MIRASIERRA / PARTES INCIDENCIAS` como `VILLA NN` con su `PARTES FIRMADOS` | R34, R37; tabla de `design.md` §4.6 |
| **T4-6** | **La hoja de VILLA 02** se llama `PARTES FIRMADO` (singular): «que cuente como buena». Cuenta como la hoja, se archiva dentro y no se crea otra `PARTES FIRMADOS` al lado | R14, R49 |

> **Enmienda del 2026-09-25 (F-049) · T4-1 y T4-5, con tres cifras.** La
> fila T4-1 decía, literal: *«La unidad se crea como `VILLA NN`, derivada del
> `con.cod` de Sigrid (`0677.03VILLA 13.` → `VILLA 13`, dos cifras)»*; y la
> T4-5, que las villas 8 a 15 se crean *«como `VILLA NN` con su `PARTES
> FIRMADOS`»*. **Qué las invalidó**: Posventa reorganizó la biblioteca a
> `VILLA 001` … `VILLA 007`, `VILLA 012` y `VILLA 013` (script 23, paso 2 del
> corte, 2026-09-25), y el humano decidió ese día «siempre con tres cifras».
> Desde hoy: `0677.03VILLA 13.` → `VILLA 013`, y las villas que falten se
> crean como `VILLA 008` … con su `PARTES FIRMADOS`. **Lo que no cambia**: la
> unidad se sigue derivando del `con.cod` «al estilo Posventa», y T4-1 sigue
> diciendo lo mismo de la obra.

Y dos que decide **esta enmienda** (spec-author, 2026-09-24) por no dejar un
hueco donde la medición lo abrió, **a validar por el humano sin bloquear**:
R44 (dos obras de Sigrid con el mismo número → 409) y R50 (una carpeta de
unidad que casaría con dos unidades de la obra → 409). Las dos fallan
**cerradas**: su coste es un 409, nunca un parte en la carpeta de otro.

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

   > **Precisión del 2026-09-24 (T2/T3).** La carpeta de obra real es
   > `677  MIRASIERRA`; las de unidad, `VILLA 01` … `VILLA 07`. En Sigrid, la
   > 0677 es **la única obra con unidades de posventa** con ese código (T3
   > buscó `0677` y `677`: **1** obra; la segunda fila del maestro no tiene
   > unidades de posventa, así que ninguna reclamación de posventa cuelga de
   > ella). Sus 15 unidades tienen `con.cod` `0677.03VILLA N.` y `con.res`
   > `Viviendas Bloque Villa N`, sin nombres de persona **[MEDIDO, T3]**. Que
   > el código no sea único en general sigue siendo cierto y lo cubre R44.
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
| **Borrar** lo archivado en IT: ficheros de su biblioteca, filas de `postventa.archivos` | Decisión del humano del **2026-09-22**: «se pueden olvidar, pero no borrar» (§8) | — |
| **Retirar la traza `archivado`** de esos partes para poder re-archivarlos en Posventa | La misma decisión. Cierra la decisión abierta que dejaron F-033 (O-2) y su acta de cierre | — |
| Pintar la cola de «destino no resuelto» en el front | Es circuito de front | propuesta de ficha nueva (D-5) |

## Vocabulario

| Término | Qué es |
|---|---|
| **Estrategia de destino** | Cómo se compone la carpeta: `por_obra` (F-006: `<base>/<cod obra>`) o `posventa` (F-013). Configuración `SHAREPOINT_ESTRUCTURA` |
| **Carpeta de obra** | La carpeta de primer nivel bajo la base cuyo nombre es `<cod obra>` seguido de un blanco y el nombre de la obra. La crea Posventa o, si no hay ninguna ni parecida, el sistema (R34). **Precisado el 2026-09-24**: lo que la identifica es el **número de obra** con el que **empieza** su nombre (`677  MIRASIERRA` es la de la 0677); el resto del nombre no cuenta (R10) |
| **Carpeta de unidad** | La carpeta bajo `<obra>/PARTES INCIDENCIAS/` de una unidad de posventa (`VILLA 05`). La crea Posventa o, si no hay ninguna ni parecida, el sistema (R34) |
| **Candidata que casa** | Carpeta que cumple la regla **estricta** de su nivel (R10, R11, `design.md` §4) |
| **Carpeta parecida** | Carpeta que **no** casa pero cumple la regla **amplia** de su nivel (`design.md` §4.5): el mismo código de obra, el mismo número de unidad o la misma palabra clave del tramo fijo, con otra grafía. Su existencia **impide crear** (R35) |
| **Hoja** | `PARTES FIRMADOS`, la carpeta final dentro de la unidad. Desde el 2026-09-24 (T4-6) también cuenta como hoja `PARTES FIRMADO`, la forma **alternativa** admitida (R49) |
| **Número de obra** | El valor **entero** del código de obra: `0677`, `677` y `00677` tienen el número 677. Solo para códigos formados únicamente por cifras; un código con letras no tiene número y se compara literal (R10). Añadido el 2026-09-24 |
| **Nombre derivado de la unidad** | `VILLA NN`, compuesto del `con.cod` de la unidad de Sigrid con la regla de R37. Añadido el 2026-09-24 |
| **Ubicación de la reclamación** | Lo que Sigrid dice de la reclamación: código de la obra y código y nombre de su **unidad de posventa** (`rcp.upvide → upv`, y `upv.obride → obr`), leído por `sigrid-api` |
| **Clave de unidad** | La forma canónica con la que se compara una unidad: mayúsculas, sin tildes, blancos colapsados y **los números comparados como enteros** (`05` = `5`) — ver `design.md` §4.3 |
| **Destino no resuelto** | Resultado del archivado que **no sube nada** porque una carpeta del camino es ambigua, solo hay parecidas o no se puede crear. Lleva motivo y candidatas |

> **Enmienda del 2026-09-25 (F-049) · el nombre derivado, con tres cifras.**
> El término «Nombre derivado de la unidad» decía, literal: *«`VILLA NN`,
> compuesto del `con.cod` de la unidad de Sigrid con la regla de R37»*.
> **Qué lo invalidó**: la decisión del humano del 2026-09-25, «siempre con
> tres cifras». Desde hoy es `VILLA` y el número de la unidad con **al menos
> tres cifras** (`VILLA 008`, `VILLA 013`, `VILLA 1000`), con la regla de R37
> enmendada.

---

## 1 · El destino es configuración

**R1.** El sistema debe leer de configuración la estrategia de destino
(`SHAREPOINT_ESTRUCTURA`, valores `por_obra` y `posventa`), los nombres
literales de los dos tramos fijos de la estructura de Posventa
(`SHAREPOINT_CARPETA_INCIDENCIAS`, por omisión `PARTES INCIDENCIAS`, y
`SHAREPOINT_CARPETA_FIRMADOS`, por omisión `PARTES FIRMADOS`), la forma
alternativa admitida de la hoja (`SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA`,
por omisión `PARTES FIRMADO`; vacía = ninguna, R49) y si se pueden crear
carpetas (`SHAREPOINT_CREAR_CARPETAS`, por omisión encendido, D-4). Cambiar de
estrategia o de nombres **no debe tocar** el dominio, la aplicación ni el
pipeline (criterio de aceptación 1 de la ficha).

> **Enmienda del 2026-09-24 · T4-1 y T4-6.** R1 decía además, literal: *«y de
> qué campo de la unidad de Sigrid sale el nombre de una unidad creada
> (`SHAREPOINT_NOMBRE_UNIDAD`, `codigo` o `nombre`, R37)»*. **Qué la
> invalidó**: la decisión del humano en T4 de crear la unidad como `VILLA NN`
> derivado del `con.cod` (R37). Con una regla fija, la variable no tiene nada
> que elegir: una segunda forma sería otra enmienda de la spec con su
> medición, no un valor de configuración. **Se retira.** Entra
> `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` por T4-6 (VILLA 02).

**R2.** MIENTRAS `SHAREPOINT_ESTRUCTURA` valga `por_obra` —que es el valor por
omisión— y la base no esté vacía (R17), el sistema debe componer la carpeta y
el nombre **exactamente** como hoy (F-006 R1–R12), sin llamar a Sigrid ni listar ninguna carpeta. Los tests
de F-006 siguen en verde sin tocarlos.

**R3.** SI `SHAREPOINT_ESTRUCTURA` trae un valor que no es ninguno de los dos,
ENTONCES la construcción del archivador debe fallar con
`ConfiguracionSharePointIncompleta` nombrando la variable y los valores
admitidos, **antes** de pedir ningún token.

> **Enmienda del 2026-09-24.** R3 decía también, literal: *«o
> `SHAREPOINT_NOMBRE_UNIDAD` uno que no es `codigo` ni `nombre`»*. Cae con la
> variable (recuadro de R1). Un test comprueba que `config/settings.py` **no**
> tiene el campo, para que no vuelva por inercia.

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

> **Enmienda del 2026-09-24 · R44 y R50.** «Una sola consulta» deja de ser
> toda la lectura: si la ubicación pasa R7 y R8, el sistema hace **una segunda
> lectura**, también parametrizada y también por `sql/read`, de las unidades de
> posventa de las obras con **el mismo número** (R44). La primera sigue siendo
> una sola consulta y no cambia. Máximo por parte: **dos** lecturas de Sigrid.

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
>
> **Precisión del 2026-09-24 · T4-1.** Los nombres de Sigrid que componen son
> el `con.res` de la obra (R36) y el `con.cod` de la unidad, del que se
> **deriva** `VILLA NN` con una regla fija (R37). El `con.res` de la unidad
> sigue sirviendo **solo para casar** (§4.3 de `design.md`).

## 4 · Casar con las carpetas que existen

**R10.** Para localizar la carpeta de obra, el sistema debe listar las
**carpetas** (no los ficheros) hijas de `<base>` y quedarse con las que
**empiezan por el número de la obra**: partido el nombre por blancos (uno o
varios, de cualquier clase), la **primera palabra** está formada solo por
cifras y su valor **entero** es el número de la obra. El resto del nombre no
cuenta. Así `677  MIRASIERRA`, `0677 MIRASIERRA`, `677` y
`0677 15 VIVIENDAS…` casan con la obra `0677`; **no** casan `06770 X`
(6770), `0677-MIRASIERRA` ni `677MIRASIERRA` (la primera palabra lleva algo
más que cifras), ni `OBRA 0677` (no empieza por el número). SI el código de
obra del parte **no** está formado solo por cifras, ENTONCES se aplica la
regla literal de antes: el nombre recortado es el código o empieza por el
código seguido de un blanco.

> **Enmienda del 2026-09-24 · T4-4.** R10 decía, literal: *«…y quedarse con
> las que cumplen que su nombre, recortado, **empieza por el código de obra
> seguido de un blanco** (o es exactamente el código). La comparación del
> código es literal y conserva los ceros: `0677` no casa con `677 ...` ni con
> `06770 ...`.»* **Qué la invalidó**: T2 midió que la carpeta real de la 0677
> es `677  MIRASIERRA` —sin el cero y con dos blancos—; con la regla literal
> no casaba ninguna (0 casan, 1 parecida → 409 `obra_parecida` en **todos** los
> partes de la obra piloto). El líder propuso en T4 casar por número y el
> humano no lo discutió. **Lo que no cambia**: `06770` sigue sin casar con
> `0677`, porque se compara el número entero y no un prefijo de texto; y las
> grafías con otro separador (`0677-MIRASIERRA`) siguen siendo **parecidas**,
> no candidatas (R35).

**R11.** Para localizar la carpeta de unidad, el sistema debe listar las
carpetas hijas de `<carpeta de obra>/<INCIDENCIAS>` y quedarse con las que
cumplen la regla de casado de la **clave de unidad** (`design.md` §4.3) contra
el código **o** el nombre de la unidad de Sigrid.

> **Medido el 2026-09-24 (T2/T3): la regla de D-6 se sostiene.** Los siete
> casos reales casan por el nombre: `VILLA 05` es sufijo de la clave de
> `Viviendas Bloque Villa 5` (`05` = `5`). Por el código no casa ninguno
> (`0677.03VILLA 5.` da la clave `677 03VILLA 5`), y no hace falta. Sin
> cambios en R11.

**R12.** Los listados deben pedir **solo carpetas** y deben seguir la
paginación del proveedor hasta el final: una biblioteca con cientos de obras
no puede resolver mal porque la obra buscada estuviera en la segunda página.

**R13.** SI hay **más de una** candidata que casa a carpeta de obra, ENTONCES
«destino no resuelto», motivo `obra_ambigua`, con los nombres de las
candidatas en el resultado. (Cero candidatas: R34, R35.)

> **Precisión del 2026-09-24 · T4-4.** Con el casado por número, «más de una»
> es **dos carpetas de la raíz que empiezan por el mismo número de obra**, se
> llamen como se llamen: `677  MIRASIERRA` y `0677 MIRASIERRA FASE 2` →
> `obra_ambigua` con las dos. El sistema **no elige** entre ellas por el resto
> del nombre ni por el número de ceros: lo resuelve una persona renombrando
> una. Hoy en la raíz de Posventa hay **una** (T2).

**R14.** Para cada uno de los otros tres niveles —`<INCIDENCIAS>`, unidad y
`<FIRMADOS>`— SI hay **más de una** que casa, ENTONCES «destino no resuelto»
con motivo `incidencias_ambigua`, `unidad_ambigua` o `firmados_ambigua`, con
las candidatas. (Cero: R34, R35.) En el nivel `<FIRMADOS>` casan tanto la
forma principal como la alternativa (R49), así que una unidad con
`PARTES FIRMADOS` **y** `PARTES FIRMADO` es `firmados_ambigua` (precisado el
2026-09-24, T4-6).

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

> **Enmienda del 2026-09-24 · la medición.** Casan y parecidas son una
> **partición**: una carpeta que casa no es parecida, así que la carpeta real
> `677  MIRASIERRA` casa y no bloquea nada. Las reglas amplias se ensanchan
> donde la medición enseñó un hueco (`design.md` §4.5): en obra y unidad se
> miran **todas las secuencias de cifras** del nombre (así `677MIRASIERRA` y
> `VILLA5` son parecidas), y en los tramos fijos la palabra distintiva se
> compara **sin la `S` final** (así `PARTE FIRMADO` y `PARTES INCIDENCIA` son
> parecidas). El hueco, con nombre: la hoja de VILLA 02 se llama
> `PARTES FIRMADO`, y con la regla amplia de antes —el token `FIRMADOS`
> exacto— **no** habría sido parecida y el sistema habría creado
> `PARTES FIRMADOS` a su lado. Hoy casa como alternativa (R49), pero la
> siguiente grafía del mismo tipo tiene que parar. Tests obligatorios que se
> **añaden**: `677  MIRASIERRA` **casa** con la 0677 y no es parecida;
> `677MIRASIERRA` impide crear la obra 0677; `VILLA 03` **no** impide crear
> `VILLA 13`, ni `VILLA 01` … `VILLA 07` impiden crear `VILLA 08` …
> `VILLA 15` (T4-5); `PARTE FIRMADO` impide crear `PARTES FIRMADOS`.

**R36.** El nombre de una carpeta de **obra** creada debe ser
`<código de obra> <nombre de la obra en Sigrid>`: el código normalizado (ceros
intactos) y el `con.res` **de esa obra** —la de `upv.obride`, no cualquiera con
el mismo código—, literal, recortado y con los blancos interiores colapsados a
uno. Ejemplo medido: `0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)`.
**Condicionado a T2** (`design.md` §4.6): si T2 muestra que Posventa usa otra
forma **derivable de forma determinista** de Sigrid, se enmienda con test antes
de implementar; si no es derivable, se queda esta.

> **Resuelto el 2026-09-24 · T4-1: se queda esta.** T2 midió `677  MIRASIERRA`:
> un nombre corto que **no** se deriva del `con.res` («15 VIVIENDAS
> UNIFAMILIARES EN MIRASIERRA(MADRID)») sin inventar. El humano decidió crear
> la obra con `<cod> <con.res>` literal. Posventa **puede renombrarla** como
> quiera mientras el nombre siga **empezando por el número de la obra y un
> blanco**: el siguiente archivado la encuentra por R10. Si la renombra de otra
> forma (`MIRASIERRA 677`), la siguiente resolución da 409 `obra_parecida`, que
> es el aviso correcto. Para la 0677 **no se crea nunca**: ya existe.

**R37.** El nombre de una carpeta de **unidad** creada debe ser el **nombre
derivado** del `con.cod` de la unidad de posventa de Sigrid, con esta regla y
ninguna otra (`design.md` §4.6, tabla de los 15 casos medidos):

1. el `con.cod`, sin blancos en los extremos, cumple **entero** el patrón
   `<obra>.<grupo>VILLA <n>.` —`<obra>`, `<grupo>` y `<n>` solo cifras,
   `VILLA` en mayúsculas, uno o más blancos antes de `<n>` y el punto final—
   (medido: `0677.03VILLA 13.`);
2. el número de `<obra>` es el número de la obra del parte;
3. el nombre es `VILLA ` seguido de `<n>` como entero con **al menos dos
   cifras**: `1` → `VILLA 01`, `13` → `VILLA 13`, `100` → `VILLA 100`.

SI el `con.cod` no cumple 1 o 2, ENTONCES el sistema **no inventa** un
nombre: «destino no resuelto», motivo `unidad_sin_nombre_derivable`, y no se
crea nada. Solo se evalúa **cuando hay que crear** la unidad: una unidad cuya
carpeta ya existe y casa (R11) no necesita nombre derivado. Los dos tramos
fijos se crean con el literal de `SHAREPOINT_CARPETA_INCIDENCIAS` y
`SHAREPOINT_CARPETA_FIRMADOS` (nunca con la alternativa de R49).

> **Enmienda del 2026-09-24 · T4-1.** R37 decía, literal: *«El nombre de una
> carpeta de **unidad** creada debe salir de la unidad de posventa de Sigrid,
> del campo que fije `SHAREPOINT_NOMBRE_UNIDAD` (`codigo` → `con.cod` de la
> `upv`; `nombre` → su `con.res`), literal, recortado y con blancos colapsados.
> El valor por omisión **se fija en T4 con T2/T3 delante**: `codigo` si
> `upv.cod` tiene ya la forma corta de Posventa (`VILLA 05`), `nombre` en otro
> caso. El sistema **no reformatea**: no rellena ceros ni abrevia, porque un
> `VILLA 05` fabricado a partir de «Villa 5» sería una convención que nadie ha
> escrito.»* **Qué la invalidó**: T3 midió que ni `con.cod` (`0677.03VILLA 5.`)
> ni `con.res` (`Viviendas Bloque Villa 5`) tienen la forma de Posventa, y T2
> midió que esa forma **sí está escrita**: siete carpetas `VILLA 01` …
> `VILLA 07`, siempre con dos cifras. La convención ya no es una que «nadie ha
> escrito», es la que Posventa usa; el humano eligió en T4 «Unidad al estilo
> Posventa». **Lo que no cambia**: no se sanea ni se adivina; lo que no cumple
> el patrón medido es un 409. **Solo `VILLA`**: la regla no se extiende a otras
> palabras (`CHALET`, `PORTAL`…) sin medir cómo las nombra Posventa; ampliarla
> es otra enmienda con su medición.

> **Enmienda del 2026-09-25 (F-049) · al menos tres cifras.** El punto 3 de
> R37 decía, literal: *«el nombre es `VILLA ` seguido de `<n>` como entero con
> **al menos dos cifras**: `1` → `VILLA 01`, `13` → `VILLA 13`, `100` →
> `VILLA 100`.»* **Qué lo invalidó**: en el paso 2 del corte (2026-09-25) el
> script 23 mostró que Posventa ha reorganizado sus carpetas de unidad a
> `VILLA 001` … `VILLA 007`, `VILLA 012` y `VILLA 013`; con dos cifras, lo que
> creara el sistema (`VILLA 08`) no se parecería a lo suyo. El humano decidió
> ese día «**siempre con tres cifras**», en todas las obras. **Desde hoy**, el
> punto 3 es: el nombre es `VILLA ` seguido de `<n>` como entero con **al
> menos tres cifras**: `1` → `VILLA 001`, `8` → `VILLA 008`, `13` →
> `VILLA 013`, `100` → `VILLA 100`, `1000` → `VILLA 1000`; los ceros que traiga
> el `con.cod` no cuentan (`0677.03VILLA 008.` → `VILLA 008`). **Lo que no
> cambia**: los puntos 1 y 2, el 409 `unidad_sin_nombre_derivable`, y **cómo
> se casa** (R11, `design.md` §4.3): la clave compara enteros, así que
> `VILLA 001`, `VILLA 01` y `VILLA 1` siguen siendo la villa 1. Tests:
> `test_f049_*` (`specs/F-049-villa-tres-cifras/`).

**R38.** SI el nombre compuesto para crear una carpeta está vacío, lleva algún
carácter que SharePoint no admite (`" * : < > ? / \ |`), empieza o acaba en
blanco o acaba en punto, ENTONCES el sistema no debe sanearlo ni crear nada, y
debe responder «destino no resuelto» con motivo `nombre_carpeta_imposible`
(la misma regla que F-006 R7 aplica al fichero). Todos los nombres que la
resolución vaya a necesitar se componen y se comprueban **antes de crear la
primera carpeta**: un nombre de unidad imposible no puede dejar creada una
carpeta de obra vacía.

> **Precisión del 2026-09-24.** Cada nombre se compone **cuando su nivel hay
> que crearlo**, no antes de listar: el nombre derivado de R37 solo existe si
> la unidad falta, y exigirlo siempre pararía unidades que ya tienen carpeta.
> La garantía de R38 no se pierde, porque el resolutor **no crea nada** y el
> paso ejecuta las creaciones solo tras una resolución **completa** (`design.md`
> §5): cualquier 409 de un nivel inferior sale con **cero** creaciones hechas.
> El test lo comprueba así: nombre de unidad imposible bajo una obra que
> también falta → 409 y el doble del explorador sin ninguna `crear_subcarpeta`.

**R39.** Una carpeta creada por el sistema debe **casar** consigo misma en el
siguiente archivado: dos partes seguidos de la misma unidad nueva crean las
carpetas **una vez**, y la segunda resolución las encuentra por la regla
estricta sin que ninguna parecida la bloquee. Y dos partes concurrentes que
creen la misma carpeta acaban en **una**: se crea con
`conflictBehavior=fail`, el `409` cuenta como «ya existe» (F-006 R12) y el
nombre es determinista. Desde el 2026-09-24 esto no se queda en una
propiedad de la regla: se **comprueba** en cada creación (R46).

**R40.** CUANDO el sistema crea una o más carpetas, la respuesta de
`/api/archivar` debe llevar en `avisos` una línea por carpeta creada con su
ruta, y el log una línea `F-013 carpeta creada: <ruta>`. Quien archiva tiene
que ver que ha aparecido una carpeta nueva en la biblioteca de Posventa.

## 5 ter · Lo que añade la medición (2026-09-24)

**R44.** DONDE la estrategia sea `posventa`, CUANDO la ubicación ha pasado R7
y R8, el sistema debe leer de Sigrid, por `sql/read` y con una consulta
parametrizada, las **unidades de posventa de todas las obras cuyo código tiene
el número de obra del parte** (o, si el código no es numérico, el mismo
código), con una referencia opaca de su obra. SI entre ellas hay **más de una
obra**, o ninguna, ENTONCES «destino no resuelto», motivo
`obra_numero_no_unico`, y no se lista ni se crea nada: con el casado por
número, dos obras de Sigrid con el mismo número irían a la **misma** carpeta
de Posventa. SI la respuesta llega con **1.000 filas** —el máximo que sirve
`sigrid-api` por petición, así que puede venir cortada—, ENTONCES
«destino no resuelto», motivo `unidades_sin_verificar`. La referencia de obra
**no** sale de la lectura: ni a logs, ni a respuestas, ni a la base (R23).
Para la 0677 hay **una** obra con unidades de posventa **[MEDIDO, T3]**.

**R45.** MIENTRAS la estrategia sea `posventa`, la capa L1 de F-033 debe
cortar **antes de resolver**: un parte que consta `archivado` no provoca ni la
lectura de Sigrid (R6, R44) ni ningún listado. El aviso de «archivado en otro
destino» (F-033 R14) se decide en ese punto con lo que se sabe **sin
resolver**: el nombre del fichero y la biblioteca. La carpeta **no** se
compara, porque conocerla exigiría leer Sigrid y listar, que es justo lo que L1
evita. Consecuencia aceptada: un parte archivado en Posventa cuya carpeta se
renombró después no recibe ese aviso.

**R46.** Antes de anotar la creación de una carpeta, el sistema debe
comprobar que su nombre **casa** por la regla estricta de su nivel (R10, R11,
tramo fijo) con los mismos datos con los que se resolvió. SI no casa,
ENTONCES «destino no resuelto», motivo `nombre_no_casaria`, y no se crea nada:
una carpeta que el siguiente archivado no encontraría quedaría huérfana y,
además, bloquearía su propio nivel como parecida.

**R47.** SI el destino no se resuelve y la traza guardada del parte está en
`pendiente`, ENTONCES el sistema debe dejar en el log, **antes** de escribir
la traza en `error` que la pisa, la carpeta y el nombre de aquel intento (sin
ningún identificador de biblioteca), igual que F-033 R20 hace antes de la
traza previa. Sin esto, un fichero subido sin traza final perdería su único
rastro.

**R48.** CUANDO la carpeta de unidad existe y no tiene **ninguna subcarpeta**
—ni la hoja, ni una parecida—, aunque tenga ficheros sueltos, el sistema debe
crear dentro la hoja `PARTES FIRMADOS` (R34) y archivar en ella. Los ficheros
sueltos **no se tocan**: ni se listan por su nombre, ni se mueven, ni se
renombran. El puerto del explorador no tiene ninguna operación que pudiera
hacerlo (`design.md` §3.2). Es el caso medido de VILLA 04: 142 partes sueltos
(T4-2).

**R49.** El sistema debe aceptar como hoja, además de
`SHAREPOINT_CARPETA_FIRMADOS`, **exactamente** la forma de
`SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` (por omisión `PARTES FIRMADO`), con
la misma comparación que los tramos fijos (mayúsculas, sin tildes, blancos
colapsados) y **ninguna otra grafía**: `PARTE FIRMADO` o `FIRMADOS` siguen
siendo parecidas (R35). Una hoja alternativa que casa se usa **con su nombre
tal y como existe**. SI en la misma unidad existen la principal y la
alternativa, ENTONCES `firmados_ambigua` (R14). El sistema nunca **crea** la
alternativa. Es el caso medido de VILLA 02 (T4-6).

**R50.** CUANDO se ha elegido —o se va a crear— la carpeta de unidad, el
sistema debe comprobar, con las unidades de la obra leídas en R44, que ese
nombre casa por la regla estricta de unidad (§4.3 de `design.md`) con **una y
solo una** de ellas. SI casa con más de una, o con ninguna, ENTONCES
«destino no resuelto», motivo `unidad_carpeta_compartida`, con la carpeta como
candidata. Es la misma defensa que R8 pero un nivel más abajo: el DNI no puede
acabar en la carpeta de la villa de al lado porque dos unidades de Sigrid
compartan número. En la 0677 los 15 números son distintos **[MEDIDO, T3]**.

## 6 · El destino no resuelto

**R18.** CUANDO el destino no se resuelve, el sistema **no debe** pedir la
subida ni crear ninguna carpeta, y debe dejar la traza de archivo en estado
`error` con el motivo **en forma de código** (los de R7, R8, R13, R14, R16,
R35 y R38 —y, desde el 2026-09-24, los de R37, R44, R46 y R50:
`unidad_sin_nombre_derivable`, `obra_numero_no_unico`,
`unidades_sin_verificar`, `nombre_no_casaria` y `unidad_carpeta_compartida`—),
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
estado, del cotejo de los códigos declarados (F-031, punto 1 bis), del
nombrado y de la capa L1 (F-033), y **antes** del aviso del intento anterior
(F-033 R20) y de la traza previa en `pendiente`: un parte no aprobado, uno
cuyo cuerpo no cuadra con lo guardado y uno que ya consta archivado no
provocan ni la lectura de Sigrid ni los listados; y un destino no resuelto no
deja una traza `pendiente` colgada. Los códigos con los que se resuelve son
los **guardados** (`codigos_guardados`, F-031 R1), nunca los del cuerpo ni
`ctx.extraccion`.

> **Enmienda del 2026-09-24 · lo que ya está desplegado.** R22 decía,
> literal: *«La resolución del destino debe ocurrir **después** de la puerta de
> estado y del nombrado y **antes** de la traza previa en `pendiente`: un parte
> no aprobado no provoca ni la lectura de Sigrid ni los listados; y un destino
> no resuelto no deja una traza `pendiente` colgada.»* **Qué la dejó
> incompleta**: F-031 (cotejo en 1 bis y códigos desde lo guardado), F-033 (L1
> activa desde el almacén) y F-034 (el cotejo mudado a `codigos_del_parte.py`)
> se cerraron y desplegaron después de escribirla. El orden real del paso, en
> `application/pipelines/paso_archivo.py` (`paso_archivo`, hoy líneas
> 273–311), es: puerta → cotejo → nombrado desde lo guardado → L1 → aviso del
> intento anterior → traza previa → carpeta → buscar → subir → traza final. El
> resolutor entra **entre L1 y el aviso** (`design.md` §5). Nada de lo que R22
> protegía cambia; se precisa dónde.

**R23.** El sistema no debe volcar en logs, errores ni respuestas: el DNI, las
observaciones, el contenido del PDF, el token, el secreto ni los identificadores
de sitio o biblioteca (F-006 R26). Los nombres de carpeta de obra y unidad
**sí** pueden registrarse: son de negocio y ya están en el nombre de la ruta.

**R41.** SI la lectura de la ubicación en Sigrid falla por red, tiempo o
configuración, ENTONCES el sistema no debe subir ni crear nada, debe responder
**503** y **no** debe recurrir al campo `unidad` del papel (D-7).

## 8 · Lo archivado en IT

> **Enmienda del 2026-09-22 · la premisa H4 se deroga en parte y se precisa.
> Nada se borra de esta spec: la premisa original se cita entera y sigue
> abajo.**
>
> **La premisa original**, H4 del 2026-09-18: *«Lo ya archivado en IT se queda
> en IT, sin migración, y se documenta que sigue allí»*. De ahí salían R24–R26,
> y en particular la obligación de R26 de documentar **cómo localizar** esos
> partes.
>
> **Qué la invalidó, y quién.** El humano, en dos pasos:
>
> - **2026-09-18**, literal: *«lo que esta en IT eran pruebas, se puede
>   olvidar»*. Si son pruebas, no hay nada que localizar: documentar el
>   procedimiento de búsqueda sería mantener vivo un inventario de material
>   desechado. **Decae la obligación de documentar cómo localizarlo** (R26).
> - **2026-09-22**, literal: *«los partes en IT se pueden olvidar, pero no
>   borrar»*. Precisa la anterior y marca el límite: olvidar **no** es borrar.
>   **No se borra nada**: ni los ficheros de la biblioteca de IT, ni las filas
>   de `postventa.archivos`, ni se les retira la traza `archivado` para
>   poder re-archivarlos en Posventa (R24).
>
> **La contrapartida aceptada, escrita.** Con **D-1 de F-033** —cortar siempre
> por `hash` + estado—, un parte con traza `archivado` no se vuelve a subir.
> Como esas trazas **no se tocan**, los **133 partes** archivados en IT
> **nunca se subirán a la biblioteca de Posventa**. Es lo aceptado, no un
> efecto colateral por descubrir. F-013 archiva en Posventa **solo lo que se
> archive a partir de su despliegue**.
>
> **La cifra, medida.** **133** trazas, **todas** `archivado` y todas con
> biblioteca, en **una sola** biblioteca —la de IT—, del 2026-08-26 al
> 2026-09-18. **[MEDIDO]** el 2026-09-18 con
> `infra/25_mediciones_despliegue.ps1` (solo lectura); fuente:
> `progress/cierre_verificaciones_F-033.md`. Trazas `pendiente`: **0**.
>
> **Qué cierra.** La **decisión abierta** que dejaron apuntada el implementer
> de F-033 y su review (**observación O-2**: «F-013 tendrá que decidir qué hace
> con esas trazas»). Queda **cerrada**: no se hace nada con ellas.
>
> Esto **no reabre F-033 ni cambia el alcance de F-013**: se corrige el texto
> de H4 y de R26 para que no mientan, y se deja la constancia.

**R24.** El sistema no debe mover, copiar, borrar ni volver a subir nada de la
biblioteca de IT (H4). **Precisado el 2026-09-22**: tampoco debe borrarse
—ni por el sistema ni en el corte, que lo da una persona— **ninguna fila de
`postventa.archivos`** de esos partes, ni retirárseles el estado `archivado`
ni el `drive_id` que apunta a IT. No hay ningún paso del despliegue de F-013
que escriba sobre esas trazas.

**R25.** MIENTRAS un parte conste `archivado` en `postventa.archivos` con el
`drive_id` de la biblioteca de IT, el sistema no debe volver a subirlo a la de
Posventa. **Esto no lo garantiza F-013: lo garantiza la capa L1 de F-033**, y
por eso F-033 es precondición de desplegar F-013 (D-2). Un test de F-013 lo
comprueba **desde el endpoint** una vez F-033 esté mergeada. Desde la enmienda
del 2026-09-22 esto no es solo una salvaguarda: es **el resultado querido**
para los 133 partes de IT. **Precisado el 2026-09-24**: F-033 está mergeada y
desplegada, y la rama de F-013 sale de `dev` con ella dentro; el test ya se
puede escribir sin esperar a nada. Con `posventa`, además, L1 corta **antes**
de resolver (R45).

**R26.** La documentación debe decir, con fecha, que los partes archivados
hasta el corte —**133**, medidos el 2026-09-18— siguen en la biblioteca de IT,
que **no se migran, no se borran y no se les retira la traza**, y que por eso
el archivo de Posventa **no los contiene ni los contendrá**. **Añadido el
2026-09-24** (hallazgo H-3 de F-034): la puerta de archivo del gráfico y del
cierre (`exigir_parte_archivado`) mira el **estado** de la traza y no su
biblioteca, así que uno de esos partes, archivado en IT, **sí** puede
adjuntarse y cerrarse en Sigrid. Esta spec lo lee como coherente con
«olvidar sin borrar» —el parte está archivado, aunque no en Posventa— y **no
toca esa puerta**; queda anotado para que el humano lo valide
(`progress/current.md`), sin bloquear.

> **Enmendado el 2026-09-22.** R26 decía además: *«**cómo localizarlos**
> (consulta de solo lectura sobre `postventa.archivos` por
> `drive_id`/`web_url`, sin identificadores en el repo)»*, por la segunda
> mitad de H4 y por el criterio de aceptación 2 de la ficha, opción
> «localizable». Esa obligación **decae** con la decisión del 2026-09-18 («eran
> pruebas, se puede olvidar»): ver el recuadro de §8. Lo que R26 protegía de
> verdad sigue en pie y es lo que dice ahora —que quede escrito, con fecha, que
> el archivo de Posventa no los contiene—. La consulta de solo lectura **no se
> retira del repositorio**: sigue haciendo falta para R43 (qué partes hay en
> una carpeta antes de deshacerla).

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
verificación en seco de la regla contra el archivo real. **Precisado el
2026-09-24**: aplica la regla **del dominio** (no una copia en PowerShell),
incluidas R37, R46, R49 y R50, y su resumen cuenta lo que cuelga de la carpeta
de obra que **resuelve** esa regla (ver el defecto del resumen en
`design.md` §7.1).

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

> **Precisión del 2026-09-24 · el resultado esperado para la 0677.** Con la
> regla enmendada y la medición de T2/T3, el script (ya con la regla del
> dominio, T14) tiene que decir: obra `677  MIRASIERRA` **resolvería**;
> `PARTES INCIDENCIAS` **resolvería**; VILLA 01, 03, 05, 06 y 07
> **resolverían** (con su `PARTES FIRMADOS`); VILLA 02 **resolvería** con su
> `PARTES FIRMADO` (R49); VILLA 04 **crearía** `PARTES FIRMADOS` (R48);
> VILLA 08 … VILLA 15 **crearían** `VILLA NN` y su `PARTES FIRMADOS` (T4-5); y
> **ninguna bloquearía**. Cualquier diferencia **para el corte** y vuelve al
> líder. En particular, si VILLA 02 dice «bloquearía», el literal de su hoja no
> es `PARTES FIRMADO` (ver `design.md` §10, riesgo 16).

> **Enmienda del 2026-09-25 (F-049) · el resultado esperado, con la
> biblioteca reorganizada.** La precisión de arriba decía, literal: *«VILLA 08
> … VILLA 15 **crearían** `VILLA NN` y su `PARTES FIRMADOS` (T4-5)»*, y daba
> por existentes `VILLA 01` … `VILLA 07`. **Qué la invalidó**: el propio R31,
> lanzado en el paso 2 del corte (2026-09-25), mostró que Posventa ha
> reorganizado las carpetas de unidad de la 0677 a `VILLA 001` … `VILLA 007`,
> `VILLA 012` y `VILLA 013`; y el humano decidió ese día que el sistema cree
> **siempre con tres cifras** (R37 enmendado). **Lo que tiene que decir ahora
> el 23**: obra `677  MIRASIERRA` y `PARTES INCIDENCIAS`, «resolvería»; las
> unidades 1 a 7, 12 y 13, «resolvería» en su carpeta de tres cifras (el
> casado es por número: `VILLA 001` es la villa 1), o «crearía `PARTES
> FIRMADOS`» dentro si esa carpeta no tiene hoja (R48) —las hojas de las
> carpetas reorganizadas **no se han medido** [NO MEDIDO]: las dice el propio
> 23, y una hoja `PARTES FIRMADO` sigue valiendo (R49)—; las unidades 8 a 11,
> 14 y 15, «crearía `VILLA 008`» … `VILLA 011`, `VILLA 014` y `VILLA 015`, y su
> `PARTES FIRMADOS`; y **ninguna «bloquearía»**. Si una unidad tuviera a la
> vez `VILLA 01` y `VILLA 001`, diría «bloquearía» (`unidad_ambigua`): es lo
> correcto, lo resuelve Posventa y **para el corte** igual que cualquier otra
> diferencia.

**R32. MANUAL.** La medición de la ubicación en Sigrid (`design.md` §4.2): qué
devuelven `con.cod` y `con.res` de las unidades de posventa de la obra piloto.
Sin ella, la regla de casado de R11 está **[NO MEDIDA]** contra el ERP.
**Hecha el 2026-09-24** (T3, `progress/explore_F-013.md`).

**R33. MANUAL.** Primeros archivados reales en la biblioteca de Posventa: el
**mismo día del despliegue**, el humano localiza con una lectura
(`infra/25_mediciones_despliegue.ps1`, que cuenta trazas por biblioteca sin
imprimir identificadores) que ya hay partes archivados en la biblioteca nueva
y comprueba **con Posventa**, sobre uno de ellos cuya ruta ya existía entera,
que el fichero está en su carpeta y en su OneDrive sincronizado, en el sitio
esperado. Anota el resultado sin identificadores ni nombres de cliente.

> **Enmienda del 2026-09-24 · T4-3.** R33 decía, literal: *«Primer archivado
> real en la biblioteca de Posventa, con un parte **autorizado expresamente**
> por el humano, y comprobación con Posventa de que el fichero aparece en su
> carpeta y en su OneDrive sincronizado, en el sitio esperado y **sin ninguna
> carpeta nueva** (se elige un parte cuya ruta ya exista entera, según T2).»*
> **Qué la invalidó**: desde el 2026-09-23 el despliegue deja **abiertas por
> defecto** las dos ventanas (Posventa ya usa el servicio en real), y el humano
> decidió en T4 «Crear desde el principio». El primer parte archivado en
> Posventa será **el de quien archive primero**, no uno autorizado: el «parte
> autorizado único» ya no existe y R33 no lo promete. Lo que se conserva es la
> **comprobación con Posventa**, hecha a posteriori y el mismo día.

**R42. MANUAL.** Primera creación real de carpetas: Posventa queda **avisada
antes del despliegue** de que, desde ese momento, el sistema creará las
carpetas que falten (en la 0677: `VILLA 08` … `VILLA 15` según lleguen sus
partes —VILLA 12 y 13 tienen reclamaciones— y `PARTES FIRMADOS` dentro de
VILLA 04). El mismo día en que aparezca la primera (aviso en la respuesta y
línea `F-013 carpeta creada:` en el log, R40), el humano relanza el script de
R28 —solo lectura— para ver que esa unidad pasa a «resolvería», y comprueba
**con Posventa** que el nombre les sirve y que no ha aparecido ningún
duplicado. Si algo no les sirve: se cierra la ventana de archivo
(`infra/22_ventana_archivo.ps1 -Cerrar`, sin redesplegar), lo deshace una
persona (R43), se enmienda R36/R37 y solo entonces se vuelve a abrir.

> **Enmienda del 2026-09-24 · T4-3.** R42 decía, literal: *«Primer archivado
> real que **crea** carpetas (una unidad u obra sin carpeta ni parecida,
> elegida con el script de R28 que diga «se crearía: …»), autorizado
> expresamente y con Posventa **avisada antes**; comprobación con ellos de que
> el nombre creado les sirve y de que no ha aparecido ningún duplicado. Si no
> les sirve, lo deshace una persona (R43) y se enmienda R36/R37 antes de volver
> a crear.»* **Qué la invalidó**: la misma decisión. Con
> `SHAREPOINT_CREAR_CARPETAS` activo desde el primer despliegue y las ventanas
> abiertas, la primera creación la provoca el primer parte de una unidad sin
> carpeta, sin elegirlo nadie. El aviso a Posventa pasa de «antes de ese parte»
> a «antes del despliegue», y la comprobación, de «con ese parte» a «el día que
> ocurra». **Riesgo aceptado por el humano**: entre el despliegue y esa
> comprobación pueden crearse varias carpetas; lo contiene que la regla de
> creación está medida contra la obra piloto (R31) y que el freno es inmediato.

> **Enmienda del 2026-09-25 (F-049) · qué se creará en la 0677.** R42 decía,
> literal: *«(en la 0677: `VILLA 08` … `VILLA 15` según lleguen sus partes
> —VILLA 12 y 13 tienen reclamaciones—»*. **Qué lo invalidó**: la
> reorganización de Posventa que midió el 23 el 2026-09-25 (`VILLA 001` …
> `VILLA 007`, `VILLA 012`, `VILLA 013`) y la decisión del humano de ese día,
> «siempre con tres cifras». El aviso a Posventa pasa a ser: en la 0677 se
> crearán `VILLA 008` … `VILLA 011`, `VILLA 014` y `VILLA 015` según lleguen
> sus partes (sin reclamaciones cuando T3 las midió; las villas 12 y 13, que sí las tienen,
> ya tienen carpeta), y `PARTES FIRMADOS` dentro de las carpetas que no tengan
> hoja. El resto de R42 no cambia.

**R43. MANUAL / documental.** El sistema **no borra, no mueve ni renombra**
carpetas en ningún caso. `docs/INTEGRACION.md` debe llevar el procedimiento
para deshacer una carpeta creada por error —lo hace **una persona**: mueve el
PDF a la carpeta buena (dentro de la misma biblioteca el `item_id` de la traza
se conserva), y borra o renombra la carpeta sobrante; el borrado va a la
papelera del sitio y se propaga a los OneDrive sincronizados— y la consulta de
solo lectura que lista, desde `postventa.archivos`, los partes archivados en
una carpeta dada, para saber qué hay que mover antes de borrar.
