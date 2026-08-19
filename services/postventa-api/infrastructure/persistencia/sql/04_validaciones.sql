-- services/postventa-api/infrastructure/persistencia/sql/04_validaciones.sql
-- Construye: el veredicto de cada parte (F-004). Lee de: 03_partes.sql.
--
-- 1:1 con el parte, y la clave primaria es la que lo garantiza: revalidar un
-- parte SUSTITUYE su veredicto, nunca acumula una segunda fila (R17).
--
-- Los valores de los CHECK son las etiquetas que de verdad emite el dominio
-- (Veredicto, Destino y ClasificacionFirma de F-004). Estan escritos aqui y
-- comparados contra los Enum por tests/test_f005_ddl_idempotente_texto.py: una
-- etiqueta nueva en el dominio que no llegue a la base rompe la suite, no
-- produccion (R20).
--
-- LAS OBSERVACIONES NO SE COPIAN AQUI (R21, R39). ResultadoValidacion las
-- transporta, pero su origen es la extraccion y ya estan en postventa.partes.
-- Una segunda copia de texto manuscrito de un cliente dobla la exposicion y
-- diverge. Quien las necesite las trae con un JOIN a partes.

CREATE TABLE IF NOT EXISTS postventa.validaciones (
    hash_parte          text PRIMARY KEY
                        REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    veredicto           text NOT NULL
                        CHECK (veredicto IN ('apto', 'no_apto')),
    destino             text NOT NULL
                        CHECK (destino IN ('archivo_y_cierre', 'cola_validacion_humana', 'revision_manual')),
    clasificacion_firma text NOT NULL
                        CHECK (clasificacion_firma IN ('humana', 'marca_simple', 'casilla_vacia', 'ilegible')),
    motivos             jsonb       NOT NULL DEFAULT '[]',
    avisos              jsonb       NOT NULL DEFAULT '[]',
    validado_at_utc     timestamptz NOT NULL
);

-- Indice parcial de la cola de validacion humana: solo indexa lo que se
-- consulta, que son los partes esperando que una persona decida.
CREATE INDEX IF NOT EXISTS ix_validaciones_cola
    ON postventa.validaciones (validado_at_utc)
    WHERE destino = 'cola_validacion_humana';
