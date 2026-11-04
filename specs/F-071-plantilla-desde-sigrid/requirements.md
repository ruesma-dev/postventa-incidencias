<!-- specs/F-071-plantilla-desde-sigrid/requirements.md -->
# F-071 · La plantilla de incidencias saca todos sus desplegables de Sigrid al descargarla — Requisitos

> **PENDIENTE DE APROBACIÓN DEL HUMANO.** Escrita el 2026-11-04 por el
> spec-author en la rama `feature/F-071-plantilla-desde-sigrid` (worktree
> `postventa-f071`, desde `feature/F-040-volcado-sigrid` en `d50fe9d`). Rigor
> **`critico`**, prioridad 1 (URGENTE). Solo `services/postventa-api` y los
> documentos.
>
> Los requisitos marcados **[D-n]** dependen de una decisión de `design.md`
> §13 y están escritos con la **opción recomendada**; las preguntas al humano,
> numeradas **Q-n**, están en `progress/spec_F-071.md`. Si el humano elige otra
> opción, el requisito cambia **antes** de empezar.
>
> **Absorbe F-058** (spec aprobada el 2026-10-09 en el worktree `postventa-f058`,
> nunca implementada): sus requisitos de ubicación dependiente pasan aquí con
> las decisiones que el humano ya tomó entonces (D-4: solo la versión nueva;
> Q-4: se rellena en Excel; Q-6: importación de prueba en producción
> autorizada; Q-7: Excel de escritorio y Excel web).
>
> Ejemplos siempre ficticios: obras `99NN`, unidades «Vivienda N»,
> ubicaciones «Estancia A-NN», oficios «Oficio ficticio N».

## 0 · De dónde sale

Petición del humano (2026-11-04, literal): «el excel que descarga debe extraer
TODAS las opciones de TODOS los desplegables de lo que hay en el momento en
sigrid. esta feature es urgente. lo mismo oficios, etc.»

Lo que pasa hoy en la obra 0677 (Mirasierra), con la plantilla v1 de F-036:

1. **Ubicación.** El desplegable sale de una **lista fija** versionada
   (`config/plantilla_incidencias.yaml`, 44 etiquetas, con «General (toda la
   unidad)» y «Otra (explicar en el detalle)» inventadas por nosotros), igual
   para todas las filas. La revisión de la bandeja (F-056) valida contra las
   ubicaciones de la **tipología de cada unidad** en Sigrid (`upv.obrtplide`
   → `prmtpl.ubica`). Quien rellena elige «Escalera» o «General» y la bandeja
   dice «La ubicación no está en la lista».
2. **Oficio.** El desplegable **agrupa** oficios casi iguales (R86, R92 de
   F-036, grupos confirmados en `oficios.html`). Cuando un grupo tiene varios
   códigos en la obra y el proveedor no desempata, la fila entra
   `oficio_ambiguo` y la bandeja pide «Elige el código del oficio: hay varios
   en la obra»: algo que el Excel ya debería haber decidido.

Lo que hay en Sigrid para cada desplegable (`azure-apps/sigrid_tablas.md`,
`azure-apps/sigrid_api.md` §8.9):

| Columna | En Sigrid | Hoy | Con F-071 |
|---|---|---|---|
| Unidad | `upv` de la obra | Sigrid, al descargar | igual |
| Ubicación | `prmtpl.ubica` de la tipología de cada unidad | lista fija del YAML | **Sigrid, por unidad** |
| Oficio | `obrofc` → `auxofc` de la obra, sin baja | Sigrid, agrupado | **Sigrid, un código por entrada** |
| Proveedor | `obrofc` de la obra con proveedor | Sigrid, por grupo de oficio | **Sigrid, una fila de `obrofc` por entrada** |
| Urgencia | **no hay catálogo**: `rcp.texurg` es texto libre de 32; la pasarela no lo admite y el volcado no lo manda (D-10 de F-059) | YAML | YAML [D-15, Q-2] |
| Listado | `auxtrcp` («Tipos de reclamación»); el volcado manda **siempre** `0002` (Q-1 de F-059) | YAML | YAML; el tipo de reclamación de punta a punta, ficha aparte [D-16, Q-3] |

## 0.1 · Glosario

