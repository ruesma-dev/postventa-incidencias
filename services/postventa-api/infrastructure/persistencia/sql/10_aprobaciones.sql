-- services/postventa-api/infrastructure/persistencia/sql/10_aprobaciones.sql
-- Construye: el registro de que UNA PERSONA aprobo un parte que la validacion
-- automatica habia mandado a revision (F-026). Lee de: 03_partes.sql.
--
-- Es una tabla propia y NO una columna en postventa.validaciones, y el motivo
-- es medido: upsert_validacion hace ON CONFLICT (hash_parte) DO UPDATE SET
-- sobre TODAS las columnas menos la clave, y POST /api/parte recalcula y
-- vuelve a guardar el veredicto en cada revalidacion. Una columna
-- "aprobado_por" ahi duraria hasta el siguiente guardado, o sea hasta que
-- alguien corrigiera una coma. Mismo patron que archivos (F-006), cierres
-- (F-009) y graficos (F-012): UNA TABLA POR HECHO CON CICLO DE VIDA PROPIO.
--
-- Y hay una segunda razon, que es el requisito: la aprobacion se registra AL
-- LADO del veredicto, NUNCA ENCIMA. Escribir 'apto' donde la maquina dijo
-- 'no_apto' borraria el motivo por el que alguien tuvo que decidir, y haria
-- indistinguible el parte que siempre fue verde del que una persona dio por
-- bueno A PESAR de la maquina. Esa distincion es justo lo que F-026 existe
-- para registrar.
--
-- aprobado_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien
-- aprobo, y nada mas. NUNCA su correo, NUNCA su nombre y NUNCA su login del
-- ERP (R13). Mismo tratamiento y misma nota que cierres.confirmado_por y
-- graficos.confirmado_por. Para saber que alguien decidio no hace falta saber
-- quien es; quien necesite auditarlo cruza por hash_parte con cierres y
-- graficos, que ya llevan el numero de incidencia y el ide de la reclamacion.
--
-- NI UNA COPIA DEL TEXTO MANUSCRITO (R15). Las observaciones del cliente ya
-- viven en postventa.partes, y una segunda copia dobla la exposicion y
-- diverge. Sobre QUE VEREDICTO se decidio se guarda como HUELLA.
--
-- huella_aprobada es un sha256 en hexadecimal de destino + codigos de motivo
-- ordenados + clasificacion de firma + observaciones normalizadas
-- (domain/models/aprobacion.py). Es lo que decide la vigencia: cuando se
-- guarda una validacion cuya huella ya no es esta, la aprobacion se REVOCA en
-- la misma operacion. Se compara por huella y no por fecha porque recuperar
-- el trabajo tras recargar la pantalla exige volver a subir la remesa, y eso
-- reprocesa cada parte: caducar por tiempo invalidaria todas las aprobaciones
-- en el unico gesto con el que se recuperan.
--
-- destino_aprobado es DE DONDE SE RESCATO el parte, con CHECK y solo los dos
-- destinos NO APTOS: aprobar un 'archivo_y_cierre' no significa nada, porque
-- ahi no hay nada que aprobar. Los literales son los que emite el Enum
-- Destino de F-004 y un test los compara con el, asi que una etiqueta nueva
-- en el dominio que no llegue aqui rompe la suite y no produccion.
--
-- motivos_aprobados guarda CODIGOS, no textos: ["firma_no_humana"]. El texto
-- de un motivo es redaccion para Posventa y puede cambiar; el codigo es
-- contrato de F-004.
--
-- validado_at_utc es QUE VALIDACION se aprobo. Es traza, no criterio: quien
-- decide la vigencia es la huella.
--
-- revocada_at_utc / revocada_motivo: revocar NO BORRA (R33). La decision se
-- tomo, y quien la tomo y cuando sigue siendo informacion. NULL es "vigente",
-- y el indice parcial indexa solo eso, que es lo unico que se consulta -mismo
-- patron que ix_validaciones_cola-. revocada_motivo es una ETIQUETA CORTA Y
-- CERRADA ('veredicto_cambiado'), nunca el texto que la provoco.
--
-- hash_parte es clave primaria Y clave ajena: una sola aprobacion por parte
-- (R17) y ninguna aprobacion de un parte que no conste guardado. Es la misma
-- restriccion que sostiene la garantia de orden de F-019 y por el mismo
-- motivo: lo impone la base, no una comprobacion previa en Python.
--
-- NI UNA COLUMNA BINARIA (R12): aqui no entra el PDF, como en ninguna otra.

CREATE TABLE IF NOT EXISTS postventa.aprobaciones (
    hash_parte        text PRIMARY KEY
                      REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    aprobado_por      text        NOT NULL,
    aprobado_at_utc   timestamptz NOT NULL,
    destino_aprobado  text        NOT NULL
                      CHECK (destino_aprobado IN ('cola_validacion_humana', 'revision_manual')),
    motivos_aprobados jsonb       NOT NULL DEFAULT '[]',
    huella_aprobada   text        NOT NULL,
    validado_at_utc   timestamptz NOT NULL,
    revocada_at_utc   timestamptz,
    revocada_motivo   text
);

CREATE INDEX IF NOT EXISTS ix_aprobaciones_vigentes
    ON postventa.aprobaciones (aprobado_at_utc)
    WHERE revocada_at_utc IS NULL;
