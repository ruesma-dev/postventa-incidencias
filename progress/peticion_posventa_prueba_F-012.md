<!-- progress/peticion_posventa_prueba_F-012.md -->
# Petición a Posventa: la prueba del circuito completo (F-012)

> **Para el humano, antes de reenviar nada.**
>
> **Qué es esto.** La petición a **Ana Bello** y **Alicia Echevarría** para que
> prueben la aplicación de punta a punta: subir partes firmados, revisarlos y
> confirmar el cierre, sobre **la obra de pruebas 404** y ninguna otra. El
> bloque de abajo, de la línea de guiones en adelante, está escrito para
> **reenviarse tal cual** por correo.
>
> **NO se envía todavía.** Antes tienen que cumplirse tres cosas:
>
> 1. **El bloque 9 de F-012 hecho y en verde**
>    (`progress/guion_bloque9_F-012.md`, T25–T32). Si la aplicación no ha
>    adjuntado y cerrado ni una vez con el humano delante, no se le pide a
>    negocio que lo estrene.
> 2. **Los logins de Sigrid de las dos, dados de alta**, con
>    `infra/07_alta_usuario_sigrid.ps1`. Sin esa correspondencia la aplicación
>    no puede firmar el cierre y la pantalla se lo dirá con un aviso.
>    **Ojo con Alicia**: su login del ERP es **`aechevarria`**, que **no**
>    coincide con el prefijo de su correo, así que la siembra automática no lo
>    acierta y hay que darlo a mano. El de Ana, comprobarlo antes de asumirlo.
> 3. **Las dos, dentro del grupo de seguridad** que da acceso al portal
>    (`posventa-usuarios`, `docs/DESPLIEGUE.md` §6). Si no están, la tarjeta
>    de Posventa ni siquiera les aparece.
>
> **Un hueco que rellena quien envía**: donde pone `<la dirección del portal>`
> va la URL real. No se escribe en este repositorio a propósito.
>
> **Qué desbloquea la respuesta.** La pregunta marcada como *«una pregunta
> para vosotras dos»* es la **P1** de `specs/F-012-grafico-sigrid/design.md`
> §14 y la precondición documental **D2** del guion del bloque 9: si `PV002`
> no fuera el tipo correcto, cambiarlo es decisión de dos dueños (una opción
> nuestra **y** la lista de la pasarela), así que conviene tener la respuesta
> por escrito.

---

**Asunto: ¿Nos ayudáis a probar la aplicación de partes, sobre la obra de pruebas?**

Hola Ana, hola Alicia:

Ya tenemos lista la primera versión completa de la aplicación de partes de
posventa y nos gustaría que la probarais vosotras antes que nadie. Lo que os
pedimos es esto: **subir por la aplicación unos cuantos partes firmados y
confirmar el cierre**, y después mirar en Sigrid y decirnos si lo que ha
quedado ahí es **exactamente lo que habríais dejado vosotras a mano**.

## Por qué precisamente vosotras

Porque lo que la aplicación hace es, paso por paso, lo que ya hacéis hoy:
renombrar el parte firmado, colgarlo de la reclamación desde el botón de
**gráficos**, con la Descripción `PARTE FIRMADO` y el tipo de gráfico de
*Fotos Reparaciones*, y después **Procesos → 3. Cerrar parte**. Está sacado
de la guía que escribió Alicia. La diferencia es que ahora lo hace la
aplicación sola, y por eso quien mejor puede decir si está bien hecho sois
vosotras: nadie más sabe cómo tiene que quedar.

## Sobre qué obra se prueba: **la 404, la de pruebas. Solo la 404**

Esto es importante y no es una formalidad: **cuando confirmáis el cierre, la
aplicación escribe de verdad en Sigrid**, igual que si lo hubierais hecho a
mano. No hay un Sigrid de mentira donde ensayar.

Por eso la prueba entera se hace **sobre la obra 404, la de pruebas**. Ni
Mirasierra, ni ninguna obra con clientes de verdad. Si en algún momento os
aparece en pantalla una incidencia que no sea de la 404, no confirméis nada y
avisadnos.

## Lo que necesitamos que preparéis antes (esto es lo que más tiempo lleva)

Necesitamos partes firmados **de verdad**, de la obra 404. Es decir:

