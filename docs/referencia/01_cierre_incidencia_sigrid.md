<!-- docs/referencia/01_cierre_incidencia_sigrid.md -->
# Cómo cierra Posventa una incidencia en Sigrid

> Origen: `PASOS CERRAR INCIDENCIA.docx`, de Alicia Echevarría (Arquitecta
> Técnica, Posventa), adjunto a su correo del 2026-08-18. Convertido con
> `markitdown`; las capturas se han leído una a una y su contenido está
> volcado en este documento.
> Fecha del documento original: 2026-08-18.
> **Redactado**: se han sustituido por marcadores el nombre del propietario y
> el nombre del servidor interno de Sigrid que aparecían en las capturas.

El modelo de datos (tablas `rcp`, `upv`, `gra`, `rcg`, `con`, `conest`) **no
se copia aquí**: vive en `azure-apps/sigrid_tablas.md` y
`azure-apps/sigrid_api.md` §9. Esto es solo el procedimiento de negocio y lo
que enseñan las pantallas.

## El procedimiento, tal y como lo hace Posventa

1. **Renombrar el parte**: `RS26.08 – 0123 PARTE FIRMADO`.
2. **Subirlo a Sigrid**: obra → unidad de obra → buscar la incidencia →
   entrar → botón de **gráficos** → **Importa → Importar desde archivo…** →
   elegir el PDF → rellenar dos campos (abajo) → cerrar la ventana.
3. **Cerrar**: en la ficha de la reclamación, menú **Procesos → 3. Cerrar
   parte**, y aceptar el mensaje de confirmación.

La incidencia también se puede localizar por la pestaña **Post-Venta →
Reclamaciones** de la obra, sin entrar en la unidad.

**De dónde sale el fichero.** La guía cita la ruta real desde la que Posventa
importa el parte, y muestra la estructura de carpetas en la que hoy vive:
`…677 MIRASIERRA\PARTES INCIDENCIAS\VILLA 05\PARTES FIRMADOS`, es decir
**obra → «PARTES INCIDENCIAS» → unidad (villa) → «PARTES FIRMADOS»**.

## Lo que se rellena al importar el gráfico

Ventana *"Ventana de Gráficos / Documentos asociados al concepto"*. De todos
sus campos, Posventa solo rellena **dos** (los subrayados en la guía):

| Campo de la pantalla | Valor | Campo probable en `gra` |
|---|---|---|
| **Descripción** | `PARTE FIRMADO` | `res` |
| **Tipo gráfico / documento** | `PV002` — `POSTVENTA:Fotos Reparaciones` | `gratipide` → `auxgra` |

El resto lo pone Sigrid solo: **Código** (`20260818140392614.aechevarria`,
sello de tiempo + usuario), **Archivo / Ubicación / URL** (el nombre del
fichero, `RS26.08 - 0123 PARTE FIRMADO.pdf`), **Fecha de incorporación al
sistema**, **Usuario**. Quedan vacíos *Clave*, *Estado asociado*, *Revisión*
y *Descripción larga*.

El documento aparece como `[INCRUSTADO EXTERNO]`, cargado desde una carpeta
temporal del servidor de aplicación. El menú *Importa* ofrece dos vías:
**Importar desde archivo…** y **Asociar URL de Internet…** — la segunda es
relevante para nosotros, porque permitiría referenciar el PDF ya archivado en
SharePoint en lugar de incrustar el binario.

## La ficha de la reclamación

Cabecera: `04/08/2026 · RS26.08/0123 · Sellado de encuentro de falsos techos
de porches`, y el estado a la derecha: **`3 (PTE : PENDIENTE)`** — es decir
`con.est = 3`, con `conest.cod = PTE` y `conest.res = PENDIENTE`.

**Ojo con el formato del código**: en Sigrid la incidencia se escribe
`RS26.08/0123` (con barra); en el nombre del fichero, `RS26.08 - 0123`.

Campos de *Identificación*:

| Pantalla | Valor de ejemplo |
|---|---|
| Obra | `0677` — 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID) |
| Unidad Post-Venta | `0677.03VILLA 5` — Viviendas Bloque Villa 5 |
| Tipo de reclamación | `0002` — PRIMER LISTADO POSTVENTA |
| Ubicación | `jardín` (desplegable) |
| Propietario | `0677_REF/0004` — *(nombre redactado)* |
| Persona que realiza la reclamación | `0677_PER/0004` — *(nombre redactado)* |
| Correo adicional para avisos, Teléfonos de avisos | vacíos |

Campos de *Datos de la reclamación*: fecha y hora (`04/08/2026 9:33:10`),
**Clase de reclamación** `0001` Vicios o defectos, **Oficio** `0039`
Ascensores, **Parte comunicado de forma** `Verbal`, Urgencia y Motivo
(vacíos), Fecha prevista de nueva visita, **Descripción corta del problema** y
Descripción del problema.

Pestañas de la ficha: *Detalle*, *Intervinientes*, *Seguimiento*, *MOTIVOS
RECHAZO*.

## El menú Procesos

| Opción | |
|---|---|
| 1 | Pasar a terminada |
| 2 | Rechazar reclamación (envía email) |
| **3** | **Cerrar parte** ← la que usa Posventa |
| 4 | Crear Reparaciones a Intervinientes |
| 5 | Rechazar reclamación (NO enviar email) |
| **6** | **Cerrar parte sin archivo (RPV)** |

## Lo más importante de todo: qué comprueba «Cerrar parte»

El mensaje de confirmación del proceso dice, literalmente:

> **Cerrar parte**
> Este proceso cambiará el estado de las Reclamaciones (1) a estado: **CERRADA**
> **Comprobando:**
> - Que la Reclamación tenga asociado algún gráfico o Doc. multimedia.

Es decir: **Sigrid no deja cerrar una incidencia que no tenga documento
adjunto**. Por eso existe la opción 6, "Cerrar parte sin archivo (RPV)".

Consecuencias para nosotros:

- Un `UPDATE con.est` directo **se saltaría esa comprobación**: dejaría la
  incidencia cerrada sin parte, que es justo lo que el ERP impide a mano.
- «Cerrar parte» es un **proceso** del ERP, no un simple cambio de campo. No
  consta qué más hace (seguimiento, avisos, fechas). Antes de replicarlo por
  SQL hay que verificar en una incidencia real qué filas toca.

> **Esa última duda ya está resuelta**, y no por deducción: F-008 la midió
> contra el ERP. «Cerrar parte» escribe **`con.est` y una fila en `dbo.log`,
> nada más** — ni seguimiento, ni actuaciones, ni fechas. El detalle, con la
> forma exacta de la fila de log, está en `03_modelo_posventa_sigrid.md` §2.

## Anexo de la guía: cómo nombrar y dónde guardar el parte

La autora deja una **cuestión abierta**, con sus palabras: le resulta más fácil
buscar la incidencia entrando en la vivienda, pero también se puede llegar por
la pestaña de reclamaciones; y por eso duda entre **renombrar el fichero con el
nombre de la vivienda más el de la incidencia** o seguir como hasta ahora —solo
el nombre de la incidencia, y cada parte en la carpeta de su vivienda—.

No afecta al cierre en Sigrid, que localiza la reclamación por su código. Afecta
a **cómo se nombra y archiva el PDF**, así que es materia de la feature de
archivo en SharePoint, no de F-009. Queda anotada aquí para que quien la aborde
no la reinvente: es una pregunta del negocio, todavía sin responder.
