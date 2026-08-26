// services/postventa-front/js/cola.js
// Limitador de concurrencia (R7-R12). Lógica pura: sin fetch, sin DOM, sin
// Alpine. Es la pieza que cumple el criterio de aceptación 3 —«una remesa
// larga no dispara N peticiones a la vez»— y la MISMA que se usa para
// archivar (R20): otra fase, mismo límite, misma implementación.
//
// Por qué una cola con plazas y no lotes de N con Promise.all: un lote va al
// ritmo del parte más lento y deja plazas vacías esperando. Con plazas, en
// cuanto una queda libre entra el siguiente parte.
//
// El módulo se expone en las dos direcciones: `window` para el navegador
// (se carga como <script> de siempre, sin defer) y `module.exports` para
// `node --test`. Cero herramientas de build.

(function () {
  "use strict";

  /**
   * Ejecuta `tareas` con como mucho `limite` vivas a la vez.
   *
   * @param {Array<function(): Promise<*>>} tareas Funciones que devuelven una promesa.
   *        Se invocan aquí dentro, no antes: invocarlas fuera ya habría
   *        disparado las peticiones y el límite no serviría de nada.
   * @param {number} limite Entero >= 1.
   * @param {function(number, {ok: boolean}): void} [alTerminar] Se llama al
   *        acabar CADA tarea, con su índice y su resultado. Es el progreso
   *        «N de M» de R9: avanza con veredicto o con error.
   * @returns {Promise<Array<{ok: true, valor: *}|{ok: false, error: Error}>>}
   *          Un resultado por tarea, EN EL ORDEN DE ENTRADA.
   *
   * Nunca rechaza por culpa de una tarea: un parte roto no puede tumbar la
   * remesa (R10). El error viaja como resultado `{ok: false, error}`.
   */
  async function ejecutarConLimite(tareas, limite, alTerminar) {
    if (!Number.isInteger(limite) || limite < 1) {
      // Un límite inválido NO puede degradar a «sin límite»: sería justo lo
      // que el criterio de aceptación 3 prohíbe, y en silencio.
      throw new Error(
        `el límite de concurrencia debe ser un entero >= 1, y es ${limite}`,
      );
    }

    const resultados = new Array(tareas.length);
    let siguiente = 0;

    async function plaza() {
      // Cada plaza toma tareas mientras queden. `siguiente++` es atómico
      // dentro de una plaza porque JavaScript no interrumpe entre sentencias
      // síncronas: dos plazas nunca se llevan el mismo índice.
      while (siguiente < tareas.length) {
        const indice = siguiente;
        siguiente += 1;

        let resultado;
        try {
          // `await` sobre el retorno cubre también a una tarea que lance de
          // forma síncrona, antes siquiera de devolver una promesa.
          resultado = { ok: true, valor: await tareas[indice]() };
        } catch (error) {
          resultado = { ok: false, error: error };
        }

        resultados[indice] = resultado;
        if (typeof alTerminar === "function") {
          alTerminar(indice, resultado);
        }
      }
    }

    const plazas = [];
    for (let i = 0; i < Math.min(limite, tareas.length); i += 1) {
      plazas.push(plaza());
    }
    await Promise.all(plazas);

    return resultados;
  }

  const Cola = { ejecutarConLimite: ejecutarConLimite };

  if (typeof window !== "undefined") {
    window.Cola = Cola;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Cola;
  }
})();
