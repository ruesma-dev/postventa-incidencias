<!-- docs/referencia/04_alta_incidencia_sigrid.md -->
# Cómo da de alta Posventa una incidencia en Sigrid

> Origen: `PASOS CREAR PARTE.docx`, de Alicia Echevarría (Posventa) · Fecha del documento: 2026-09-24
> Convertido a Markdown el 2026-09-24 con la herramienta MCP `markitdown`.
> El original vive fuera del repositorio.
> `markitdown` no convierte las capturas: las seis se han leído una a una y lo
> que enseñan está volcado en este documento.

> **Redactado.** Se han quitado los nombres del propietario y de la persona que
> reclama que salían en la ficha del parte, y los nombres de las empresas de
> las listas de proveedores. Quedan los códigos, que es lo que el volcado
> necesita.

El modelo de datos (`con`, `rcp`, `rcpint`, `upv`…) **no se copia aquí**: vive
en `azure-apps/sigrid_tablas.md` y `azure-apps/sigrid_api.md`. Lo confirmado
contra el ERP sobre posventa está en `03_modelo_posventa_sigrid.md`. Esto es
solo el procedimiento de negocio y lo que enseñan las pantallas.

Es el proceso **manual** que el volcado masivo (F-040) tiene que replicar,
fila a fila, a partir del Excel importado (F-036).

## El texto del documento

> Entras dentro de la unidad de postventa donde vas a crear el parte, en el
> apartado de reclamaciones pulsas nueva.
>
> Te salen estas ventanas. La primera la aceptas en reclamaciones postventa y
> en la segunda escribes en descripción el resumen de la incidencia.
>
> Te salta el cuadro de la incidencia, yo al ser del primer listado de
> incidencias cambio el tipo de reclamación que por defecto sale 3 a 2.
>
> Le pongo oficio poniendo un \* en la casilla pequeña y sale un desplegable
> con los posibles oficios. Eliges el que sea según la incidencia.
>
> Y después en la pestaña intervinientes: pulsas en añadir y te sale otro
> desplegable con las empresas. Eliges la que corresponda y aceptas.

## Paso a paso, con lo que enseñan las capturas

### 1 · Ficha de la unidad de posventa → pestaña «Reclamaciones» → «Nueva»

La ficha es `Ficha : Unidad de Post-Venta`. La cabecera lleva el código de la
unidad y su descripción (en la captura, de otra obra: `0592.1-2-C · Portal B 1
Piso 2 Letra C`) y el estado de la unidad (`1 (PRE : EN PREVENTA)`). La
pestaña «Reclamaciones» lista las de la unidad con las columnas Código,
Descripción, Descripción del problema, Tipología (`PRIMER LISTADO POS…`),
Oficio, Fecha y hora de reclamación y Cód. estado (`PTE`). Debajo, el botón
**Nueva**.

### 2 · Serie y descripción

- **Selección de Series : PARTE DE RECLAMACIÓN**, con dos series:
  - `RS<año2>.<mes>/` → **Reclamaciones postventa** ← la que se elige;
  - `RP<año2>.<mes>/` → Reclamaciones Preventa.
- **Nuevo : PARTE DE RECLAMACIÓN** (serie `RS<año2>.<mes>/`): Fecha (la del
  día), **Código** que propone Sigrid (en la captura `RS21.01/1051`) y
  **Descripción**, que escribe el usuario. Aceptar crea el parte.

El código **lo pone Sigrid** al crear: serie del mes más un correlativo. El
volcado no lo inventa; lo recibe de vuelta.

### 3 · Ficha del parte, pestaña «Detalle»

Cabecera: `04/08/2026 · RS26.08/0169 · Descuadre en interior de…` y el estado
**`3 (PTE : PENDIENTE)`**. Pestañas: Detalle, Intervinientes, Seguimiento y
Motivos rechazo.

**Identificación**

| Campo | Ejemplo de la captura | Nota |
|---|---|---|
| Obra | `0677` · 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID) | Heredado de la unidad |
| Unidad Post-Venta | `0677.03VILLA 1.` · Viviendas Bloque Villa 1 | Heredado de la unidad |
| **Tipo de reclamación** | `0002` · PRIMER LISTADO POSTVENTA | Sale **3** por defecto; Alicia lo cambia a **2** «al ser del primer listado». Qué es el 3 y cuándo se deja: **sin confirmar** |
| Ubicación | `dormitorio 1` | Desplegable |
| Propietario | `0677_REF/0001` · *(nombre redactado)* | Código `<obra>_REF/NNNN` |
| Persona que realiza la reclamación | `0677_PER/0001` · *(nombre redactado)* | Código `<obra>_PER/NNNN` |
| Correo adicional para avisos | vacío | |
| Teléfonos de avisos | vacío | |

**Datos de la reclamación**

| Campo | Ejemplo de la captura | Nota |
|---|---|---|
| Fecha y hora de reclamación | `04/08/2026 10:41:29` | |
| Clase de reclamación | vacío | |
| **Oficio** | `0143` · Carpintería de madera | Se busca con `*` en la casilla: abre el catálogo |
| Parte comunicado de forma | `Escrita` | Desplegable |
| Urgencia / Motivo | vacíos | |
| Fecha prevista de nueva visita | vacío | |
| Descripción corta del problema | `Descuadre en interior de armario` | |
| Descripción del problema | `Descuadre en interior de armario` | Texto largo |

### 4 · El catálogo de oficios

`Selección de: Oficios (*)`: **130 oficios**, con Código y Resumen (por
ejemplo `0005` Carpintería PVC, `0011` Electricidad, `0021`
Impermeabilizaciones, `0024` Jardinería). Es un catálogo **general**, no de la
obra.

### 5 · Pestaña «Intervinientes» → «Añadir»

- La pestaña lista los intervinientes del parte: **Oficio**, Descripción
  oficio, **Proveedor** (código), Nombre del proveedor y una casilla
  **Causante**. En el ejemplo hay dos: `0046` y `0143`, los dos
  «Carpintería de madera» con proveedores distintos.
- «Añadir» abre **`MULTIPLE: Seleccione el oficio de la obra`** (se pueden
  elegir varios con Control + clic): **los oficios de ESA obra, cada uno con
  su proveedor** (Tipo, Oficio, Des, Proveedor, Nom, Comentario). En la 0677
  son **39**.

**Esto importa para F-039**: la lista de oficio y proveedor de la obra es lo que
Sigrid ofrece para elegir el industrial, y encaja con el criterio del humano
(«los industriales que han hecho ese trabajo en esa obra»). Qué tabla la guarda
está por medir.

## Lo que queda abierto

1. **Tipo de reclamación 2 frente a 3.** El 2 es «PRIMER LISTADO POSTVENTA»; el
   3 es el valor por defecto. Falta saber qué es el 3 y qué regla decide.
2. **Qué tablas escribe Sigrid** al dar de alta: la reserva del código de la
   serie, `con` y `rcp`, los intervinientes (`rcpint`) y el estado inicial. Se
   mide contra el ERP al especificar F-040, no se supone.
3. **Qué oficio lleva el parte** cuando hay varios intervinientes (en el
   ejemplo el parte lleva `0143` y los intervinientes `0046` y `0143`), y quién
   marca «Causante».
4. **Propietario y persona que reclama**: de dónde salen para cada unidad en un
   alta masiva.
