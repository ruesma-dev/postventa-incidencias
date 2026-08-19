-- services/postventa-api/infrastructure/persistencia/sql/03_partes.sql
-- Construye: la tabla de partes, la unidad de trabajo. Lee de: 02_remesas.sql.
--
-- 'hash_parte' es la CLAVE PRIMARIA: es la promesa de F-002 -el mismo parte,
-- venga de la remesa o suelto en un ZIP, da la misma huella- convertida en
-- restriccion de base de datos. Ahi viven R13-R16: reprocesar actualiza, no
-- duplica.
--
-- Los nueve campos de CAMPOS_DEL_PARTE van como COLUMNAS, no como un jsonb:
-- son un contrato cerrado, la cola humana filtra por ellos, y un jsonb
-- esconderia del information_schema justo lo que hay que poder auditar, que
-- es que columnas guardan dato personal.
--
-- DATO PERSONAL en esta tabla (design.md §6):
--   dni_cliente    -> personal DIRECTO (decision D2 del humano, 2026-08-19)
--   observaciones  -> personal DIRECTO (texto manuscrito del cliente)
--   descripcion    -> personal POSIBLE (puede citar a personas)
--   promocion, unidad -> personal INDIRECTO (localizan la vivienda)
-- El DNI vive SOLO aqui: ninguna otra tabla lo copia (R39).
--
-- NO hay ninguna columna binaria (R12, R40): el PDF vive en SharePoint. El
-- disco de este servidor es compartido, solo crece, y ya se lleno una vez.
--
-- NO hay raw_extraccion_json: duplicaria el DNI y las observaciones en un
-- blob de texto. La trazabilidad la da la traza de IA (R19).
--
-- 'fecha_servicio' es text y no date a proposito: F-003 devuelve el literal
-- que el modelo lee del papel, en el formato en que este escrito. Convertirlo
-- aqui seria inventar una interpretacion y perder el literal.
--
-- 'numero_incidencia' va INDEXADO pero NO UNICO (decision D4 del humano,
-- 2026-08-19): una incidencia puede tener mas de un parte, y un unico
-- rompería el dia que F-014 reagrupe un parte de dos hojas.

CREATE TABLE IF NOT EXISTS postventa.partes (
    hash_parte                  text PRIMARY KEY,

    remesa_id                   uuid        NOT NULL
                                REFERENCES postventa.remesas (id),
    origen                      text,
    paginas_origen              integer[]   NOT NULL DEFAULT '{}',
    modo_deteccion              text        NOT NULL,

    primera_vez_at_utc          timestamptz NOT NULL,
    actualizado_at_utc          timestamptz NOT NULL,
    reprocesos                  integer     NOT NULL DEFAULT 0,

    promocion                   text,
    codigo_obra                 text,
    unidad                      text,
    numero_incidencia           text,
    fecha_servicio              text,
    descripcion                 text,
    dni_cliente                 text,
    observaciones               text,
    numero_pagina               text,

    promocion_confianza_pct         integer NOT NULL DEFAULT 0,
    codigo_obra_confianza_pct       integer NOT NULL DEFAULT 0,
    unidad_confianza_pct            integer NOT NULL DEFAULT 0,
    numero_incidencia_confianza_pct integer NOT NULL DEFAULT 0,
    fecha_servicio_confianza_pct    integer NOT NULL DEFAULT 0,
    descripcion_confianza_pct       integer NOT NULL DEFAULT 0,
    dni_cliente_confianza_pct       integer NOT NULL DEFAULT 0,
    observaciones_confianza_pct     integer NOT NULL DEFAULT 0,
    numero_pagina_confianza_pct     integer NOT NULL DEFAULT 0,

    ia_proveedor                text,
    ia_modelo                   text,
    prompt_key                  text,
    prompt_version              text,
    prompt_huella               text,

    avisos_extraccion           jsonb NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS ix_partes_numero_incidencia
    ON postventa.partes (numero_incidencia);

CREATE INDEX IF NOT EXISTS ix_partes_codigo_obra
    ON postventa.partes (codigo_obra);

CREATE INDEX IF NOT EXISTS ix_partes_remesa
    ON postventa.partes (remesa_id);