- **Ubicaciones válidas de una unidad**: las de F-056 §16.3, sin cambiar
  nada: `leer_ubicaciones_validas` sobre `UbicacionesValidasPort`; por cada
  unidad del catálogo, una tupla en el orden de Sigrid (vacía si no tiene
  tipología o su tipología no tiene ubicaciones).
- **Lista de ubicaciones de la plantilla**: cada tupla **distinta** de
  ubicaciones válidas de la obra (dos unidades con la misma tupla, carácter a
  carácter y en el mismo orden, comparten lista).
- **Unión de la obra**: todas las ubicaciones válidas de sus unidades, sin
  repetidos exactos.
- **Desplegable dependiente**: la validación de `Ubicación` cuya lista depende
  de la `Unidad` de la misma fila (`design.md` §4).
- **Casado de F-060**: `ubicacion_de_sigrid` de F-060 (exacta; o la **única**
  de la lista con la misma clave NFC + recorte + `casefold`; nunca elige
  entre dos). F-071 lo usa, no escribe otra regla.
- **Opción de oficio**: una entrada del desplegable de `Oficio`, que es
  **un** código de oficio de `obrofc` de la obra.
- **Par**: una entrada del desplegable de `Proveedor`, que es **una** pareja
  (código de oficio, código de proveedor) de `obrofc` de la obra.
- **Plantilla v1 / v2**: la de `version` 1 en sus metadatos (F-036) o 2 (esta
  ficha).

## 1 · La plantilla

### 1.1 · Lo que se lee y cuándo

**R1.** CUANDO se pide `GET /api/plantilla?obra=` de una obra con catálogo
válido, el sistema debe leer de Sigrid **en ese momento**, sin caché entre
peticiones, el catálogo de la obra (`leer_catalogo`, como hoy) y, **después**
y **una sola vez**, las ubicaciones válidas de cada unidad con la lectura de
F-056 (`fuente_de_ubicaciones(construir_ubicaciones_validas(...))`).

**R2.** La generación de la plantilla no debe leer la base de datos: ni las
decisiones de equivalencia de oficios ni ninguna otra tabla. El borde de
`GET /api/plantilla` no construye `EquivalenciasPort`. [D-14]

**R3.** SI alguna de las dos lecturas llega al techo de filas, ENTONCES el
sistema debe responder **409** (`CatalogoSinVerificar`) sin fichero; SI falla
o no hay Sigrid, ENTONCES **503** (`CatalogoNoDisponible`) sin fichero. Los
mismos códigos y el mismo borde de hoy.

### 1.2 · Unidad

**R4.** El desplegable de `Unidad` no cambia: las unidades de posventa de la
obra en Sigrid con las etiquetas de `etiquetas_de_unidades` (F-036, R8).

### 1.3 · Ubicación (de F-058)

**R5.** El desplegable de `Ubicación` de cada fila de datos (filas 2 a 1001)
debe ofrecer **exactamente** las ubicaciones válidas de la unidad elegida en
`Unidad` en **esa misma fila**, con el texto exacto de Sigrid, en su orden, y
ninguna otra.

**R6.** MIENTRAS la `Unidad` de una fila esté vacía o no sea una etiqueta del
desplegable de unidades, el desplegable de `Ubicación` de esa fila no debe
ofrecer ninguna opción y su validación (estilo «detener») debe rechazar lo
tecleado.

**R7.** SI una unidad no tiene ubicaciones válidas, ENTONCES el desplegable de
`Ubicación` de sus filas no debe ofrecer nada y debe rechazar lo tecleado,
como en R6; la plantilla se genera igual. Si **ninguna** unidad tiene
ubicaciones, también se genera.

**R8.** Las unidades con la misma tupla de ubicaciones deben compartir **una**
lista en el libro; el libro no debe llevar ninguna lista de ubicaciones que no
sea la de alguna unidad, ni la unión de la obra como desplegable. Determinista:
el mismo catálogo y las mismas ubicaciones, en cualquier orden de llegada, dan
el mismo libro. [D-2]

**R9.** Las listas de ubicaciones y la tabla «unidad → lista» deben ir en
`_catalogos` (`veryHidden`, protegida), escritas **como texto** (R7 de F-036),
con un rango con nombre por lista y uno para la tabla; el libro no debe llevar
el rango `lista_ubicaciones` de F-036.

**R10.** La validación de `Ubicación` debe ser **una sola** regla de lista
para `B2:B1001`, con la fórmula de `design.md` §4.2 (o la de §4.3 si el
Bloque 0 la elige), de 255 caracteres como mucho, con los mensajes del YAML.
[D-1]

