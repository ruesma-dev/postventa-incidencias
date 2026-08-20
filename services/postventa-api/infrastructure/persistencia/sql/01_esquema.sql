-- services/postventa-api/infrastructure/persistencia/sql/01_esquema.sql
-- Construye: el esquema propio del proyecto. Lee de: nada.
--
-- Es lo primero que se aplica y lo único que crea un contenedor. La BASE de
-- datos NO se crea aquí ni desde ninguna parte de la aplicacion (R7): la crea
-- el humano una sola vez con infra/crear_base_postventa.ps1, porque crear
-- bases desde el arranque de un servicio en un servidor compartido con
-- produccion ajena es justo lo que prohibe CLAUDE.md.
--
-- El nombre 'postventa' aparece literal: si el despliegue configura otro
-- (PG_SCHEMA), ddl.py lo sustituye en el mismo paso en que valida.

CREATE SCHEMA IF NOT EXISTS postventa;
