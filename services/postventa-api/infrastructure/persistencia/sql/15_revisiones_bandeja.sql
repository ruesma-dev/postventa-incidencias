-- services/postventa-api/infrastructure/persistencia/sql/15_revisiones_bandeja.sql
-- Construye: la REVISION de la bandeja de incidencias, una fila por accion
-- (editar, descartar, aprobar, recuperar) sobre una incidencia (F-056, R4, R36).
-- Lee de: 13_bandeja_incidencias.sql (la clave ajena).
--
-- APPEND-ONLY: cada accion anade una fila con la FOTO COMPLETA de los valores
-- vigentes tras ella (D-3), y ninguna modifica ni borra las anteriores ni la
-- fila de bandeja_incidencias, que es lo que mando la propiedad y no se toca.
-- Manda la de mayor revision_id (R38), nunca la hora: es lo que sirve el
-- indice. La concurrencia la resuelve un SELECT ... FOR UPDATE de la fila de la
-- bandeja dentro de la transaccion de escritura (R7), nunca un bloqueo
-- consultivo: su espacio de claves es del servidor compartido.
--
-- NO SE GUARDA EL ESTADO (nueva, editada, aprobada, descartada): se deriva de
-- la ultima revision (R1). Guardarlo divergiria del historico (F-026 -> F-028).
--
-- Los CHECK de longitud, de urgencia y listado y los tres de ambiguedad son los
-- de bandeja_incidencias, repetidos: la foto tiene las mismas invariantes y la
-- base las hace cumplir. El de accion lleva los valores del Enum AccionRevision
-- del dominio, y un test los compara. Ese CHECK NO SE PUEDE AMPLIAR DESPUES
-- (la guarda del DDL no deja cambiar un CHECK): el volcado a Sigrid de F-040
-- llevara su propia tabla. Por lo mismo, "aprobar exige oficio y ubicacion"
-- vive en el dominio y no en un CHECK.
--
-- revisado_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien
-- actua. Se escribe y no se lee: no sale en ninguna respuesta ni en ningun log.
--
-- revisado_correo es el CORREO CORPORATIVO de quien revisa (D-8, decision del
-- humano del 2026-10-06): dato personal de un empleado interno del grupo
-- posventa-usuarios, guardado para ensenar quien hizo cada cosa. Es la UNICA
-- columna de correo del esquema (R12): las demas tablas siguen con "el oid y
-- nada mas". Solo lo devuelven GET /api/revision (el de la ultima revision) y
-- GET /api/revision/historial (el de cada una), y NUNCA va a un log ni a un
-- mensaje de error. Es una traza de quien dice ser (sale de /.auth/me), no una
-- identidad verificada.
--
-- motivo es TEXTO LIBRE de quien descarta: solo en descartar, solo sale en el
-- historial y nunca en un log. descripcion y detalle son texto de la
-- propiedad, como en la bandeja.
--
-- Sin ON DELETE CASCADE: borrar una incidencia no puede llevarse su historico.
-- Ni columnas binarias ni JSON: cada valor en su columna, listas para el
-- datamart (F-048, que no publica el correo sin otra decision expresa).

CREATE TABLE IF NOT EXISTS postventa.revisiones_bandeja (
    revision_id       bigserial   PRIMARY KEY,
    incidencia_id     uuid        NOT NULL
                      REFERENCES postventa.bandeja_incidencias (incidencia_id),
    accion            text        NOT NULL
                      CHECK (accion IN ('editar', 'descartar', 'aprobar', 'recuperar')),
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
    huella_valores    text        NOT NULL,
    motivo            text        CHECK (char_length(motivo) <= 500),
    revisado_por      text        NOT NULL,
    revisado_correo   text        NOT NULL CHECK (char_length(revisado_correo) BETWEEN 3 AND 254),
    revisado_at_utc   timestamptz NOT NULL,
    CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL)),
    CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL)),
    CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL),
    CHECK (motivo IS NULL OR accion = 'descartar')
);

CREATE INDEX IF NOT EXISTS ix_revisiones_bandeja_incidencia
    ON postventa.revisiones_bandeja (incidencia_id, revision_id DESC);
