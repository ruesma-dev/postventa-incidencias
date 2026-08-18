// services/postventa-front/js/config.js
// Configuración del front. En local y en la Static Web App el backend cuelga
// del mismo origen (/api), así que no hay CORS ni URL que mantener: el proxy
// del dev_server y la Function enlazada a la SWA se comportan igual.
window.CONFIG_POSTVENTA = {
  baseApi: "/api",
};