**R11.** El libro no debe ofrecer «General (toda la unidad)» ni «Otra
(explicar en el detalle)» en ningún sitio, ni ninguna ubicación que no venga
de Sigrid. [D-5]

### 1.4 · Oficio y proveedor, sin agrupar

**R12.** El desplegable de `Oficio` debe tener **una entrada por código de
oficio distinto** de `obrofc` de la obra (sin los dados de baja, como hoy la
lectura), ordenadas por código, **sin aplicar ningún grupo de equivalencia**
aunque haya decisiones «mismo» guardadas. [D-11, D-14]

**R13.** La etiqueta de cada opción de oficio debe ser
`<nombre> (<código>)`, con el nombre de Sigrid recortado; sin nombre, solo el
código. [D-11]

**R14.** El desplegable de `Proveedor` debe tener **una entrada por pareja
distinta** (código de oficio, código de proveedor) de `obrofc` de la obra con
proveedor, con la etiqueta `<etiqueta de la opción de oficio> · <nombre del
proveedor> (<código del proveedor>)` (sin nombre, solo el código), en el
orden de las opciones de oficio y, dentro de cada una, por nombre plegado y
código. Una fila de `obrofc` sin proveedor no da par; tampoco una de un oficio
que no está en el desplegable de `Oficio`. [D-12]

**R15.** Las etiquetas de `Oficio` deben ser distintas entre sí **plegadas**
(sin mayúsculas ni tildes, como compara Excel al teclear), y lo mismo las de
`Proveedor`. SI no lo fueran, ENTONCES `ValueError` sin generar el fichero
(defensa: con el código en la etiqueta no puede pasar con datos de Sigrid).

### 1.5 · Urgencia y listado

**R16.** Los desplegables de `Urgencia` y `Listado` siguen saliendo de
`config/plantilla_incidencias.yaml`, con los mismos códigos (`urgente`,
`seguridad`; `primero`, `segundo`), porque Sigrid no tiene catálogo de
urgencias y el tipo de reclamación no lo decide la bandeja (§0). La hoja
«Instrucciones» no debe decir que salen de Sigrid. [D-15, D-16]

### 1.6 · Versión, textos y tamaño

**R17.** Los metadatos de la plantilla generada deben llevar `version` **2**;
el identificador, la cabecera, las hojas, la protección y el aspecto de F-036
(R121–R126) no cambian. [D-7]

**R18.** El mensaje de entrada de `Ubicación` y la hoja «Instrucciones» deben
decir que la lista **depende de la unidad** (elegir primero la unidad; si se
cambia, volver a elegir la ubicación) y que, si el sitio no está, se deja en
blanco y se explica en «Detalle». Ningún texto de la plantilla debe nombrar
«General (toda la unidad)» ni «Otra (explicar en el detalle)», ni decir que el
oficio se elige «en la revisión».

**R19.** Los ejemplos de «Instrucciones» no deben llevar en `Ubicación`,
`Oficio` ni `Proveedor` un texto que pueda tomarse por un valor de Sigrid: un
texto indicativo («… (elígela de la lista de su unidad)»).

**R20.** Una plantilla generada para una obra grande —500 unidades, 50 listas
distintas de 60 ubicaciones de 48 caracteres, 200 oficios y 1.000 pares— debe
pasar entera por el lector de la importación (los topes de la lectura aislada
de F-036: 2 MiB, 500 entradas ZIP, 17 MiB descomprimido, 300.000 elementos
XML) y reconocerse como la plantilla.

## 2 · La configuración

**R21.** `config/plantilla_incidencias.yaml` no debe contener lista de
ubicaciones. SI el YAML trae la clave `ubicaciones`, ENTONCES su carga debe
fallar con `ConfiguracionPlantillaInvalida` y un motivo que diga que las
ubicaciones salen de Sigrid (F-071).

**R22.** `ListasCerradas` deja de tener ubicaciones: ni la plantilla, ni la
importación, ni el Excel de errores reciben otra lista de ubicaciones que la
leída de Sigrid en la petición.

## 3 · La importación

### 3.1 · Versión y lecturas

