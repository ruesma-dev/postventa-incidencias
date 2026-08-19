-- services/postventa-api/infrastructure/persistencia/sql/07_preferencias.sql
-- Construye: la preferencia de auto-cierre por usuario (F-010).
-- Lee de: 01_esquema.sql.
--
-- usuario_oid es DATO PERSONAL SEUDONIMO y es la CLAVE PRIMARIA: una sola fila
-- por usuario (R27). Se guarda el identificador opaco de Entra ID y NUNCA el
-- correo ni el nombre: para saber si alguien tiene auto-cierre no hace falta
-- saber quien es.
--
-- Revocar es dejar auto_cierre en false con su marca de tiempo (R28): un
-- booleano y una fecha bastan, y asi no hay dos maneras de estar revocado.
--
-- El valor por defecto es false, y no por comodidad: el auto-cierre escribe en
-- el ERP de produccion.

CREATE TABLE IF NOT EXISTS postventa.preferencias_usuario (
    usuario_oid        text PRIMARY KEY,
    auto_cierre        boolean     NOT NULL DEFAULT false,
    actualizado_at_utc timestamptz NOT NULL
);
