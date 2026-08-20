// services/postventa-front/js/app.js
// Lógica del front (Alpine). De momento solo comprueba el backend: es lo que
// pide F-001. La carga de partes y la revisión llegan en F-007.

function appPostventa() {
  return {
    estado: "comprobando",
    mensaje: "Comprobando el servicio…",
    version: "",

    async comprobarBackend() {
      try {
        const respuesta = await fetch(`${window.CONFIG_POSTVENTA.baseApi}/health`);
        if (!respuesta.ok) {
          throw new Error(`el servicio respondió ${respuesta.status}`);
        }
        const datos = await respuesta.json();
        this.estado = "ok";
        this.version = `${datos.servicio} ${datos.version}`;
        this.mensaje = `Servicio disponible (entorno ${datos.entorno}).`;
      } catch (error) {
        this.estado = "error";
        this.mensaje = `No se puede contactar con el servicio: ${error.message}`;
      }
    },
  };
}
