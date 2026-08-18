<!-- docs/referencia/02_parte_de_trabajo.md -->
# Anatomía del parte de trabajo escaneado

> Origen: `doc02871320260817093833.pdf`, primera remesa de partes firmados de
> Mirasierra, adjunta al correo de Ana Bello (Jefa de Posventa) del
> 2026-08-17. El PDF **no se versiona**: lleva datos personales de clientes.
> Fecha del documento original: escaneo del 2026-08-17; los partes se
> imprimieron el 2026-08-05.
> **Redactado**: no se reproduce aquí ningún nombre ni DNI de cliente.

Lo genera el propio Sigrid: el pie de página dice
`(RCP_Parte_de_Trabajos.xjs) Parte de Trabajo`. `RCP` es la reclamación, así
que el papel y la incidencia son el mismo objeto visto desde dos sitios.

## Estructura

**Un parte por página.** La remesa de ejemplo son 22 páginas = 22 partes, y
el pie de cada uno numera "Página 1". Un parte que ocupara dos hojas se
delataría con un "Página 2": esa es la señal para el troceado, no el conteo
de páginas.

Todos los de esta remesa son de la misma obra (`0677`) y la misma vivienda
(Villa 5), pero de incidencias, oficios y empresas distintos.

### Bloque impreso — «PROFESIONAL Y SERVICIOS ASIGNADOS»

| Campo | Ejemplo | Notas |
|---|---|---|
| Promoción | 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID) | Nombre comercial, a dos líneas |
| **Código Obra** | `0677` | El que da la carpeta de archivo |
| **Nº Incidencia** | `RS26.08/0123` | Con **barra**; en el nombre de fichero va con guion |
| Oficio | Ascensores, Mamparas, Albañilería, Piscina… | |
| Nº Referencia externo | *(vacío en toda la remesa)* | |
| Empresa | ORONA S.COOP, NESGUEL S.L., … | El industrial asignado |
| Cliente / Teléfono | *(vacíos en toda la remesa)* | Impresos pero sin dato |
| Vivienda | Viviendas Bloque Villa 5 | La unidad de posventa |
| Dirección Postal / Población | C/ … | Población vacía |
| Estancia | jardín, almacén… | |
| Descripción | «Sellado de encuentro de falsos techos de porches» | La descripción corta de la reclamación |

### Bloque manuscrito — «SERVICIO REALIZADO Y CONFORME»

| Campo | Qué trae en la práctica |
|---|---|
| **Observaciones de reparación** | Casi siempre vacío; **cuando trae algo, es decisivo** (ver abajo) |
| Fecha servicio, Hora inicio, Hora finalización | Vacíos en toda la remesa |
| **Conformidad de trabajos por el cliente** | La firma. Es lo único que aparece siempre |
| Fdo. / DNI (columna izquierda, cliente) | A veces rellenos a mano |
| Ficha personal técnico, Fdo. / DNI (columna derecha, técnico) | **Vacíos en toda la remesa**: el técnico no firma |

## Firma no es lo mismo que conformidad

En la remesa de ejemplo hay un parte —incidencia `RS26.08/0126`, reparación
del gresite del vaso de la piscina— **firmado por el cliente** y con esta
observación escrita a mano:

> «Se aprecia que se han hecho parcheados. No se reparó la totalidad»

Está firmado, y el trabajo **no** está conforme. Cerrar esa incidencia porque
"tiene firma humana" sería exactamente el error que este proyecto no puede
cometer: dar por resuelta una reparación que el cliente dice que no lo está.

De ahí la regla: **un parte con observaciones manuscritas nunca se cierra
solo**. Va a revisión manual, con el texto extraído delante de quien decide.

## Qué significa esto para la extracción

- El bloque impreso es siempre igual: se puede anclar por etiquetas.
- Lo manuscrito no es un extra: son las observaciones, el DNI y la firma.
- **No se pueden exigir campos que la realidad deja vacíos.** Fecha de
  servicio, horas, DNI o el nombre del cliente están en blanco en casi toda
  la remesa. Exigirlos mandaría a revisión manual el 100 % de los partes.
