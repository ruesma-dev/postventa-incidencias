<!-- docs/procesos/README.md -->
# Procesos de posventa en BPMN 2.0

- **`postventa.bpmn`**: el ciclo completo de una incidencia de posventa, desde que llega el listado de la propiedad
  hasta que la incidencia se cierra en Sigrid. Un plano principal (colaboración con la propiedad, Sigrid, SharePoint y
  el industrial) y un plano por subproceso: 01 Entrada, 02 Revisión, 03 Volcado a Sigrid y 05·06 Partes firmados.
  Se abre con [bpmn.io](https://demo.bpmn.io) o con Camunda Modeler.

Colores (extensión «BPMN in Color», que bpmn-js pinta): sin color, funciona hoy; ámbar, en curso (backend desplegado y
falta la página); azul, previsto. Los códigos F-0xx son las fichas de `BACKLOG.md`.

**Estado**: sacado del código de `dev` y del backlog el 2026-10-20 (tras el cierre de F-059, con F-038 en curso).
Cuando una feature cambie el proceso, se actualiza aquí en el mismo trabajo, como `docs/ARCHITECTURE.md`.
