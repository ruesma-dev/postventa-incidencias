<!-- docs/referencia/05_excel_creacion_incidencias.md -->
# Excel de creación de incidencias: el formato de hoy (muestra)

> **Origen**: `creacion_incidencias.xlsx`, OneDrive del humano
> (`Documentos/postventa`), recibido el 2026-09-28 para F-036. Convertido con
> la herramienta MCP `markitdown` el 2026-09-28; el `.xlsx` original **no** se
> versiona. Sin datos personales: solo unidad, estancia, defecto y oficio.
>
> **Es la muestra del formato ACTUAL, no el contrato.** Por decisión del
> humano (2026-09-28), F-036 diseña una plantilla nueva, generada por obra
> desde el portal, y el importador **solo** acepta esa plantilla; este Excel
> se migra una vez a ella. Se conserva aquí para saber de dónde se parte.

## Cómo leer la conversión

`markitdown` toma la primera fila como cabecera, pero el Excel **no tiene
cabecera**: la fila «Villa 1 | … | Choca ventana con ascensor | Carpintería de
aluminio» es la primera incidencia. Lo que se ve en el fichero:

| Columna | Contenido |
|---|---|
| A | La unidad (`Villa 1`), escrita **solo en la primera fila**; el resto hereda hacia abajo. |
| B, C | Vacías. |
| D | Ubicación, texto libre e irregular (`DORMITORIO BAÑO 1` junto a `DORMITORIO 1 BAÑO`; `GENERALES` para toda la unidad). |
| E | Descripción, texto libre: varias pasan de los 128 caracteres de `con.res`, algunas mezclan dos defectos, otras remiten a otras filas («como en los otros baños») y la urgencia va en mayúsculas dentro del texto («PELIGRO DE SEGURIDAD»). Una celda trae un salto de línea. |
| F | Oficio **por nombre**, no por código; solo lo traen las primeras filas. |

La obra no aparece en el fichero. El mismo texto se repite con distinta
ubicación («Miras de hierro…», «Mejorar uniones de albardillas…»), y es
legítimo: no son duplicados.

## Conversión íntegra de `markitdown`

