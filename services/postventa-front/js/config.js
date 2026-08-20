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
  TIMEOUT_PETICION_MS: 180000,

  // Reintentos de lo TRANSITORIO (502, fallo de red, timeout) y sus esperas.
  // Un 400 no mejora repitiéndolo; un 503 de archivar es la puerta de entorno.
  REINTENTOS: 2,
  ESPERAS_MS: [1000, 3000],

  // Por debajo de esta confianza, el campo se destaca para que se mire antes
  // de confirmar nada. Es el umbral del dominio
  // (domain/models/firma.py::UMBRAL_CONFIANZA): no se inventa aquí.
  UMBRAL_CONFIANZA: 50,
};
