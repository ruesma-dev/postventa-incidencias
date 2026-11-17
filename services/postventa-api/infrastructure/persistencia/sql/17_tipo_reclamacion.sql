-- services/postventa-api/infrastructure/persistencia/sql/17_tipo_reclamacion.sql
-- Construye: la columna tipo_reclamacion de la bandeja y de la revision (F-072, R16).
-- Capa: persistencia, esquema postventa.
-- Lee de: 13_bandeja_incidencias.sql y 15_revisiones_bandeja.sql (las tablas
-- que amplia, por eso va detras de ellas).
--
-- tipo_reclamacion es el CODIGO del tipo de reclamacion de Sigrid (dbo.auxtrcp,
-- columna cod), elegido al importar o en la revision: hasta 24 caracteres, el
-- CHECK de abajo, igual que MAX_TIPO_RECLAMACION del dominio.
--
-- Es una COLUMNA NUEVA y no un CHECK nuevo sobre listado: la guarda del DDL
-- (ddl.py) no deja cambiar un CHECK ya creado, y el listado de F-036 (primero,
-- segundo) se queda como esta. Ningun DDL de F-072 toca listado (R18): se sigue
-- leyendo y copiando, pero lo nuevo nace con listado nulo (R15).
--
-- Admite nulo y no lleva DEFAULT: nulo = fila anterior a F-072, cuyo tipo
-- efectivo es 0002 (R19). Sin UPDATE (la guarda tampoco lo admite): lo heredado
-- no se migra en la base, se interpreta en el dominio (tipo_efectivo).
--
-- Una columna nula sin defecto solo toca el catalogo y no reescribe la tabla,
-- pero pide un bloqueo exclusivo breve y hay que ser DUENO de la tabla: es el
-- primer ALTER TABLE de este proyecto en produccion (Q-3 de F-072).

ALTER TABLE postventa.bandeja_incidencias ADD COLUMN IF NOT EXISTS tipo_reclamacion text CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24);
ALTER TABLE postventa.revisiones_bandeja ADD COLUMN IF NOT EXISTS tipo_reclamacion text CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24);
