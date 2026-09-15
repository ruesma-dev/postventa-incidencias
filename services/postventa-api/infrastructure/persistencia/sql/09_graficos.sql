-- services/postventa-api/infrastructure/persistencia/sql/09_graficos.sql
-- Construye: la traza del parte adjunto a la reclamacion como GRAFICO de
-- Sigrid (F-012). Lee de: 03_partes.sql.
--
-- Es una tabla propia y no columnas en postventa.cierres porque es OTRA
-- escritura externa con otro ciclo de vida: "adjuntado pero no cerrado" es un
-- estado real que hay que poder representar, y 'cerrado' es terminal por
-- diseno de F-005. Mismo patron que archivos (F-006) y cierres (F-009): una
-- tabla por escritura externa, con hash_parte como clave y clave ajena contra
-- partes.
--
-- estado = 'adjuntado' es TERMINAL (R30): el repositorio no lo pisa. Es
-- ademas la PRIMERA CAPA DE IDEMPOTENCIA de la feature (R24): un reintento del
-- mismo parte se responde desde aqui, sin llamar a la pasarela y sin volver a
-- mandar los bytes del PDF.
--
-- NI UNA COLUMNA BINARIA (R45). El PDF vive en SharePoint y dentro de Sigrid;
-- el disco de este servidor es compartido, solo crece y ya se lleno una vez
-- (2026-08-09). De el se guardan el tamano y el sha256, que es lo que permite
-- comprobar despues que el fichero que hay en el ERP es el que se mando.
--
-- sha256 y hash_parte son DOS COSAS DISTINTAS y conviven a proposito: el
-- segundo es la huella de paginas del parte (F-002) y la clave de todas las
-- trazas; el primero es el hash de LOS BYTES EXACTOS enviados, y es lo unico
-- que la pasarela coteja y lo que decide su idempotencia.
--
-- reclamacion_ide es el con.ide de la reclamacion, guardado DESDE EL PRIMER
-- DRY-RUN: es la clave estable del ERP con la que el datamart cruzara nuestras
-- filas, mientras que numero_incidencia (con.cod) es legible pero no es clave.
-- Nace aqui para no tener que hacer un ALTER manana. Es anulable porque un
-- dry-run que falle antes de leer la reclamacion deja traza igual y no hay
-- ide que inventar.
--
-- confirmado_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de
-- quien confirmo, nunca su correo, su nombre ni su login del ERP (R44).
--
-- EXCEPCION DECLARADA A R44: gra_cod SI lleva el login del ERP dentro. Su
-- formato lo genera la pasarela y es AAAAMMDDHHMMSS + 4 digitos + '.' +
-- login. Se guarda entero porque es el identificador del grafico tal y como
-- Sigrid lo produce y es lo que hace falta para localizarlo; lo que no se
-- hace en ninguna parte es imprimir ese login por separado.
--
-- gra_ide_documental puede quedar NULL en el caso idempotente: la respuesta de
-- la pasarela no lo trae [MEDIDO]. No se inventa.

CREATE TABLE IF NOT EXISTS postventa.graficos (
    hash_parte           text PRIMARY KEY
                         REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    numero_incidencia    text NOT NULL,
    reclamacion_ide      integer,
    estado               text NOT NULL
                         CHECK (estado IN ('pendiente', 'dry_run_ok', 'adjuntado', 'error', 'ya_cerrada')),
    sha256               text,
    bytes                integer,
    nombre_fichero       text,
    gratipide            integer,
    gra_cod              text,
    gra_ide_negocio      integer,
    gra_ide_documental   integer,
    rcg_ide              integer,
    idempotente          boolean NOT NULL DEFAULT false,
    confirmado_por       text,
    motivo               text,
    intentos             integer NOT NULL DEFAULT 0,
    dry_run_at_utc       timestamptz,
    adjuntado_at_utc     timestamptz
);

CREATE INDEX IF NOT EXISTS ix_graficos_estado
    ON postventa.graficos (estado);
