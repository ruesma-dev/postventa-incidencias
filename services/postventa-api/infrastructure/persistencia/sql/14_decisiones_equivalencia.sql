-- services/postventa-api/infrastructure/persistencia/sql/14_decisiones_equivalencia.sql
-- Construye: las DECISIONES HUMANAS sobre codigos casi duplicados de un
-- catalogo de Sigrid, por pares y APPEND-ONLY (F-036, R81, R83, R95, R108).
-- Lee de: nada.
--
-- Una persona confirma que dos codigos son el mismo oficio ("mismo") o que no
-- lo son ("distinto"). Se guarda POR PARES y NADA LA ACTUALIZA NI LA BORRA:
-- manda la ULTIMA fila de cada (catalogo, codigo_a, codigo_b), que es lo que
-- lee el indice. Una decision "distinto" sobre un par confirmado lo separa.
-- Como historico_estado, decision_id es un bigserial y desempata dos
-- decisiones del mismo par en el mismo instante.
--
-- UNA tabla con discriminador catalogo, y no una por catalogo: el mecanismo es
-- uno, y un codigo de oficio y otro de proveedor que se escriban igual nunca
-- se confunden porque el par se identifica con su catalogo (R95).
--
-- LA COSTURA (R108): el CHECK de catalogo admite YA 'oficio', 'proveedor' y
-- 'actividad_oficio', aunque F-036 solo escriba 'oficio'. 'proveedor' es de
-- F-050 y 'actividad_oficio' de F-039; el guard del DDL no deja ampliar un
-- CHECK despues, y asi ninguna de las dos tendra que tocar el esquema. Un test
-- compara el CHECK con el Enum Catalogo del dominio (mas 'actividad_oficio').
--
-- El par va EN ORDEN (codigo_a < codigo_b), como exige DecisionPar en el
-- dominio con el orden de Python, que es por punto de codigo. La comparacion
-- lleva COLLATE "C" (en UTF-8, orden de bytes = orden de puntos de codigo):
-- con la intercalacion por defecto de la base, dos codigos con letras podrian
-- ordenarse distinto que en Python y el INSERT fallaria (aviso B2-14).
--
-- NI UN NOMBRE (R83): solo el catalogo, los codigos de Sigrid, la decision,
-- los motivos que se propusieron (p. ej. 'errata,plural'), la obra desde la
-- que se decidio -la decision vale para todas, R84- y quien y cuando. Los
-- nombres se leen de Sigrid cada vez.
--
-- decidido_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien
-- decide, y nada mas. No sale en ningun log (R47).

CREATE TABLE IF NOT EXISTS postventa.decisiones_equivalencia (
    decision_id     bigserial   PRIMARY KEY,
    catalogo        text        NOT NULL CHECK (catalogo IN ('oficio', 'proveedor', 'actividad_oficio')),
    codigo_a        text        NOT NULL,
    codigo_b        text        NOT NULL,
    decision        text        NOT NULL CHECK (decision IN ('mismo', 'distinto')),
    motivos         text,
    obra_codigo     text        NOT NULL,
    decidido_por    text        NOT NULL,
    decidido_at_utc timestamptz NOT NULL,
    CHECK (codigo_a COLLATE "C" < codigo_b COLLATE "C")
);

CREATE INDEX IF NOT EXISTS ix_decisiones_equivalencia_par
    ON postventa.decisiones_equivalencia (catalogo, codigo_a, codigo_b, decidido_at_utc DESC, decision_id DESC);