## Hoja1
| Villa 1 | Unnamed: 1 | Unnamed: 2 | SALA/ ESTUDIO | Choca ventana con ascensor | Carpintería de aluminio |
| --- | --- | --- | --- | --- | --- |
| NaN | NaN | NaN | SALA/ ESTUDIO | Reahacer inglentes azulejos baño, son cortantes y mal ejecutados. | Solados y alicatados |
| NaN | NaN | NaN | SALA/ ESTUDIO | Pintar y lijar de nuevo paredes de cuarto de baño , mal remate con encuentro azulejos. | Pintura |
| NaN | NaN | NaN | SALA/ ESTUDIO | Se mueve la parte fija de la mampara, PELIGRO DE SEGURIDAD. | Mamparas |
| NaN | NaN | NaN | SALA/ ESTUDIO | Rematar agujero en pared ,  azulejo con escudo sifon | Albañilería |
| NaN | NaN | NaN | SALA/ ESTUDIO | Miras de hierro que son de soporte de encimera estan oxidadas, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD. | Mobiliario cocina |
| NaN | NaN | NaN | SALA/ ESTUDIO | Enlechar azulejos ducha | Solados y alicatados |
| NaN | NaN | NaN | SALA/ ESTUDIO | Remate de rodapie junto a puerta del baño | Carpintería de madera |
| NaN | NaN | NaN | SALA/ ESTUDIO | REHACER  el rodapie Y SUELO PORCELANICO inacabado en la puerta de salida a la terraza | Solados y alicatados |
| NaN | NaN | NaN | SALA/ ESTUDIO | Rematar azulejos entre mampara e inodoro | Solados y alicatados |
| NaN | NaN | NaN | TERRAZA | Mejorar uniones de albardillas, irregulares y cortantes. Ademas relleno de hueco en encuentros finales libres. | Carpintería de aluminio |
| NaN | NaN | NaN | TERRAZA | Reparar esconchon en viguetas y limpiar restos de hormigón | Albañilería |
| NaN | NaN | NaN | TERRAZA | Repasos de pintura en los vivos, en el paño de pared monocapa. | Pintura |
| NaN | NaN | NaN | TERRAZA | REHACER.Rodapie mal cortado enla salida de la puerta de la terraza lado izquierdo, | Carpintería de madera |
| NaN | NaN | NaN | TIRO DE ESCALERA | Pandeos en todo el tiro de la escalera, ERROR ESTRUCTURAL, se aprecia en sus verticales por miras de pladur y en sus horizontales por estructura de hormigon. | Albañilería |
| NaN | NaN | NaN | TIRO DE ESCALERA | Sellar encuentros de rodapie en toda la escalera | Albañilería |
| NaN | NaN | NaN | VENTANA PATIO | AL ABRIR CHOCA CONTA PARED DE ASCENSOR | Carpintería de aluminio |
| NaN | NaN | NaN | DORMITORIO 1 | Repaso de carpinteria y rodapie en la puerta de entrada a la habitación | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Clavos en moldura puerta corredera | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Remate moldura con rodapie en dormitorio | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Lijar y pintar pintura alrededor de los mecanismos. | Pintura |
| NaN | NaN | NaN | DORMITORIO 1 | Lijar y pintar pintura alrededor de las luminarias en techos. | Pintura |
| NaN | NaN | NaN | DORMITORIO 1 | Falta balda en armario pequeño lado de la derecha. | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Remate de armario con techo repasar. | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Descuadre en interior de armario | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 TERRAZA | Sellar encuentros de madera con vIgas de hormigón, hay agujeros. | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 TERRAZA | Mejorar uniones de albardillas, irregulares y cortantes. Ademas relleno de hueco en encuentros finales libres. | Carpintería de aluminio |
| NaN | NaN | NaN | DORMITORIO 1 | Repaso de pintura en aristas del vestidor | Pintura |
| NaN | NaN | NaN | DORMITORIO 1 | Repasar la lechada en solado de vestidor | Solados y alicatados |
| NaN | NaN | NaN | DORMITORIO 1 | Cajones de vestidor son 4 no 2 | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Puertas de armario ralladas | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Clavos en costado de armario de vestidor | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 | Ingletes de azulejos en baño defectuosos CAMBIAR. | Solados y alicatados |
| NaN | NaN | NaN | DORMITORIO 1 | Encuentro azulejo con pared en ducha arreglar | Solados y alicatados |
| NaN | NaN | NaN | DORMITORIO 1 | Remates de mampara con plato de ducha y solado | Albañilería |
| NaN | NaN | NaN | DORMITORIO 1 | Lechada en azulejos ducha y repasar candileja | Solados y alicatados |
| NaN | NaN | NaN | DORMITORIO 1 | Mampara de ducha  no funciona  esta caida. CAMBIAR | Mamparas |
| NaN | NaN | NaN | DORMITORIO 1 | Miras de hierro que son de soporte de encimera estan OXIDADAS, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD. | Mobiliario cocina |
| NaN | NaN | NaN | DORMITORIO 1 BAÑO | Fijar balda sobre cajonera, no es estable | Carpintería de madera |
| NaN | NaN | NaN | DORMITORIO 1 BAÑO | Repasar encuentros de azulejo con pared | Solados y alicatados |
| NaN | NaN | NaN | DORMITORIO 1 BAÑO | Tapon de lavavo roto | Fontanería |
| NaN | NaN | NaN | DORMITORIO BAÑO 1 | HOJA DE VENTANA, NO SE ABRE, no se corta grifo. CAMBIAR VENTANA | NaN |
| NaN | NaN | NaN | DORMITORIO 1 BAÑO | Clavos en puerta y molduras de baño | NaN |
| NaN | NaN | NaN | DORMITORIO 1 | Lijar y pintaren los encuentros techos y pared en vestidor | NaN |
| NaN | NaN | NaN | TIRO DE ESCALERA | Barandilla se sale del plano del ascensor | NaN |
| NaN | NaN | NaN | VENTANAS | Juntas de goma de ventanas, estan sueltas muchas. | NaN |
| NaN | NaN | NaN | PASILLO | Lijar, tender, colocar malla en Fisura en techo de pasillo | NaN |
| NaN | NaN | NaN | PASILLO DORMITORIO 1 | Repasar encuentro carpinteria con techo | NaN |
| NaN | NaN | NaN | TIRO DE ESCALERA | Repasos de pintura en techo y aristas de escalera | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Pared de casoneto sin asentamiento ni anclaje, pared que ofrece movimiento\nhorizonta.Puerta corredera  del baño esta suelta  y el cerco. PELIGRO DE SEGURIDAD. | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Baldosa suelo entrada al baño rota. | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Mampara se mueve mucho. INESTABLE. PELIGRO DE SEGURIDAD | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Rematar interior de candilejas de ducha, agujeros, irregularidades. | NaN |
| NaN | NaN | NaN | DORMITORIO 2 | Focos sin rematar, techo a reparar en pintura | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Fijar balda de baño y alinear, no estable | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Azulejo roto en arista de ducha | NaN |
| NaN | NaN | NaN | DORMITORIO 2 BAÑO | Rematar encuentros azulejos con pared | NaN |
| NaN | NaN | NaN | DORMITORIO 2 | HOJA DE VENTANA, CHOCA CONTRA PARED. CAMBIAR VENTANA | NaN |
| NaN | NaN | NaN | DORMITORIO 2 | Repaso de pintura en la pared del cabezero, agujero por golpe causado por la apertura de la ventana | NaN |
| NaN | NaN | NaN | DORMITORIO 2 | Lijar y pintar. Repasar encuentros focos de habitación | NaN |
| NaN | NaN | NaN | DORMITORIO 2 | Repasos de pintura en pared de armarios, no pegotes de pintura, sino laca completa | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Puerta de entrada con silicona y rallada | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Puerta corredera arañada, TORNILLO QUE RALLA LA PUERTA | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Repasar unión de rodapies | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Sellar encuentro de madera con pared en terraza | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Sellar encuentro de madera con peldaño en terraza | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Repasar molduras puertas | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Repaso de pintura en pared del  termostato | NaN |
| NaN | NaN | NaN | DORMITORIO 3 BAÑO | Fijar balda de madera en cuarto de baño, inestable. | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Miras de hierro que son de soporte de encimera estan oxidadas, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD. | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Mecanismo del tapon roza con el sifon | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Repasar encuentro de solado con Azulejo debajo de la balda | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Repasar lechada y candileja como en los otros baños | NaN |
| NaN | NaN | NaN | DORMITORIO 3 | Remates de pintura en focos de baño y mecanismos | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Puerta de entrada termo sellada se ve en los cantos y clavos en las jambas | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Encuentro de moldura con rodapie repasar | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Mecanismos torcidos y repaso de pintura en pared frente armario | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Puerta de entrada al baño sistema de cierre roto | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Puerta corredera del baño arañada y con clavos en moldura | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Miras de hierro que son de soporte de encimera estan oxidadas, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD. | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Sellar escudos de sifones como en todos los baños. Estan todos abiertos conagujeros a pared | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | El mecanismo del tapon del lavavo derecho esta roto | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Plato de ducha roto en la arista | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Lechada en azulejos ducha y repasar candileja | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Azulejo corto en esquina de candileja | NaN |
| NaN | NaN | NaN | DORMITORIO 4 | Revisar encuentros de mampara  con azulejos | NaN |
| NaN | NaN | NaN | OFFICE | Puertas correderas sin topes | NaN |
| NaN | NaN | NaN | OFFICE | Los tornillosde la puerta corredera nos estan en la misma cara | NaN |
| NaN | NaN | NaN | OFFICE | Las puertas correderas tienen movimiento excesivo | NaN |
| NaN | NaN | NaN | COCINA | Faltan topes de puerta corredera para cerrar y abrir | NaN |
| NaN | NaN | NaN | COCINA | lacar canto de puerta corredera arañado. LACA DETERIORADA | NaN |
| NaN | NaN | NaN | COCINA | Arañado fijo izquierdo de corredera  y quitar silicona cristal. LACA DETERIORADA Y SILICONA ENTRRE CRISTALES PEGADA | NaN |
| NaN | NaN | NaN | COCINA | La puerta del congelador esta rota y la madera DE MELAMINA debajo del congelador esta rallada | NaN |
| NaN | NaN | NaN | COCINA | La pieza de union, GOLA, estre nevera y congelador  esta rallada y la goma suelta | NaN |
| NaN | NaN | NaN | COCINA | Repasar encuentro techo con focos cocina | NaN |
| NaN | NaN | NaN | COCINA | La gola del esquinero no esta NIVELADA | NaN |
| NaN | NaN | NaN | COCINA | El panelado del lavavajillas roza LA LACA | NaN |
| NaN | NaN | NaN | COCINA | La puerta de al lado de la vitrina esta espotillada y en la esquina también | NaN |
| NaN | NaN | NaN | COCINA | Repasar lechada en baldosa jonto a puerta corredera y rodapie | NaN |
| NaN | NaN | NaN | COCINA | Sellar encuentro suelo pared esquina de la vitrina y puerta despensa arañada | NaN |
| NaN | NaN | NaN | VESTIBULO | TODOS  los cantos de la candilejas que son irregulares en todos los techos de planta baja | NaN |
| NaN | NaN | NaN | VESTIBULO | TODOS  los techo de pladur est lleno de parches y pañaos de pintura mal hechos. | NaN |
| NaN | NaN | NaN | VESTIBULO | Lijar y pintar techos. Colocar velo . Se aprecia TODOS loa perfiles y conductos de aire acondicionado | NaN |
| NaN | NaN | NaN | VESTIBULO | PINTURA COMPPLETA DE techo frente ascensor | NaN |
| NaN | NaN | NaN | VESTIBULO | Rejilla de retorno rota | NaN |
| NaN | NaN | NaN | VESTIBULO | Rejilla de retorno de aacc OBSTRUIDO POR CONDUCUCTOS. | NaN |
| NaN | NaN | NaN | COMEDOR | Repasar encentros de carpintería central con techo. | NaN |
| NaN | NaN | NaN | COMEDOR | TODOS LOS TECHOS ESTAN IRREEGULARES . Repasar encuentro focos y techo de toda la planta baja | NaN |
| NaN | NaN | NaN | SALON | Soporte de guia para la corredera esta mal rematado y ejecutado. MOVIMIENTO DE PUERTA. | NaN |
| NaN | NaN | NaN | SALON | Falta tope y tornilleria en puerta corredera | NaN |
| NaN | NaN | NaN | SALON | Remate de techo encima de la puerta de hierro. TABICA MAL TERMINADA | NaN |
| NaN | NaN | NaN | SALON | La pletina de la guia de la corredera es cortante. PELIGRO DE SEGURIDAD | NaN |
| NaN | NaN | NaN | SALON | Las barandilla salen del plano del ascensor. PELIGRO DE SEGURIDAD | NaN |
| NaN | NaN | NaN | SALON | Pared del ascensor repasar de pintura | NaN |
| NaN | NaN | NaN | ALMACÉN | Baldosa  rota cerca de la puerta de salida al patio.en suelo. | NaN |
| NaN | NaN | NaN | ALMACÉN | Puerta de cerrajeria  da potazo no amortigüa | NaN |
| NaN | NaN | NaN | ALMACÉN | AGUJERO de techo encima de la puerta. | NaN |
| NaN | NaN | NaN | ALMACÉN | Repasar uniones de los rodapies | NaN |
| NaN | NaN | NaN | ALMACÉN | Mampara baño se mueve mucho. PELIGRO DE SEGURIDAD. | NaN |
| NaN | NaN | NaN | PATIO SOTANO | TELA ASFALTICA DETERIORADA. COLOCAR UNA NUEVA. COMPROBRA DESAGUES | NaN |
| NaN | NaN | NaN | PATIO SOTANO | AGUJERO EN PARED repaso de pintura en pared derecha antes de la puerta de salida al garaje | NaN |
| NaN | NaN | NaN | GARAJE | SUELO TOTALMENTE DETERIORADO, ARREGLAR ESQUINAS Y SUELO COMPLETO NIVELADO Y PINTADO | NaN |
| NaN | NaN | NaN | GARAJE | El hormigón no llega en su totalidad contra las esquinas | NaN |
| NaN | NaN | NaN | GARAJE | La estructura de la puerta del garaje esta suelta | NaN |
| NaN | NaN | NaN | GARAJE | La puerta del garaje no asienta en su totalidad contra el suelo | NaN |
| NaN | NaN | NaN | GARAJE | Sellar y limpiar las tiras de led | NaN |
| NaN | NaN | NaN | LAVANDERIA | La tapas de las arquetas falta sellar y poner un mecanismo para poder levantarse | NaN |
| NaN | NaN | NaN | CUARTO DE PLANCHA | La mampara son endebles en general | NaN |
| NaN | NaN | NaN | CUARTO DE PLANCHA | Maneta de puerta del baño no esta recta | NaN |
| NaN | NaN | NaN | CUARTO DE PLANCHA | Mueble de baño roza el cajon primero | NaN |
| NaN | NaN | NaN | CUARTO DE PLANCHA | Repasar lechada azulejos | NaN |
| NaN | NaN | NaN | CUARTO DE PLANCHA | Repasar encuentro con focos | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Miras de hierro que son de soporte de encimera estan oxidadas, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD. | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Sellar sifon | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Remate de azulejo en candileja | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Repasar encuentro azulejos con techo en candileja | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Repasar encuentro de azulejos con pared | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Azulejo roto en mecanismo de inodoro | NaN |
| NaN | NaN | NaN | BAÑO PLANTA BAJA | Perfil de mampara rematar encuentro con pared | NaN |
| NaN | NaN | NaN | GENERALES | Revisar todos los mecanismos que estan sueltos  y mal rematados a su alrededor | NaN |
| NaN | NaN | NaN | GENERALES | Repasar todos los encuentros de las luminarias y los techos | NaN |
| NaN | NaN | NaN | GENERALES | Pandeos en todo el tiro de escalera y repasar las aristas | NaN |
| NaN | NaN | NaN | GENERALES | Repasar las aguas de los techos de planta baja y los cantos de las candilejas son irregulares | NaN |
| NaN | NaN | NaN | GENERALES | Puertas de paso  y rodapies. NO SON LACADOS, SON TERMOSELLADOS. | NaN |
