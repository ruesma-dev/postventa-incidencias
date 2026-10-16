-- services/postventa-api/infrastructure/persistencia/sql/16_volcados_sigrid.sql
-- Construye: los EVENTOS DEL VOLCADO de la bandeja a Sigrid, una fila por parte
-- y por intento, de ensayo o de volcado (F-059, R32).
-- Lee de: 13_bandeja_incidencias.sql y 15_revisiones_bandeja.sql (las claves
-- ajenas).
--
-- APPEND-ONLY: cada ensayo y cada volcado anaden filas, y ninguna se modifica ni
-- se borra. Manda el evento_id, nunca la hora: es lo que sirve el indice por
-- incidencia (el primer evento con parte y el ultimo de modo volcado). La
-- escritura anticipada (R20) inserta un evento 'enviado' ANTES de llamar a
-- Sigrid con commit: true, dentro de la transaccion que bloquea la fila de la
-- bandeja con un SELECT ... FOR UPDATE, nunca con un bloqueo consultivo: su
-- espacio de claves es del servidor compartido.
--
-- NO SE GUARDA EL ESTADO de la incidencia (volcada, en_duda): se deriva de los
-- eventos (R1). Los CHECK de modo y de estado llevan los valores de los Enum
-- ModoVolcado y EstadoEvento del dominio, y un test los compara: la guarda del
-- DDL no deja cambiar un CHECK despues. Los cuatro CHECK de fila: el ensayo no
-- lleva ensayo_id y el volcado si; un ensayo solo guarda lo que dice la pasarela
-- con commit: false; sigrid_ide y sigrid_cod van si y solo si el parte existe
-- ('creado', 'idempotente'); y 'rechazado' y 'no_procesado' llevan su codigo.
--
-- SIN INDICE UNICO sobre 'creado', a proposito (R26): si Sigrid llegara a crear
-- dos partes de la misma incidencia, la segunda fila tiene que PODER GUARDARSE y
-- avisar, no fallar despues de haber escrito en el ERP.
--
-- actor_oid es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien ensaya
-- o vuelca. Se escribe y NO SE LEE NUNCA: la lectura del ensayo lo compara en la
-- base con el de quien pide y solo devuelve si coincide (B-1 (a), R17, R33).
--
-- actor_correo es el CORREO CORPORATIVO de quien ensaya o vuelca (D-8), como
-- revisado_correo de 15_revisiones_bandeja.sql: dato personal de un
-- empleado interno del grupo posventa-usuarios. Solo lo devuelve
-- GET /api/revision (el de quien volco) y NUNCA va a un log ni a un mensaje de
-- error.
--
-- Ni descripciones, ni nombres, ni el login de Sigrid, ni el motivo.mensaje de
-- la pasarela: del motivo, solo su codigo (R35). La referencia_externa es 'PVI-'
-- y el incidencia_id: la llave de la idempotencia en Sigrid (R5).
--
-- Sin ON DELETE CASCADE: borrar una incidencia no puede llevarse la traza de lo
-- que se escribio en el ERP. Ni columnas binarias ni JSON: cada valor en su
-- columna, listas para el datamart (F-048).

CREATE TABLE IF NOT EXISTS postventa.volcados_sigrid (
    evento_id          bigserial   PRIMARY KEY,
    llamada_id         uuid        NOT NULL,
    modo               text        NOT NULL CHECK (modo IN ('ensayo', 'volcado')),
    ensayo_id          uuid,
    incidencia_id      uuid        NOT NULL
                       REFERENCES postventa.bandeja_incidencias (incidencia_id),
    revision_id        bigint      NOT NULL
                       REFERENCES postventa.revisiones_bandeja (revision_id),
    huella_valores     text        NOT NULL,
    obra_codigo        text        NOT NULL,
    referencia_externa text        NOT NULL
                       CHECK (referencia_externa LIKE 'PVI-%'
                              AND char_length(referencia_externa) <= 80),
    estado             text        NOT NULL CHECK (estado IN ('previsto', 'enviado',
                       'creado', 'idempotente', 'rechazado', 'no_procesado', 'sin_respuesta')),
    motivo_codigo      text        CHECK (char_length(motivo_codigo) BETWEEN 1 AND 64),
    sigrid_ide         bigint,
    sigrid_cod         text        CHECK (char_length(sigrid_cod) <= 24),
    actor_oid          text        NOT NULL,
    actor_correo       text        NOT NULL CHECK (char_length(actor_correo) BETWEEN 3 AND 254),
    at_utc             timestamptz NOT NULL,
    CHECK ((modo = 'ensayo') = (ensayo_id IS NULL)),
    CHECK (modo = 'volcado'
           OR estado IN ('previsto', 'idempotente', 'rechazado', 'no_procesado')),
    CHECK ((estado IN ('creado', 'idempotente'))
           = (sigrid_ide IS NOT NULL AND sigrid_cod IS NOT NULL)),
    CHECK (estado NOT IN ('rechazado', 'no_procesado') OR motivo_codigo IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_incidencia
    ON postventa.volcados_sigrid (incidencia_id, evento_id DESC);
CREATE INDEX IF NOT EXISTS ix_volcados_sigrid_llamada
    ON postventa.volcados_sigrid (llamada_id);
