<!-- specs/F-013-archivo-posventa/requirements.md -->
# F-013 · Mudar el archivo a la biblioteca de Posventa — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f013_rN_*`, salvo los marcados **MANUAL**, que se
> verifican a mano por el humano y tienen su comando en `tasks.md`.
>
> **Rigor propuesto: `critico`** (hoy la ficha dice `estandar`). Motivo en
> `design.md` §0.3: esta feature pasa a escribir en la **biblioteca real de
> negocio** de Posventa, sincronizada por OneDrive en sus equipos, con PDFs que
> llevan el **DNI manuscrito** de clientes, y el fallo típico —el parte en la
> carpeta de otra vivienda u otra obra— **no se ve** desde nuestro lado. Es la
> misma clase de riesgo por la que F-006 se hizo `critico`. **Lo decide el
> humano** (decisión abierta D-R en `design.md` §9).
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
| **H3** | «PARTES FIRMADOS (sistema)» como carpeta base de la estructura propia: con la estructura de Posventa probablemente no aplica. **Se deja abierto** | Decisión abierta **D-1**, `design.md` §9; R17 |
| **H4** | **Lo ya archivado en IT se queda en IT**, sin migración, y se documenta que sigue allí | R24–R26 |

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
las existentes; la lectura de la ubicación de la reclamación en Sigrid (solo
lectura, por `sigrid-api`); el estado de «destino no resuelto» con su motivo;
el script de solo lectura que resuelve sitio y biblioteca desde la URL y
comprueba permisos; y la documentación.

**No entra**, y cada cosa tiene su dueña:

| Fuera | Por qué | Dónde |
|---|---|---|
| Activar la capa L1 contra el duplicado | Es un defecto propio con su ficha; F-013 **depende** de él | **F-033** (D-2, `design.md` §8.1) |
| Que carpeta y nombre salgan de lo persistido y no del cuerpo | Ficha propia, toca el front | **F-031** (D-3, `design.md` §8.2) |
| Recortar permisos a `Sites.Selected` y conceder el sitio de Posventa | Lo ejecuta el humano en el tenant | **F-018** (se le anota, T-doc) |
| Migrar lo archivado en IT | Decisión H4 | — |
| Crear carpetas de obra o de unidad | Son de Posventa (D-4) | — |
| Pintar la cola de «destino no resuelto» en el front | Es circuito de front | propuesta de ficha nueva (D-5) |

## Vocabulario

| Término | Qué es |
|---|---|
| **Estrategia de destino** | Cómo se compone la carpeta: `por_obra` (F-006: `<base>/<cod obra>`) o `posventa` (F-013). Configuración `SHAREPOINT_ESTRUCTURA` |
| **Carpeta de obra** | La carpeta de primer nivel bajo la base cuyo nombre es `<cod obra>` seguido de un blanco y el nombre de la obra. La crea Posventa |
| **Carpeta de unidad** | La carpeta bajo `<obra>/PARTES INCIDENCIAS/` de una unidad de posventa (`VILLA 05`). La crea Posventa |
| **Hoja** | `PARTES FIRMADOS`, la carpeta final dentro de la unidad |
| **Ubicación de la reclamación** | Lo que Sigrid dice de la reclamación: código de la obra y código y nombre de su **unidad de posventa** (`rcp.upvide → upv`, y `upv.obride → obr`), leído por `sigrid-api` |
| **Clave de unidad** | La forma canónica con la que se compara una unidad: mayúsculas, sin tildes, blancos colapsados y **los números comparados como enteros** (`05` = `5`) — ver `design.md` §4.3 |
| **Destino no resuelto** | Resultado del archivado que **no sube nada** porque la carpeta de obra o de unidad no existe o no es única. Lleva motivo y candidatas |

---

## 1 · El destino es configuración

**R1.** El sistema debe leer de configuración la estrategia de destino
(`SHAREPOINT_ESTRUCTURA`, valores `por_obra` y `posventa`) y los nombres
literales de los dos tramos fijos de la estructura de Posventa
(`SHAREPOINT_CARPETA_INCIDENCIAS`, por omisión `PARTES INCIDENCIAS`, y
`SHAREPOINT_CARPETA_FIRMADOS`, por omisión `PARTES FIRMADOS`). Cambiar de
estrategia o de nombres **no debe tocar** el dominio, la aplicación ni el
pipeline (criterio de aceptación 1 de la ficha).

