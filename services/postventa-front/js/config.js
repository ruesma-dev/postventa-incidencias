// services/postventa-front/js/config.js
// Configuración del front. En local y en la Static Web App el backend cuelga
// del mismo origen (/api), así que no hay CORS ni URL que mantener: el proxy
// del dev_server y la Function enlazada a la SWA se comportan igual.
window.CONFIG_POSTVENTA = {
  baseApi: "/api",

  // Cuántos PARTES se procesan a la vez (D2, decisión del humano del
  // 2026-08-20). Tres partes son SEIS peticiones vivas —cada parte pide
  // /api/extraer y /api/firma en paralelo—, que es justo el máximo de
  // conexiones simultáneas por origen que abre un navegador sobre HTTP/1.1.
  // Pedir más no acelera nada: el navegador las encola igual, pero sin que el
  // usuario lo vea y con el temporizador de abajo corriendo. Además, en local
  // hay UN solo worker de `func start`, y 44 llamadas multimodales de golpe
  // son la forma más rápida de comerse un 429.
  // Cambiarlo es esta línea, no una búsqueda por el código.
  CONCURRENCIA_PARTES: 3,

  // Una petición que pase de aquí se aborta y se trata como error transitorio.
  // Sin esto, una petición colgada dejaría su plaza de la cola ocupada para
  // siempre y la remesa no terminaría nunca.
  //
  // 40 s, y el número NO es negociable a la ligera: sale del ESCALONADO de
  // tiempos que impone la plataforma (F-010, D2, `design.md` §5).
  //
  //     la IA abandona a los 35 s  →  el front aborta a los 40  →  el proxy
  //     de la Static Web App corta a los 45
  //
  // Cada capa cede ANTES que la de fuera. Ese orden es lo que hace que el
  // usuario reciba NUESTRO error —explicado, reintentable, y que libera la
  // plaza de la cola— en vez de un corte opaco del proxy con una llamada
  // zombi por detrás gastando cuota de IA.
  //
  // Subirlo por encima de 45 s no da más margen: da un corte del proxy que el
  // front no sabe que ha ocurrido. Si de verdad hiciera falta más tiempo, lo
  // que hay que cambiar es el montaje (patrón asíncrono), no este número.
  //
  // Medido antes de fijarlo (F-010, T2, con una remesa real de 22 partes): el
  // peor `/api/extraer` fue 6,5 s con seis peticiones vivas. Los 40 s son
  // colchón para el salto de región, el arranque en frío y un día malo del
  // proveedor de IA, no el caso normal.
  TIMEOUT_PETICION_MS: 40000,

  // Reintentos de lo TRANSITORIO (502, fallo de red, timeout) y sus esperas.
  // Un 400 no mejora repitiéndolo; un 503 de archivar es la puerta de entorno.
  REINTENTOS: 2,
  ESPERAS_MS: [1000, 3000],

  // Por debajo de esta confianza, el campo se destaca para que se mire antes
  // de confirmar nada. Es el umbral del dominio
  // (domain/models/firma.py::UMBRAL_CONFIANZA): no se inventa aquí.
  UMBRAL_CONFIANZA: 50,
};
