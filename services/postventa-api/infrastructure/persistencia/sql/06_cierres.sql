-- services/postventa-api/infrastructure/persistencia/sql/06_cierres.sql
-- Construye: la traza del cierre en Sigrid (F-009). Lee de: 03_partes.sql.
--
-- estado = 'cerrado' es TERMINAL (R25): el repositorio no lo pisa. Volver a
-- cerrar una incidencia ya cerrada seria una escritura de mas en el ERP de
-- produccion.
--
-- estado_origen_sigrid y estado_destino_sigrid guardan EL CODIGO QUE SE
-- RESOLVIO CONTRA conest EN EJECUCION, como traza de lo que se hizo. No es
-- configuracion y nadie los lee para decidir: CHECKPOINTS.md C3 prohibe
-- hardcodear un estado de Sigrid, y registrarlo a posteriori no lo hace.
--
-- confirmado_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de
-- quien confirmo el cierre, nunca su correo ni su nombre.

CREATE TABLE IF NOT EXISTS postventa.cierres (
    hash_parte            text PRIMARY KEY
                          REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    numero_incidencia     text NOT NULL,
    estado                text NOT NULL
                          CHECK (estado IN ('pendiente', 'dry_run_ok', 'cerrado', 'error', 'ya_cerrada')),
    estado_origen_sigrid  text,
    estado_destino_sigrid text,
    dry_run_at_utc        timestamptz,
    cerrado_at_utc        timestamptz,
    confirmado_por        text,
    motivo                text,
    intentos              integer NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_cierres_estado
    ON postventa.cierres (estado);