**R23.** SI el fichero subido es una plantilla **v1**, ENTONCES el sistema
debe rechazarlo **entero** (400) con el código `version_anterior` y el motivo
«Esta plantilla es de una versión anterior: sus listas ya no son las de
Sigrid. Descarga una nueva desde el portal y copia en ella tus filas.», sin
leer Sigrid ni escribir nada. Una versión distinta de 1 y 2 sigue siendo
`version_no_soportada`. [D-4]

**R24.** CUANDO se importa una plantilla v2 no ya importada, el sistema debe
leer de Sigrid el catálogo y, **después** y **una sola vez**, las ubicaciones
válidas de cada unidad. SI el fichero no es la plantilla o ya estaba importado
(atajo de R39 de F-036), ENTONCES no debe leer ninguna de las dos. La
importación no debe leer las decisiones de equivalencia. [D-14]

**R25.** SI alguna lectura de la importación llega al techo, ENTONCES **409**
sin registrar nada; SI falla, **503** sin registrar nada. Ni importación, ni
filas, ni Excel de errores.

### 3.2 · Ubicación (de F-058)

**R26.** Una `Ubicación` vacía (o solo blancos) sigue siendo válida, sin
error ni aviso (opcional al importar; F-056 la exige al aprobar).

**R27.** CUANDO la `Ubicación` de una fila con unidad válida es
**exactamente** una de las ubicaciones válidas de esa unidad, la incidencia
debe guardarse con ese texto, sin aviso.

**R28.** CUANDO la `Ubicación` de una fila con unidad válida no es exacta pero
el casado de F-060 la casa con **una** de las de esa unidad, la incidencia debe
guardarse con **el texto exacto de Sigrid** y la fila debe llevar el aviso
«la ubicación se ha ajustado al texto de Sigrid: «<de Sigrid>»». [D-3]

**R29.** SI la `Ubicación` de una fila con unidad válida no casa (ni R27 ni
R28) con las de esa unidad, ENTONCES la fila debe volver con error en
`Ubicación` y el motivo `UBICACION_FUERA_DE_LA_UNIDAD` (`design.md` §5.4).

**R30.** SI la unidad de una fila válida no tiene ubicaciones y la `Ubicación`
no está vacía, ENTONCES error en `Ubicación` con `UNIDAD_SIN_UBICACIONES`.

**R31.** SI la `Unidad` de una fila falta o no es válida y la `Ubicación` no
está vacía, ENTONCES se compara con la **unión de la obra** (R27 y R28 contra
la unión): si no casa, error `UBICACION_FUERA_DE_LA_OBRA`; si casa, ningún
error de `Ubicación`. [D-8]

### 3.3 · Oficio y proveedor, resueltos

**R32.** CUANDO el `Oficio` de una fila casa con una opción de oficio, la
incidencia debe guardarse con **su código** y, como nombre, el **nombre de
Sigrid** (no la etiqueta del desplegable), con `oficio_ambiguo = false`.

**R33.** CUANDO el `Proveedor` de una fila casa con un par, la incidencia debe
guardarse con el código de proveedor del par y su nombre de Sigrid, y con el
oficio **del par**, con `proveedor_ambiguo = false` y `oficio_ambiguo =
false`; si `Oficio` está vacío, el oficio es el del par (D-17 de F-036).

**R34.** SI `Oficio` y `Proveedor` casan y el oficio del par no es el
elegido en `Oficio`, ENTONCES error en `Proveedor` con
`PROVEEDOR_DE_OTRO_OFICIO` (como hoy).

**R35.** Ninguna incidencia de una plantilla v2 debe entrar en la bandeja con
`oficio_ambiguo` ni `proveedor_ambiguo` a `true`.

### 3.4 · Las demás columnas tasadas

**R36.** En `Unidad`, `Oficio`, `Proveedor`, `Urgencia` y `Listado`, un valor
que no es exacto pero casa con **una sola** opción de su desplegable por la
clave del casado de F-060 (NFC, recorte, `casefold`) debe aceptarse como esa
opción, con el aviso «<columna>: se ha tomado «<opción>»»; con dos o más, o
con ninguna, es el error de lista de siempre. Excel acepta lo tecleado sin
mirar mayúsculas: la importación no rechaza lo que el Excel dio por bueno.
[D-17]

