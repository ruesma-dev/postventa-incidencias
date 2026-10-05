-- services/postventa-api/infrastructure/persistencia/sql/12_importaciones.sql
-- Construye: una fila por cada Excel de incidencias subido a la bandeja
-- (F-036, R39, R42, R70). Lee de: nada.
--
-- Que se guarda de cada subida (R42): quien, cuando, el nombre del fichero, su
-- sha256, la obra, la version de la plantilla, los recuentos -incluidas las
-- filas con error- y si fue COMPLETA o PARCIAL. NO se guardan los textos de
-- las filas con error ni el Excel de errores (R68): si se pierde, se recupera
-- subiendo otra vez el mismo fichero.
--
-- hash_fichero NO ES UNICO (enmienda del 2026-09-28): el mismo fichero de una
-- importacion parcial se vuelve a procesar para recuperar su Excel de errores.
-- El atajo de R39 ("ya_importado", sin escribir nada) solo vale para una
-- importacion COMPLETA, y busca por hash y estado: ese es el indice.
--
-- estado = 'parcial' si y solo si filas_con_error > 0 (R69, R70). Una
-- importacion con TODAS las filas con error consta, parcial y con 0 nuevas.
--
-- El CHECK de estado lleva los valores del Enum EstadoImportacion del dominio,
-- y un test (tests/test_f036_ddl.py) los compara: un valor nuevo en el dominio
-- que no llegue aqui rompe la suite y no produccion.
--
-- importado_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien
-- sube, y nada mas. NUNCA su correo ni su nombre. No sale en ningun log (R47).
-- nombre_fichero lo pone quien sube y puede llevar un nombre de persona:
-- tampoco sale en ningun log; el borde lo recorta a 255 caracteres.
--
-- NI UNA COLUMNA BINARIA: el .xlsx no se guarda.

CREATE TABLE IF NOT EXISTS postventa.importaciones (
    importacion_id              uuid        PRIMARY KEY,
    hash_fichero                text        NOT NULL,
    nombre_fichero              text        NOT NULL,
    obra_codigo                 text        NOT NULL,
    plantilla_version           integer     NOT NULL,
    estado                      text        NOT NULL CHECK (estado IN ('completa', 'parcial')),
    importado_por               text        NOT NULL,
    importado_at_utc            timestamptz NOT NULL,
    filas_leidas                integer     NOT NULL CHECK (filas_leidas >= 0),
    filas_con_error             integer     NOT NULL CHECK (filas_con_error >= 0),
    filas_nuevas                integer     NOT NULL DEFAULT 0 CHECK (filas_nuevas >= 0),
    filas_duplicadas_en_fichero integer     NOT NULL DEFAULT 0 CHECK (filas_duplicadas_en_fichero >= 0),
    filas_ya_en_bandeja         integer     NOT NULL DEFAULT 0 CHECK (filas_ya_en_bandeja >= 0),
    CHECK ((estado = 'parcial') = (filas_con_error > 0))
);

CREATE INDEX IF NOT EXISTS ix_importaciones_hash
    ON postventa.importaciones (hash_fichero, estado);
