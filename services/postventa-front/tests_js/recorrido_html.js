// services/postventa-front/tests_js/recorrido_html.js
// F-040 · Ayuda de los tests (no es un `*.test.js`: `node --test` no lo lanza solo).
//
// Recorre un HTML con directivas de Alpine como lo pintaría Alpine con un
// alcance dado, sin navegador: un `x-if` falso no pinta lo de dentro; un
// `x-for` pinta su primer elemento (con sus variables); un `x-show` falso deja
// el elemento oculto. Es la misma técnica que `recorrerBandeja` de
// `tests_js/revision.test.js` (F-038, Bloque 1 bis), sacada aquí para que el
// panel de volcado (`tests_js/volcado.test.js`) la use sin tocar la de F-038.

const VACIOS_HTML = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
const ETIQUETA_HTML = /<(\/?)([a-zA-Z][\w-]*)((?:\s+[^\s"'=<>\/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*(\/?)>/g;
const ATRIBUTO_HTML = /([^\s"'=<>\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;
const DIRECTIVAS_DE_VALOR = /^(?:x-text|x-show|x-if|x-model|x-html|:[\w.-]+|x-bind:[\w.-]+)$/;
const DIRECTIVAS_DE_EVENTO = /^(?:@[\w.-]+|x-on:[\w.-]+|x-init)$/;
const BUCLE = /^\s*(?:\(\s*(\w+)\s*(?:,\s*(\w+)\s*)?\)|(\w+))\s+in\s+([\s\S]+)$/;

function atributosHtml(trozo) {
  const atributos = {};
  for (const m of trozo.matchAll(ATRIBUTO_HTML)) {
    atributos[m[1]] = m[2] ?? m[3] ?? m[4] ?? "";
  }
  return atributos;
}

/** `with (alcance) { return (expresión) }`: como evalúa Alpine. */
function evaluarEn(alcance, expresion) {
  // eslint-disable-next-line no-new-func
  return Function("alcance", `with (alcance) { return (${expresion}); }`)(alcance);
}

/**
 * Los elementos pintados (con su alcance, sus atributos, si se ven y la pila
 * de sus antepasados pintados) y los problemas de evaluación.
 */
function recorrer(html, alcanceBase) {
  const limpio = html.replace(/<!--[\s\S]*?-->/g, "").replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, "");
  const pila = [{ nombre: "#raiz", alcance: alcanceBase, pinta: true, visible: true, atributos: {} }];
  const elementos = [];
  const problemas = [];
  for (const m of limpio.matchAll(ETIQUETA_HTML)) {
    const [, cierre, nombreCrudo, resto, autocierre] = m;
    const nombre = nombreCrudo.toLowerCase();
    if (cierre) {
      const i = pila.map((e) => e.nombre).lastIndexOf(nombre);
      if (i > 0) pila.length = i;
      continue;
    }
    const padre = pila[pila.length - 1];
    const atributos = atributosHtml(resto);
    let alcance = padre.alcance;
    let pinta = padre.pinta;
    let visible = padre.visible;
    const evaluar = (nombreAtributo, expresion) => {
      try {
        return { valor: evaluarEn(alcance, expresion) };
      } catch (error) {
        problemas.push(`<${nombre} ${nombreAtributo}="${expresion}">: ${error.message}`);
        return { error };
      }
    };
    if (pinta && "x-for" in atributos) {
      const bucle = atributos["x-for"].match(BUCLE);
      if (!bucle) {
        problemas.push(`x-for ilegible: ${atributos["x-for"]}`);
        pinta = false;
      } else {
        const lista = evaluar("x-for", bucle[4]);
        const elementosDeLaLista = Array.isArray(lista.valor) ? lista.valor : [];
        if (!elementosDeLaLista.length) {
          pinta = false;
        } else {
          alcance = Object.create(alcance);
          alcance[bucle[1] || bucle[3]] = elementosDeLaLista[0];
          if (bucle[2]) alcance[bucle[2]] = 0;
        }
      }
    }
    if (pinta && "x-if" in atributos) {
      const condicion = evaluar("x-if", atributos["x-if"]);
      if (!condicion.valor) pinta = false;
    }
    if (pinta && "x-show" in atributos) {
      const condicion = evaluar("x-show", atributos["x-show"]);
      if (!condicion.valor) visible = false;
    }
    const antepasados = pila.slice(1).map((e) => ({ nombre: e.nombre, atributos: e.atributos }));
    if (pinta) {
      for (const [nombreAtributo, expresion] of Object.entries(atributos)) {
        if (["x-for", "x-if", "x-show", "x-data"].includes(nombreAtributo)) continue;
        if (DIRECTIVAS_DE_VALOR.test(nombreAtributo)) {
          evaluar(nombreAtributo, expresion);
        } else if (DIRECTIVAS_DE_EVENTO.test(nombreAtributo)) {
          const llamada = expresion.match(/^\s*([\w$.]+)\s*\(/);
          if (llamada) {
            const funcion = evaluar(nombreAtributo, llamada[1]);
            if (!funcion.error && typeof funcion.valor !== "function") {
              problemas.push(`<${nombre} ${nombreAtributo}="${expresion}">: ${llamada[1]} no es una función del componente`);
            }
          }
        }
      }
      elementos.push({ nombre, atributos, alcance, visible, antepasados });
    }
    if (!VACIOS_HTML.has(nombre) && !autocierre) {
      pila.push({ nombre, alcance, pinta, visible, atributos });
    }
  }
  return { elementos, problemas };
}

module.exports = { recorrer, evaluarEn, atributosHtml };
