-- services/postventa-api/infrastructure/persistencia/sql/08_usuarios_sigrid.sql
-- Construye: la correspondencia entre el usuario de la aplicacion y su login
-- del ERP (F-009).
-- Lee de: 01_esquema.sql.
--
-- usuario_oid es DATO PERSONAL SEUDONIMO y es la CLAVE PRIMARIA: una sola fila
-- por usuario. Se guarda el identificador opaco de Entra ID y NUNCA el correo
-- ni el nombre.
--
-- Esta es la UNICA tabla del proyecto donde conviven las dos identidades, y esa
-- es su razon de existir. Las otras dos no las mezclan a proposito: en el log
-- del ERP va el login, porque es el ERP quien necesita saber quien ejecuto el
-- proceso; en postventa.cierres va solo el oid (R43), porque para reconstruir
-- que hicimos no hace falta saber quien es.
--
-- POR QUE UNA TABLA Y NO UNA COLUMNA EN preferencias_usuario: son dos cosas
-- distintas con dos duenos distintos. La preferencia la decide el usuario y su
-- fila nace sola al decidirla; el mapeo lo da de alta un administrador y su
-- AUSENCIA IMPIDE CERRAR. Fundirlas haria que guardar una preferencia creara
-- media identidad.
--
-- verificado_at_utc distingue una correspondencia CONFIRMADA -comprobada
-- contra dbo.usu y utilizable sin volver a preguntar (R29)- de un alta manual
-- todavia por confirmar, que tiene precedencia sobre la derivacion (R34) pero
-- NO exime de verificar antes de escribir en el log del ERP (R32). Es
-- anulable a proposito: no todo lo que hay aqui esta verificado.

CREATE TABLE IF NOT EXISTS postventa.usuarios_sigrid (
    usuario_oid       text PRIMARY KEY,
    login_sigrid      text        NOT NULL,
    alta_at_utc       timestamptz NOT NULL,
    verificado_at_utc timestamptz
);
