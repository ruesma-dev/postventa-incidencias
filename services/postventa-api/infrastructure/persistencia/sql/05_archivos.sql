-- services/postventa-api/infrastructure/persistencia/sql/05_archivos.sql
-- Construye: la traza del archivo en SharePoint (F-006). Lee de: 03_partes.sql.
--
-- La clave primaria por hash_parte es lo que hace verdad el acceptance de
-- F-006: subir dos veces el mismo parte no genera un duplicado (R23).
--
-- Aqui se guardan IDENTIFICADORES de SharePoint y metadatos, nunca los bytes
-- del PDF (R12, R40): el documento lleva el DNI manuscrito y vive alli.

CREATE TABLE IF NOT EXISTS postventa.archivos (
    hash_parte       text PRIMARY KEY
                     REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    estado           text NOT NULL
                     CHECK (estado IN ('pendiente', 'archivado', 'error')),
    nombre_fichero   text,
    carpeta          text,
    drive_id         text,
    item_id          text,
    web_url          text,
    motivo           text,
    intentos         integer NOT NULL DEFAULT 0,
    archivado_at_utc timestamptz
);

CREATE INDEX IF NOT EXISTS ix_archivos_estado
    ON postventa.archivos (estado);
