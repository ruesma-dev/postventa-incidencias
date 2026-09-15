# services/postventa-api/tests/test_f009_usuarios_sigrid.py
"""Quién firma el cierre: la correspondencia `oid` → login (F-009, R29–R34).

**Este es el requisito que decide de quién dice el ERP que cerró la
incidencia.** El error, si lo hay, no es un fallo técnico: es firmar en el log
de un ERP de producción el cierre de una persona que no lo hizo.

El mecanismo que resolvió el humano el 2026-08-26 —«el correo manda y el login
se confirma una vez»— se apoya en un supuesto que **la base no confirma**: de
los 228 usuarios del ERP, ninguno tiene correo registrado, y de los 8 que lo
tienen en la tabla de usuario×empresa, solo 6 cumplen la convención. Lo que
hace seguro apoyarse en un supuesto así es un paso, y es el que estos tests
vigilan: el supuesto **propone**, el ERP **dispone**, y solo lo que el ERP
confirma se guarda y se escribe.

Los seis requisitos:

- **R29** · si hay correspondencia confirmada, se usa **sin derivar nada**.
- **R30** · si no la hay, se deriva del correo y **se verifica contra el ERP**.
- **R31** · candidato inexistente o ambiguo → **no se cierra**.
- **R32** · jamás se escribe un login sin verificar.
- **R33** · lo verificado se guarda como confirmado.
- **R34** · el alta manual tiene **precedencia** sobre la derivación.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from application.pipelines.paso_cierre import resolver_login_de_sigrid
from domain.models.cierre import CorrespondenciaSigrid, derivar_login_candidato
from domain.models.errores import (
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)
from domain.models.persistencia import ResultadoGuardado
from infrastructure.persistencia.mapeo import fila_a_correspondencia
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres
from infrastructure.persistencia.sentencias import (
    select_login_sigrid,
    upsert_login_sigrid,
)

from tests.utiles_pg import ConexionDoble
from tests.utiles_sigrid import ErpEnMemoria

#: Un instante fijo: los tests no miran el reloj.
AHORA = datetime(2026, 8, 26, 9, 46, 33, tzinfo=UTC)

#: Un `oid` de Entra inventado. No es de nadie.
OID = "oid-inventado-para-el-test"

#: Un correo inventado, de un dominio que no existe.
CORREO = "fulanito@ejemplo.invalido"


class UsuariosEnMemoria:
    """Un `RepositorioUsuariosSigridPort` de mentira, sin SQL de por medio."""

    def __init__(self, correspondencia: CorrespondenciaSigrid | None = None) -> None:
        self.correspondencia = correspondencia
        self.guardadas: list[CorrespondenciaSigrid] = []
        self.consultas: list[str] = []

    def resolver_login(self, *, usuario_oid: str):
        self.consultas.append(usuario_oid)
        return self.correspondencia

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        self.guardadas.append(correspondencia)
        return ResultadoGuardado.CREADO


# --------------------------------------------------------------------------
# R30 · la derivación, que es la SIEMBRA y no el mecanismo
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("correo", "esperado"),
    [
        ("fulanito@ejemplo.invalido", "fulanito"),
        ("  Fulanito@Ejemplo.Invalido  ", "fulanito"),
        ("fulanito.perez@ejemplo.invalido", "fulanito.perez"),
    ],
)
def test_f009_r30_el_candidato_se_deriva_de_la_parte_local_del_correo(correo, esperado):
    """R30 · lo que dijo el humano: «es el mismo el de la app y el de Sigrid».

    Se normaliza a minúsculas porque un login no es dos logins por cómo lo
    escriba el proveedor de identidad, y porque el maestro del ERP los tiene en
    minúsculas.
    """
    assert derivar_login_candidato(correo) == esperado


@pytest.mark.parametrize("correo", [None, "", "   ", "sin-arroba", "@solodominio"])
def test_f009_r30_de_un_correo_que_no_lo_es_no_se_deriva_nada(correo):
    """R30 · sin correo utilizable no hay candidato, y eso no se inventa."""
    assert derivar_login_candidato(correo) == ""


# --------------------------------------------------------------------------
# R29 y R34 · lo guardado manda sobre la derivación
# --------------------------------------------------------------------------


def test_f009_r29_una_correspondencia_confirmada_se_usa_sin_derivar_ni_preguntar():
    """R29 · **la derivación es la siembra, no el mecanismo de cada cierre.**

    El segundo cierre de una persona no vuelve a proponerle un candidato al ERP:
    ya está confirmado. Se comprueba que no se hizo ni una verificación.
    """
    usuarios = UsuariosEnMemoria(
        CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid="loginraro",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )
    )
    erp = ErpEnMemoria()

    login = resolver_login_de_sigrid(
        usuarios, erp, usuario_oid=OID, correo=CORREO, ahora=AHORA
    )

    assert login == "loginraro"
    assert erp.verificaciones == []
    assert usuarios.guardadas == []


def test_f009_r34_un_alta_manual_tiene_precedencia_sobre_la_derivacion():
    """R34 · la salida para los 2 de 8 medidos que no siguen la convención.

    El login que un administrador dio de alta a mano **gana** al que saldría del
    correo. Si no fuera así, la tabla no serviría de nada: existe justamente
    para los casos en los que la convención falla.
    """
    usuarios = UsuariosEnMemoria(
        CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid="jperez",
            alta_at_utc=AHORA,
            verificado_at_utc=None,
        )
    )
    erp = ErpEnMemoria(existe_login=True)

    login = resolver_login_de_sigrid(
        usuarios, erp, usuario_oid=OID, correo=CORREO, ahora=AHORA
    )

    assert login == "jperez"
    assert erp.verificaciones == ["jperez"]


def test_f009_r32_un_alta_manual_sin_verificar_si_se_verifica_antes_de_escribir():
    """R32 · precedencia **no** es exención: se comprueba contra el ERP igual.

    Un alta manual dice «este es el login»; el ERP dice si existe. Dar por bueno
    lo primero sin lo segundo sería firmar con un login que nadie ha comprobado,
    que es exactamente lo que R32 prohíbe.
    """
    usuarios = UsuariosEnMemoria(
        CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid="noexiste",
            alta_at_utc=AHORA,
            verificado_at_utc=None,
        )
    )
    erp = ErpEnMemoria(existe_login=False)

    with pytest.raises(UsuarioSigridInexistente):
        resolver_login_de_sigrid(
            usuarios, erp, usuario_oid=OID, correo=CORREO, ahora=AHORA
        )


def test_f009_r33_lo_verificado_se_guarda_como_confirmado_con_su_marca():
    """R33 · para que el segundo cierre de esa persona no derive nada."""
    usuarios = UsuariosEnMemoria(None)
    erp = ErpEnMemoria(existe_login=True)

    resolver_login_de_sigrid(
        usuarios, erp, usuario_oid=OID, correo=CORREO, ahora=AHORA
    )

    assert len(usuarios.guardadas) == 1
    guardada = usuarios.guardadas[0]
    assert guardada.usuario_oid == OID
    assert guardada.login_sigrid == "fulanito"
    assert guardada.verificado_at_utc == AHORA
    assert guardada.confirmada is True


def test_f009_r33_una_correspondencia_confirmada_no_se_vuelve_a_guardar():
    """R33 · guardar en cada cierre sería escribir en la base por costumbre."""
    usuarios = UsuariosEnMemoria(
        CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid="fulanito",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )
    )

    resolver_login_de_sigrid(
        usuarios, ErpEnMemoria(), usuario_oid=OID, correo=CORREO, ahora=AHORA
    )

    assert usuarios.guardadas == []


# --------------------------------------------------------------------------
# R31 · sin confirmación, no se cierra
# --------------------------------------------------------------------------


def test_f009_r31_un_candidato_que_no_existe_en_el_erp_no_cierra_nada():
    """R31 · y el mensaje nombra el correo **y** el login que se intentó.

    Sin esas dos cosas, quien lo recibe no puede dar de alta la correspondencia:
    no sabría ni de quién es el problema ni qué se probó.
    """
    usuarios = UsuariosEnMemoria(None)
    erp = ErpEnMemoria(existe_login=False)

    with pytest.raises(UsuarioSigridInexistente) as fallo:
        resolver_login_de_sigrid(
            usuarios, erp, usuario_oid=OID, correo=CORREO, ahora=AHORA
        )

    assert CORREO in fallo.value.motivo
    assert "fulanito" in fallo.value.motivo
    assert "alta" in fallo.value.motivo.lower()


def test_f009_r32_un_candidato_no_verificado_no_se_guarda_jamas():
    """R32 · lo que el ERP no confirma no entra en la tabla.

    Guardarlo «para no volver a preguntar» convertiría un candidato rechazado en
    una correspondencia confirmada al siguiente arranque.
    """
    usuarios = UsuariosEnMemoria(None)

    with pytest.raises(UsuarioSigridInexistente):
        resolver_login_de_sigrid(
            usuarios,
            ErpEnMemoria(existe_login=False),
            usuario_oid=OID,
            correo=CORREO,
            ahora=AHORA,
        )

    assert usuarios.guardadas == []


def test_f009_r30_sin_correspondencia_y_sin_correo_no_hay_de_donde_derivar():
    """R30 · y entonces se dice así, en vez de firmar con lo que sea."""
    usuarios = UsuariosEnMemoria(None)
    erp = ErpEnMemoria()

    with pytest.raises(UsuarioSigridNoMapeado) as fallo:
        resolver_login_de_sigrid(
            usuarios, erp, usuario_oid=OID, correo="", ahora=AHORA
        )

    assert erp.verificaciones == []
    assert "alta" in fallo.value.motivo.lower()


def test_f009_r45_el_motivo_del_error_no_lleva_el_oid_del_usuario():
    """R43, R45 · el `oid` es dato personal seudónimo y no pinta en un mensaje.

    El correo sí: se lo estamos diciendo a su dueño, que lo tiene delante. El
    `oid` no le dice nada a nadie y sí identifica a la persona en los logs.
    """
    usuarios = UsuariosEnMemoria(None)

    with pytest.raises(UsuarioSigridInexistente) as fallo:
        resolver_login_de_sigrid(
            usuarios,
            ErpEnMemoria(existe_login=False),
            usuario_oid=OID,
            correo=CORREO,
            ahora=AHORA,
        )

    assert OID not in fallo.value.motivo


# --------------------------------------------------------------------------
# El SQL de la tabla, y el adaptador que lo ejecuta
# --------------------------------------------------------------------------


def test_f009_el_select_busca_por_el_oid_y_no_por_el_correo():
    """La clave es el `oid` opaco: el correo no se guarda en ninguna parte."""
    sql, parametros = select_login_sigrid(esquema="postventa", usuario_oid=OID)

    assert "FROM postventa.usuarios_sigrid" in sql
    assert "WHERE usuario_oid = %s" in sql
    assert parametros == (OID,)


def test_f009_r33_el_upsert_deja_una_sola_fila_por_usuario():
    """Dos filas para la misma persona serían dos identidades para firmar."""
    sql, _ = upsert_login_sigrid(
        esquema="postventa",
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=OID, login_sigrid="fulanito", alta_at_utc=AHORA
        ),
    )

    assert "ON CONFLICT (usuario_oid) DO UPDATE SET" in sql


def test_f009_el_upsert_conserva_la_fecha_de_alta_original():
    """Refrescar el alta al reconfirmar borraría desde cuándo existe el mapeo.

    Es la misma regla que `primera_vez_at_utc` en la tabla de partes: se
    conserva lo que cuenta la historia y se refresca lo que cuenta el ahora.
    """
    sql, _ = upsert_login_sigrid(
        esquema="postventa",
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=OID, login_sigrid="fulanito", alta_at_utc=AHORA
        ),
    )

    assert "alta_at_utc = EXCLUDED.alta_at_utc" not in sql
    assert "login_sigrid = EXCLUDED.login_sigrid" in sql
    assert "verificado_at_utc = EXCLUDED.verificado_at_utc" in sql


def test_f009_ningun_valor_va_pegado_al_texto_del_sql():
    """El `oid` y el login son valores, y los valores no se interpolan."""
    sql, parametros = upsert_login_sigrid(
        esquema="postventa",
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=OID, login_sigrid="fulanito", alta_at_utc=AHORA
        ),
    )

    assert OID not in sql
    assert "fulanito" not in sql
    assert sql.count("%s") == len(parametros)


def test_f009_el_repositorio_devuelve_none_cuando_no_hay_correspondencia():
    """No tener mapeo **no es un error**: es la primera vez de esa persona."""
    conexion = ConexionDoble()
    repositorio = RepositorioPostgres(conexion, esquema="postventa")

    assert repositorio.resolver_login(usuario_oid=OID) is None


def test_f009_el_repositorio_devuelve_la_correspondencia_guardada():
    """Y cuando la hay, vuelve al dominio con su marca de verificación."""
    conexion = ConexionDoble().responder(
        "usuarios_sigrid", [(OID, "fulanito", AHORA, AHORA)]
    )
    repositorio = RepositorioPostgres(conexion, esquema="postventa")

    correspondencia = repositorio.resolver_login(usuario_oid=OID)

    assert correspondencia is not None
    assert correspondencia.login_sigrid == "fulanito"
    assert correspondencia.confirmada is True


def test_f009_el_repositorio_guarda_la_correspondencia_y_hace_commit():
    """Sin `commit` la siembra se perdería y cada cierre volvería a derivar."""
    conexion = ConexionDoble().responder("usuarios_sigrid", [(True,)])
    repositorio = RepositorioPostgres(conexion, esquema="postventa")

    resultado = repositorio.guardar_login(
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid="fulanito",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )
    )

    assert resultado == ResultadoGuardado.CREADO
    assert conexion.commits == 1


def test_f009_r45_el_repositorio_no_registra_el_login_en_ningun_log(caplog):
    """R45 · el log del servicio no dice quién cerró qué.

    Lo lee cualquiera que abra Application Insights, y para operar el servicio
    no hace falta. Quien necesita saberlo es el ERP, y ahí sí va (R28).
    """
    conexion = ConexionDoble().responder("usuarios_sigrid", [(True,)])
    repositorio = RepositorioPostgres(conexion, esquema="postventa")

    with caplog.at_level("DEBUG"):
        repositorio.guardar_login(
            correspondencia=CorrespondenciaSigrid(
                usuario_oid=OID, login_sigrid="fulanito", alta_at_utc=AHORA
            )
        )

    assert "fulanito" not in caplog.text


def test_f009_el_mapeo_de_la_fila_respeta_el_orden_de_las_columnas():
    """Cuatro columnas, y el orden es el del `SELECT`.

    Divergir aquí significaría leer el login donde está la fecha.
    """
    correspondencia = fila_a_correspondencia((OID, "fulanito", AHORA, None))

    assert correspondencia.usuario_oid == OID
    assert correspondencia.login_sigrid == "fulanito"
    assert correspondencia.alta_at_utc == AHORA
    assert correspondencia.verificado_at_utc is None
    assert correspondencia.confirmada is False