1. **Crear en la obra 404 dos o tres reclamaciones de prueba**, como creáis
   cualquier otra: su unidad, su oficio, su descripción del problema. Con dos
   o tres nos vale de sobra.
2. **Imprimir sus partes de trabajo**, los mismos que se le dan al industrial.
3. **Firmarlos a mano**, tal y como los firma un cliente: en la casilla de
   conformidad, con bolígrafo. Vale que os los firméis vosotras; lo que
   importa es que sea una firma de verdad sobre el papel, porque la
   aplicación tiene que reconocerla.
4. **En uno de ellos, escribid a mano una observación** del estilo de «no se
   reparó del todo» o «se ha hecho solo un parcheado». **Este es el caso que
   más nos interesa ver**: un parte firmado pero con una pega escrita no se
   puede cerrar solo, y la aplicación tiene que apartarlo y dejarlo en manos
   de una persona en vez de darlo por bueno. Queremos comprobar delante de
   vosotras que lo hace.
5. **Escanearlos** como escaneáis siempre las remesas, en PDF. Da igual si
   salen todos en un mismo PDF o cada uno en el suyo: la aplicación los
   separa.

Una cosa que **no** nos sirve: reaprovechar un parte real ya firmado de otra
obra. Aunque el papel esté perfecto, el **número de incidencia** impreso en
él es de una obra real, y la aplicación iría a cerrar esa incidencia de
verdad. Los partes tienen que ser de reclamaciones de la 404.

## Los pasos, ya con los PDF escaneados delante

1. **Entrad en el portal** (`<la dirección del portal>`) con vuestro usuario
   de siempre y abrid la tarjeta **«Partes de Posventa»**.
2. **Soltad los PDF** en el recuadro grande de la pantalla, o buscadlos con
   *Elegir ficheros* / *Elegir una carpeta*. Hasta aquí no se ha enviado nada:
   lo dice la propia pantalla.
3. Pulsad **«Trocear la remesa»**. La aplicación separa el escaneo en un parte
   por hoja y os enseña una barra con «N de M partes terminados» mientras los
   va leyendo. Tarda un poco: está leyendo cada parte.
4. **Revisad lo que ha leído.** A la izquierda queda la lista de partes, cada
   uno con un punto de color: **verde** el que ve correcto y completo,
   **ámbar** el que quiere que mire una persona, **rojo** el que no ha podido
   leer. Al pulsar sobre uno se abre a la derecha con el PDF y los datos que
   ha sacado —promoción, obra, unidad, nº de incidencia, fecha, descripción,
   DNI, observaciones y página—, cada uno con el porcentaje de seguridad que
   tiene. Los que no las tiene todas consigo vienen marcados en ámbar.
5. **Corregid lo que esté mal**: se escribe encima del dato, sin más, y
   después se pulsa **«Revalidar»** (eso no vuelve a gastar lectura, solo
   recalcula con vuestra corrección).
   - El parte que lleva la observación escrita a mano **debería quedarse en
     ámbar**, con un aviso que dice que firmado no es lo mismo que conforme y
     que alguien tiene que leerla y decidir. **Ese parte no se archiva ni se
     cierra**, y es lo correcto. Decidnos si os aparece así.
6. **Archivar.** Pulsad **«Archivar los partes aptos»**, y luego **«Sí,
   archivar»**. La aplicación guarda cada PDF en su carpeta de SharePoint, con
   su nombre, y os deja un enlace para abrirlo y comprobarlo.
7. **Ver antes de cerrar.** Pulsad **«Ver qué pasaría (no cierra nada)»**.
   Este botón **no toca Sigrid**: solo mira y os cuenta lo que va a hacer con
   cada parte —qué fichero va a colgar de la reclamación, con qué descripción
   y qué tipo de gráfico, y de qué estado a qué estado va a pasar la
   reclamación—. Leedlo, que es justo lo que queremos que juzguéis.
8. **Cerrar.** Pulsad **«Cerrar las incidencias»**, y cuando os pregunte
   «¿Seguro? Esto escribe en Sigrid y lo ve Posventa», **«Sí, cerrar»**.

Por cada parte, y **en este orden**, la aplicación: **guarda el PDF en su
carpeta**, **lo cuelga de la reclamación como gráfico** y **después cierra la
reclamación**. Nunca al revés, para que ninguna reclamación se quede cerrada
sin su parte dentro. Y **no cierra absolutamente nada mientras no pulséis vosotras ese último
botón**.

