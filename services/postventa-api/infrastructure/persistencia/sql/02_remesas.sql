-- services/postventa-api/infrastructure/persistencia/sql/02_remesas.sql
-- Construye: la tabla de remesas (una subida). Lee de: 01_esquema.sql.
--
-- 'id' es un uuid GENERADO EN PYTHON (domain.models.persistencia.nuevo_id):
-- gen_random_uuid() exigiria CREATE EXTENSION pgcrypto, que es una sentencia
-- de ambito de base de datos y esta prohibida (R6).
--
-- 'usuario_oid' es DATO PERSONAL SEUDONIMO: el identificador opaco de Entra ID
-- de quien sube la remesa, nunca su correo ni su nombre. Queda NULL hasta
-- F-007/F-010 (decision D6 del humano del 2026-08-19).

CREATE TABLE IF NOT EXISTS postventa.remesas (
    id               uuid PRIMARY KEY,
    nombre_origen    text        NOT NULL,
    recibida_at_utc  timestamptz NOT NULL,
    num_partes       integer     NOT NULL DEFAULT 0,
    avisos           jsonb       NOT NULL DEFAULT '[]',
    usuario_oid      text
);

CREATE INDEX IF NOT EXISTS ix_remesas_recibida
    ON postventa.remesas (recibida_at_utc);