**R2.** MIENTRAS `SHAREPOINT_ESTRUCTURA` valga `por_obra` —que es el valor por
omisión— y la base no esté vacía (R17), el sistema debe componer la carpeta y
el nombre **exactamente** como hoy (F-006 R1–R12), sin llamar a Sigrid ni listar ninguna carpeta. Los tests
de F-006 siguen en verde sin tocarlos.

**R3.** SI `SHAREPOINT_ESTRUCTURA` trae un valor que no es ninguno de los dos,
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
(en forma de ERP, `RS26.08/0123`): código de obra, código y nombre de la
unidad de posventa. Una sola consulta parametrizada, acotada por el tipo de
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

**R9.** El sistema no debe usar el nombre de la obra de Sigrid ni el campo
`unidad` extraído del papel para **componer** ninguna carpeta: solo para
**casar** con las existentes (R10–R14). Un test lo fija con los dos ejemplos
medidos del apartado «Por qué».

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

**R13.** SI hay **cero** candidatas a carpeta de obra, ENTONCES «destino no
resuelto», motivo `obra_sin_carpeta`. SI hay **más de una**, motivo
`obra_carpeta_ambigua`, con los nombres de las candidatas en el resultado.

**R14.** SI no existe `<carpeta de obra>/<INCIDENCIAS>`, ENTONCES «destino no
resuelto», motivo `sin_carpeta_incidencias`. SI hay **cero** candidatas a
carpeta de unidad, motivo `unidad_sin_carpeta`; SI hay **más de una**,
`unidad_carpeta_ambigua`, con las candidatas.

**R15.** El sistema **no debe crear nunca** la carpeta de obra, la de
`INCIDENCIAS` ni la de unidad. La única carpeta que puede crear es la hoja
`<FIRMADOS>` dentro de una carpeta de unidad **ya existente**, y solo DONDE
`SHAREPOINT_CREAR_HOJA` esté encendido (decisión abierta D-4; por omisión,
encendido). Crear la hoja no puede crear, como efecto lateral, ninguna carpeta
intermedia: si el padre no existe, falla.

**R16.** SI la hoja no existe y `SHAREPOINT_CREAR_HOJA` está apagado,
ENTONCES «destino no resuelto», motivo `sin_carpeta_firmados`.

## 5 · La carpeta base

**R17.** El sistema debe admitir una `SHAREPOINT_CARPETA_BASE` **vacía** como
«raíz de la biblioteca», sin producir rutas con barra inicial ni tramos vacíos
(`/0677 ...` o `//`). En la estrategia `por_obra`, en cambio, una base vacía
pasa a ser un **error de configuración** (`ConfiguracionSharePointIncompleta`,
como R3): hoy produce la ruta `/0677`, y dejaría las carpetas por código de
F-006 sueltas en la raíz de la biblioteca de Posventa, mezcladas con las suyas.

## 6 · El destino no resuelto

**R18.** CUANDO el destino no se resuelve, el sistema **no debe** pedir la
subida ni crear ninguna carpeta, y debe dejar la traza de archivo en estado
`error` con el motivo **en forma de código** (los de R7, R8, R13, R14, R16),
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
para cada unidad, si la regla de casado de R11 la resolvería. Es la
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
identificadores**, qué unidades resuelve la regla y cuáles no.

**R32. MANUAL.** La medición de la ubicación en Sigrid (`design.md` §4.2): qué
devuelven `con.cod` y `con.res` de las unidades de posventa de la obra piloto.
Sin ella, la regla de casado de R11 está **[NO MEDIDA]** contra el ERP.

**R33. MANUAL.** Primer archivado real en la biblioteca de Posventa, con un
parte **autorizado expresamente** por el humano, y comprobación con Posventa de
que el fichero aparece en su carpeta y en su OneDrive sincronizado, en el sitio
esperado y sin carpetas nuevas salvo, como mucho, la hoja.
