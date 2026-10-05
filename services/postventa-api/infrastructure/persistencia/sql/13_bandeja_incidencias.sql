-- services/postventa-api/infrastructure/persistencia/sql/13_bandeja_incidencias.sql
-- Construye: la BANDEJA de incidencias de la propiedad, una fila por fila
-- buena de cada Excel importado (F-036, R37, R38, R41, R44, R99).
-- Lee de: 12_importaciones.sql.
--
-- LA NO DUPLICACION LA GARANTIZA LA BASE (R41), no una consulta previa: el
-- indice unico PARCIAL ux_bandeja_clave (obra, clave) solo entre las filas que
-- no son duplicadas de otra. Dos importaciones simultaneas del mismo contenido
-- no dejan dos filas no duplicadas con la misma clave. La segunda y siguientes
-- filas de un mismo fichero con la misma clave se guardan con duplicada_de
-- apuntando a la primera (R37); si la clave ya estaba en la bandeja de esa
-- obra, no se guarda ninguna del grupo (R38).
--
-- clave_duplicado es el sha256 hexadecimal de obra, unidad, ubicacion y
-- descripcion normalizadas (R35): no lleva texto legible.
--
-- oficio_ambiguo (R99): el grupo de oficio tiene varios codigos en la obra y
-- la fila no dice cual; va sin codigo y con su nombre, y lo decide una persona
-- en la bandeja (F-038, D-19). proveedor_ambiguo es la costura para F-050
-- (agrupacion de proveedores): en F-036 SIEMPRE es false, porque cada codigo
-- de proveedor es su propia opcion. No hay proveedor sin oficio: se comprueba
-- con el NOMBRE del oficio, porque un oficio ambiguo no lleva codigo.
--
-- Los CHECK de origen, urgencia y listado llevan los valores de los Enum del
-- dominio (OrigenIncidencia, Urgencia, Listado), y un test los compara. 'web'
-- entra ya (F-037, D-13): el guard del DDL no deja cambiar un CHECK despues.
--
-- NO HAY COLUMNA DE ESTADO DE REVISION (R44): la revision es de F-038, que la
-- anadira con su propia tabla, igual que F-028 hizo con el historico.
--
-- descripcion y detalle son TEXTO LIBRE DE LA PROPIEDAD, y proveedor_nombre
-- puede ser el nombre de un AUTONOMO: ninguno sale en ningun log (R47), y solo
-- los devuelve GET /api/bandeja a usuarios autenticados.
--
-- NI UNA COLUMNA BINARIA: ni el .xlsx ni el Excel de errores se guardan.

CREATE TABLE IF NOT EXISTS postventa.bandeja_incidencias (
    incidencia_id     uuid        PRIMARY KEY,
    origen            text        NOT NULL CHECK (origen IN ('excel', 'web')),
    importacion_id    uuid        REFERENCES postventa.importaciones (importacion_id),
    fila_origen       integer,
    obra_codigo       text        NOT NULL,
    unidad_codigo     text        NOT NULL,
    unidad_nombre     text        NOT NULL,
    ubicacion         text        CHECK (char_length(ubicacion) <= 48),
    descripcion       text        NOT NULL CHECK (char_length(descripcion) BETWEEN 1 AND 128),
    detalle           text        CHECK (char_length(detalle) <= 2000),
    oficio_codigo     text,
    oficio_nombre     text,
    oficio_ambiguo    boolean     NOT NULL DEFAULT false,
    proveedor_codigo  text,
    proveedor_nombre  text,
    proveedor_ambiguo boolean     NOT NULL DEFAULT false,
    urgencia          text        CHECK (urgencia IN ('urgente', 'seguridad')),
    listado           text        CHECK (listado IN ('primero', 'segundo')),
    clave_duplicado   text        NOT NULL,
    duplicada_de      uuid        REFERENCES postventa.bandeja_incidencias (incidencia_id),
    creada_at_utc     timestamptz NOT NULL,
    CHECK (origen <> 'excel' OR (importacion_id IS NOT NULL AND fila_origen IS NOT NULL)),
    CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL)),
    CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL)),
    CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_bandeja_clave
    ON postventa.bandeja_incidencias (obra_codigo, clave_duplicado)
    WHERE duplicada_de IS NULL;

CREATE INDEX IF NOT EXISTS ix_bandeja_obra
    ON postventa.bandeja_incidencias (obra_codigo, creada_at_utc DESC, fila_origen);
