<!-- progress/peticion_posventa_prueba_url_F-023.md -->
# Petición a Posventa: la prueba que desbloquea F-023

> **Para el humano, antes de reenviar nada.**
>
> **Qué es esto.** La petición a **Alicia Echevarría (Posventa)** para que haga
> **una vez a mano**, en Sigrid, lo que ningún documento puede contarnos: qué
> guarda el ERP cuando se asocia un documento **por enlace** en vez de subiendo
> el fichero. Es la consulta **Q10** de `progress/explore_grafico_url.md`, y es
> **lo único** que bloquea F-023.
>
> **Cómo se usa.** El bloque de abajo, de la línea de guiones en adelante, está
> escrito para **reenviarse tal cual** por correo. No lleva jerga de tablas ni
> de SQL, no menciona ningún dato de ningún cliente y no pide nada que no sepa
> hacer ya.
>
> **Qué hacer con la respuesta.** En cuanto Alicia conteste, la lectura de lo
> que quedó guardado la hace este script, **sin escribir nada**:
>
> ```
> powershell -ExecutionPolicy Bypass -File infra\13_caracterizacion_grafico_url.ps1 -FechaPruebaPosventa <AAAAMMDD> -CodigoReclamacionPrueba "<el código que ella diga>"
> ```
>
> Con eso F-023 pasa de `blocked` a diseñable, y **solo entonces** se escribe su
> spec: F-008 ya advirtió que esto **no se diseña sobre suposiciones**.

---

**Asunto: Una prueba de cinco minutos en Sigrid, sobre una incidencia de prueba**

Hola Alicia:

Te pido un favor pequeño, y te cuento primero para qué, porque así se entiende
mejor lo que hay que hacer.

## Por qué te lo pedimos

Estamos automatizando el cierre de las incidencias de posventa: cuando el parte
firmado esté revisado y archivado, el sistema cerrará la incidencia sin que
nadie tenga que entrar a Sigrid a hacerlo.

Nos falta una pieza: queremos que la incidencia **siga quedando con su parte a
la vista dentro de Sigrid**, como queda ahora cuando lo adjuntáis vosotros. Hay
dos maneras de conseguirlo, y la que nos gustaría usar es dejar en Sigrid **un
enlace** al parte —que ya queda guardado, firmado y ordenado, en su carpeta— en
lugar de meter otra copia del fichero dentro del ERP.

El problema es que **esa opción no se ha usado nunca aquí**. Está en el menú de
Sigrid, pero en toda la historia del sistema no hay ni un solo documento
guardado así. Y hasta que alguien la use una vez, no podemos saber cómo la
guarda Sigrid por dentro, ni si el ERP la da por buena al cerrar el parte. **No
queremos programarlo a base de suponer.**

Por eso te lo pedimos a ti: es un minuto de la aplicación que usas todos los
días, y nos ahorra semanas de ir a ciegas.

## Qué NO va a pasar

- **Nosotros no vamos a tocar nada.** No escribimos, ni cambiamos, ni borramos
  nada en Sigrid. Después de tu prueba solo **miramos** lo que quedó guardado.
- **Es sobre una incidencia de prueba**, no sobre una de un cliente en curso. Si
  prefieres crear una nueva para esto, mejor todavía.
- **No cambia nada de vuestra forma de trabajar.** Hoy seguís haciéndolo como
  siempre. Esto es solo para ver si el camino existe.
- **Si sale mal, no pasa nada**: descartamos la idea y seguimos por el otro
  camino. Un resultado negativo también nos vale.

## Lo que hay que hacer

Sobre una incidencia de prueba (o una que crees para esto):

1. Abre la ventana donde normalmente adjuntas el parte firmado.
2. En vez de importar el documento desde un archivo, entra en
   **Importa → «Asociar URL de Internet…»**.
3. Te pedirá una dirección de internet: **vale cualquiera**. Si tienes a mano el
   enlace de un parte que ya esté guardado en SharePoint, úsalo mejor, porque
   así vemos de paso si Sigrid lo abre bien.
4. Rellena la **descripción** y el **tipo de gráfico** como haces siempre con
   los partes (el de *Fotos Reparaciones*), y guarda.
5. **Intenta abrirlo desde Sigrid**, como si fueras a consultarlo: haz doble
   clic sobre lo que acabas de asociar y mira qué ocurre.
6. Y por último, sobre esa misma incidencia, lanza
   **Procesos → «3. Cerrar parte»**, como si la fueras a cerrar de verdad.

## Lo que nos tienes que contar después

Con dos líneas nos vale. Lo que necesitamos saber es:

- **El código de la incidencia de prueba y el día** en que lo hiciste.
- Si al abrirlo desde Sigrid **se ve el documento**, o no se abre, o **te pide
  usuario y contraseña**.
- Si **«Cerrar parte» te dejó cerrarla**, o si se quejó. Si te salió algún
  mensaje, **cópialo tal cual** o mándanos una foto de la pantalla: el texto
  exacto nos dice mucho.
- Cualquier cosa que te haya parecido rara, aunque no sepas si tiene que ver.

Son cinco minutos. Y si en algún paso no te deja, o no ves la opción, o
simplemente no lo tienes claro, **no insistas**: dínoslo y ya está, que eso
también es una respuesta.

Muchas gracias.
