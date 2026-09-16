-- services/postventa-api/infrastructure/persistencia/sql/11_historico_estado.sql
-- Construye: el HISTORICO APPEND-ONLY de los cambios de estado de un parte
-- (F-028, R21 a R26). Lee de: 03_partes.sql y, solo para la semilla,
-- 10_aprobaciones.sql.
--
-- ESTA TABLA NO SE PISA. Es la primera del esquema cuya clave NO es el
-- hash_parte, y es deliberado: el historico ACUMULA, ese es su oficio. Las
-- diez tablas anteriores se escriben con INSERT ... ON CONFLICT (hash_parte)
-- DO UPDATE porque de cada una de ellas solo interesa el ultimo estado; aqui
-- interesan TODOS, en orden. Un ON CONFLICT encima de esta tabla la
-- convertiria en una segunda tabla de "ultima decision", que es exactamente
-- lo que ya existe y lo que no sirve.
--
-- El motivo esta medido, no es preferencia: postventa.aprobaciones tiene
-- clave primaria hash_parte y ON CONFLICT DO UPDATE, asi que un ciclo
-- aprobar -> rechazar -> aprobar deja UNA fila y borra el rechazo por el
-- camino. Nadie puede responder despues a "quien lo rechazo y por que", que
-- es justo lo que F-028 viene a arreglar (R25).
--
-- Y por eso esta tabla es NUEVA y aprobaciones NO SE MIGRA: volverla
-- append-only exigiria cambiarle la clave primaria, y eso en una base
-- COMPARTIDA y ya desplegada con datos reales es una migracion de verdad, no
-- un ADD COLUMN. Se congela, se siembra (abajo) y se deja de escribir.
--
-- CONSTANCIA, NUNCA CRITERIO (R26). El estado de un parte NO SE GUARDA: se
-- DERIVA, y quien lo deriva es domain/models/estado.py a partir del veredicto
-- (04_validaciones), de la ultima decision humana de aqui y de la traza de
-- cierre (06_cierres). De esta tabla nadie decide nada leyendo una fila de
-- maquina; lo unico que se consulta de ellas es cual fue el ultimo estado
-- registrado, y solo para no repetir fila. Si manana faltara una fila, el
-- estado seguiria siendo el correcto y lo unico perdido seria una linea del
-- relato.
--
-- cambio_id es un bigserial y no el hash_parte, por lo de arriba. Sirve
-- ademas para desempatar dos cambios del mismo parte en el mismo instante:
-- el orden es (decidido_at_utc DESC, cambio_id DESC), y es el del indice.
--
-- decidido_por ADMITE NULL, y ese NULL significa LO DECIDIO LA MAQUINA (R24).
-- Escribir ahi 'sistema' seria inventarse un autor, y convertiria una
-- anotacion en una acusacion. Es ademas lo unico que distingue la fila humana
-- -la que manda sobre la maquina, R9- de la de constancia.
--
-- decidido_por es DATO PERSONAL SEUDONIMO: el oid opaco de Entra ID de quien
-- decidio, y nada mas. NUNCA su correo, NUNCA su nombre y NUNCA su login del
-- ERP (R15). Mismo tratamiento y misma nota que aprobaciones.aprobado_por,
-- cierres.confirmado_por y graficos.confirmado_por. Y NO SALE EN NINGUN LOG
-- ni en ninguna respuesta HTTP (R52): quien audite lo lee aqui.
--
-- motivo es TEXTO LIBRE DE QUIEN REVISA, no del papel: por que alguien
-- rechaza un parte. Puede llevar nombres de personas, asi que tampoco sale en
-- ningun log ni en ninguna respuesta (R52), y el borde lo acota a 500
-- caracteres. No confundirlo con aprobaciones.revocada_motivo, que es una
-- etiqueta corta y cerrada.
--
-- NI UNA COPIA DEL TEXTO MANUSCRITO. Las observaciones del cliente y su DNI
-- viven en postventa.partes y en ningun otro sitio. Sobre QUE VEREDICTO se
-- decidio se guarda como HUELLA: huella_veredicto es el sha256 en hexadecimal
-- de domain/models/aprobacion.py::huella_de_veredicto, el mismo criterio de
-- F-026 y sin una letra del papel dentro. Es lo que hace que una aprobacion
-- deje de contar cuando el veredicto cambia (R19).
--
-- Los dos CHECK de estado llevan los cuatro valores del Enum EstadoParte de
-- F-028, y un test los compara con el: un estado nuevo en el dominio que no
-- llegue aqui rompe la suite y no produccion. estado_anterior admite NULL
-- porque la primera fila de un parte no viene de ningun sitio.
--
-- NI UNA COLUMNA BINARIA: aqui no entra el PDF, como en ninguna otra.

CREATE TABLE IF NOT EXISTS postventa.historico_estado (
    cambio_id        bigserial   PRIMARY KEY,
    hash_parte       text        NOT NULL
                     REFERENCES postventa.partes (hash_parte) ON DELETE CASCADE,
    estado_anterior  text
                     CHECK (estado_anterior IN ('pendiente', 'aprobado', 'rechazado', 'cerrado')),
    estado           text        NOT NULL
                     CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'cerrado')),
    decidido_por     text,
    decidido_at_utc  timestamptz NOT NULL,
    motivo           text,
    huella_veredicto text
);

-- El indice es el de select_situacion_estado, columna por columna: por parte,
-- lo mas reciente primero y con el contador para desempatar. Se indexa lo que
-- se consulta y nada mas, como ix_validaciones_cola: un indice de mas en un
-- Standard_B1ms de 1 vCPU compartido con otros tres proyectos lo pagan ellos.
CREATE INDEX IF NOT EXISTS ix_historico_estado_parte
    ON postventa.historico_estado (hash_parte, decidido_at_utc DESC, cambio_id DESC);

-- SEMILLA de las aprobaciones VIGENTES de F-026. Se ejecuta con el resto del
-- DDL en cada arranque, antes de atender ninguna peticion, y es IDEMPOTENTE
-- por el NOT EXISTS: un parte que ya tenga historico no se vuelve a sembrar.
--
-- Sin ella, el dia del despliegue todo parte aprobado a mano se quedaria sin
-- su decision humana: postventa.aprobaciones deja de leerse, el historico
-- estaria vacio y el estado caeria al de la maquina. Alguien tendria que
-- volver a aprobar a mano lo que ya aprobo.
--
-- Las aprobaciones YA REVOCADAS no se siembran: su efecto hoy es "no hay
-- aprobacion", y sembrarlas las resucitaria como ultima decision humana del
-- parte, abriendole otra vez la puerta del circuito que escribe en el ERP de
-- produccion. Siguen consultables en su tabla congelada.
--
-- estado_anterior va a NULL y no a 'pendiente': de donde venia ese parte no
-- consta en ningun sitio, y no se inventa.
INSERT INTO postventa.historico_estado
    (hash_parte, estado_anterior, estado, decidido_por, decidido_at_utc, motivo, huella_veredicto)
SELECT a.hash_parte, NULL, 'aprobado', a.aprobado_por, a.aprobado_at_utc,
       'semilla de F-026', a.huella_aprobada
FROM postventa.aprobaciones AS a
WHERE a.revocada_at_utc IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM postventa.historico_estado AS h
      WHERE h.hash_parte = a.hash_parte
  );