**R37.** SI un valor de `Unidad`, `Oficio` o `Proveedor` no casa con las
opciones **de Sigrid en el momento de importar** (por ejemplo, un proveedor
que ya no está en la obra desde que se descargó la plantilla), ENTONCES la
fila debe volver con error en esa columna y un motivo que diga que el valor ya
no está en Sigrid para esa obra y que se elija del desplegable del Excel de
errores, que sale con las listas de ese momento.

**R38.** Una fórmula, una fecha, un booleano o un número en una columna
tasada siguen dando los errores de F-036 (`FORMULA`, `FECHA_EN_TASADA`,
`NUMERO_EN_TASADA`), sin compararlos con ninguna lista.

**R39.** Todas las columnas de una fila se siguen validando aunque falle una
(R33 de F-036), y el orden de los errores de la fila es el de las columnas.

### 3.5 · El Excel de errores y los duplicados

**R40.** El Excel de errores debe generarse con **el mismo** catálogo y **las
mismas** ubicaciones leídos en esa importación (sin otra lectura), en
`version` 2, con los desplegables de R5–R15, y con los valores de cada fila
**tal como llegaron**.

**R41.** La clave de duplicado no cambia: reimportar una fila que ya está en
la bandeja con la ubicación en otras mayúsculas sigue siendo `ya_en_bandeja`.

## 4 · Lo que no hace

**R42.** Nada de F-071 escribe en Sigrid: solo `POST /api/sql/read`, con las
tres lecturas que ya existen (unidades, oficios de la obra, ubicaciones de las
unidades) y **ninguna consulta nueva**. Ningún endpoint nuevo, ninguna
variable de entorno, ninguna dependencia, ningún DDL.

**R43.** F-071 no cambia la bandeja ni sus tablas (`bandeja_incidencias`,
`importaciones`, `revisiones_bandeja`), ni la revisión
(`domain/models/revision.py`, `application/pipelines/revision.py`,
`interface_adapters/api/revision.py`), ni el volcado (F-059/F-040), ni las
equivalencias (`domain/models/equivalencias.py`,
`application/pipelines/equivalencias.py`, `postventa.decisiones_equivalencia`,
`oficios.html` y sus dos rutas), ni `services/postventa-front/`. Las filas ya
importadas con `oficio_ambiguo` se siguen resolviendo en la bandeja como hoy.
[D-18]

**R44.** Ni el texto de `prmtpl.ubica`, ni una ubicación, ni un nombre de
unidad, oficio o proveedor deben ir a un log. Los logs de la plantilla y de la
importación añaden solo recuentos (listas de ubicaciones distintas, unidades
sin ubicaciones, opciones de oficio, pares).

**R45.** El script de migración de F-036 (`scripts/migrar_excel_f036.py`,
`scripts/migracion_f036.py`, `scripts/migracion_f036_correcciones.yaml`) y sus
tests se **retiran**, con constancia en `docs/ARCHITECTURE.md` de que
cumplieron y del commit en que quedan. [D-6]

## 5 · Documentación y verificación

**R46.** `docs/ARCHITECTURE.md` («La plantilla», «La importación», «La
agrupación de oficios casi duplicados», «Dónde vive cada pieza», «Lo que no
hace la revisión») y `docs/INTEGRACION.md` (§1 y lo que dice de la lista
cerrada de ubicaciones y de los grupos en la plantilla) deben decir que todos
los desplegables de la plantilla salen de Sigrid salvo urgencia y listado, que
la ubicación depende de la unidad, que el oficio y el proveedor van por código
y que los grupos de equivalencia ya no se aplican a la plantilla.
`azure-apps/postventa_incidencias.md` lo mismo, **por el líder al
desplegar**. Un test de documentación lo fija.

**R47.** Verificación en producción, **MANUAL (humano)**, en la obra 0677:
la plantilla se descarga; dos unidades de tipologías distintas enseñan listas
distintas, cada una con tantas entradas como su tipología en
`GET /api/revision` (`catalogo.ubicaciones`); una fila sin unidad no ofrece
ninguna; el desplegable de `Oficio` tiene tantas entradas como oficios
distintos de la obra en `catalogo.oficios` de esa misma respuesta, cada una
con su código; y una importación de prueba (autorizada en F-058 Q-6; el humano
la reconfirma, Q-10) con una fila de ubicación de otra unidad la devuelve en
el Excel de errores con `UBICACION_FUERA_DE_LA_UNIDAD`, y una fila buena con
oficio y proveedor entra sin `oficio_ambiguo` y se descarta en la bandeja.