## Dos avisos, para que no os pillen por sorpresa

- **«Cerrar las incidencias» cierra TODOS los partes que haya en pantalla en
  ese momento**, no solo el que tengáis abierto. Como es la primera vez,
  hacedlo **de uno en uno o de dos en dos**: subís un parte, lo cerráis, lo
  miráis en Sigrid, y luego el siguiente. Así, si algo no os gusta, no se ha
  ido de las manos.
- **Lo que confirméis se escribe de verdad en Sigrid.** No hay ensayo ni
  deshacer. De ahí que sea solo sobre la obra 404.

Y un detalle menor: los botones que escriben piden **dos clics**, y el
segundo **caduca** si tardáis un rato. Si os dice que volváis a empezar el
gesto, no es un fallo: es a propósito.

## Lo que nos tenéis que contar después

Cuando hayáis cerrado alguna, entrad en Sigrid a la reclamación de prueba y
miradla como miraríais cualquier otra. Nos vale con contestar a estas
preguntas, aunque sea en una línea cada una:

1. **El gráfico que ha quedado colgado de la reclamación, ¿es el parte que
   subisteis?** ¿Se abre bien desde Sigrid, haciendo doble clic como siempre?
2. **La Descripción y el Tipo de gráfico, ¿son los que pondríais vosotras?**
   Si no, decidnos exactamente qué pondríais.
3. **El nombre del fichero, ¿os sirve para reconocerlo y encontrarlo?** ¿Le
   cambiaríais algo? (Esta es la duda que dejó Alicia abierta en su guía: si
   conviene que lleve también el nombre de la vivienda.)
4. **El estado en que ha quedado la reclamación, ¿es el que esperabais?**
   ¿Está igual que si la hubierais cerrado vosotras con *Procesos → 3. Cerrar
   parte*, o notáis algo distinto?
5. **¿Leyó bien los datos del parte?** Y sobre todo: **¿en qué campos se
   equivocó?** Nombradlos, que es lo que nos permite mejorarlo.
6. **¿Qué echáis en falta** para que esto os sirva de verdad en el día a día?

Si podéis, apuntad **la reclamación y el día** de cada prueba, para que
podamos ir a mirar lo mismo que vosotras.

## Y una pregunta para vosotras dos, que decide una cosa importante

> Cuando colgáis un parte firmado de una reclamación, el Tipo de gráfico que
> usáis es **`PV002 — POSTVENTA:Fotos Reparaciones`**.
>
> **¿Es ese el tipo correcto para un parte firmado, o solo es el que se ha
> venido usando?**
>
> Lo preguntamos porque el nombre habla de *fotos de reparaciones*, no de
> partes, y hemos visto que en Sigrid hay ya varios miles de documentos
> llamados «PARTE FIRMADO» guardados con ese tipo. Con esto la aplicación va a
> marcar **todos** los partes que suba, así que preferimos que nos lo digáis
> vosotras antes que suponerlo. **Si hubiera que usar otro, decidnos cuál** y
> lo cambiamos.

## Lo que os pedimos que NO hagáis

- **No probéis sobre obras reales.** Solo la 404, aunque tengáis a mano un
  parte firmado de otra obra que «vendría de perlas».
- **No cerréis a mano una reclamación que ya hayáis pasado por la
  aplicación**, mientras dure la prueba. Si algo no ha quedado bien,
  contádnoslo y lo miramos: si lo arregláis por vuestra cuenta, nos quedamos
  sin ver dónde falló.
- **No repitáis muchas veces algo que se queda a medias.** Si un parte se
  atasca, o la pantalla se queda pensando, o sale un mensaje que no entendéis,
  **paradlo y avisadnos**. Con una foto de la pantalla nos sobra. Insistir es
  lo único que puede liarnos de verdad.

## Si algo falla

Escribidnos y ya está, con la foto de la pantalla si podéis. **Que falle es un
resultado tan bueno como que funcione**: para eso es una prueba, y para eso la
hacemos sobre una obra que no es de nadie. Lo que no queremos es que perdáis
media mañana peleándoos con algo que arreglamos nosotros en cinco minutos.

Muchas gracias a las dos.
