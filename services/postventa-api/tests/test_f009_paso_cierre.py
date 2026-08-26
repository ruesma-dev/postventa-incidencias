# services/postventa-api/tests/test_f009_paso_cierre.py
"""El paso que decide si se cierra, con dobles en memoria (F-009).

Aquí no hay red, no hay base de datos y **no hay ERP**: el paso habla con
puertos, así que se ejercita entero sin que Sigrid se entere de que existimos.
Eso es lo que permite exigirle cobertura y mutación a la pieza que decide si se
escribe en el ERP de producción.

Lo que fija:

- **R8, R10** · el dry-run va **primero**, y sin él no se escribe.
- **R16, R17** · las dos precondiciones **propias**: parte apto y archivado.
- **R20** · y ninguna otra: el gráfico **no se consulta**.
- **R12, R13, R14** · la confirmación, el auto-cierre y su valor por omisión.
- **R18** · ya cerrada no es un error.
- **R19** · un estado que no admite cierre aborta nombrando el estado.
- **R40, R41, R42** · la traza local, y que `cerrado` es terminal.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import paso_cierre
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import (
    CierreFallido,
    CuerpoDeCierreInvalido,
    EstadoNoCerrable,
    ParteNoApto,
    ParteNoArchivado,
    ReclamacionNoLocalizada,
    UsuarioSigridInexistente,
)
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoCierre,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion, Veredicto

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria

AHORA = datetime(2026, 8, 26, 9, 46, 33, tzinfo=UTC)
HASH = "hash-inventado-del-parte"
OID = "oid-inventado-para-el-test"
CORREO = "fulanito@ejemplo.invalido"
INCIDENCIA = "RS26.08 - 0123"


class UsuariosEnMemoria:
    """Un `RepositorioUsuariosSigridPort` de mentira, ya confirmado."""

    def __init__(self, login: str = "fulanito") -> None:
        self.correspondencia = CorrespondenciaSigrid(
            usuario_oid=OID,
            login_sigrid=login,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )
        self.guardadas: list[CorrespondenciaSigrid] = []

    def resolver_login(self, *, usuario_oid: str):
        return self.correspondencia

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        self.guardadas.append(correspondencia)
        return ResultadoGuardado.CREADO


class PreferenciasEnMemoria:
    """Un `RepositorioPreferenciasPort` de mentira.

    Por omisión devuelve **la de quien no ha decidido nada**: sin auto-cierre.
    Es el valor que hay que poder comprobar (R14).
    """

    def __init__(self, auto_cierre: bool = False) -> None:
        self.auto_cierre = auto_cierre
        self.consultas: list[str] = []

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        self.consultas.append(usuario_oid)
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=self.auto_cierre,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias: PreferenciasUsuario):
        return ResultadoGuardado.CREADO


def _reclamacion(*, est: int = 3, cod_origen: str = "PTE") -> Reclamacion:
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=est,
        codigo="RS26.08/0123",
        descripcion="REPARACION",
        estado_origen_cod=cod_origen,
        estado_origen_res=f"ESTADO {cod_origen}",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _contexto(
    *,
    veredicto: Veredicto = Veredicto.APTO,
    destino: Destino = Destino.ARCHIVO_Y_CIERRE,
    archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO,
    con_validacion: bool = True,
) -> ContextoParte:
    """El contexto de un parte que ya pasó validación y archivo."""
    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"",
        ),
        validacion=(
            ResultadoValidacion(
                hash_parte=HASH,
                veredicto=veredicto,
                destino=destino,
                motivos=(),
                clasificacion_firma=ClasificacionFirma.HUMANA,
                observaciones=None,
                confianza_observaciones=0,
            )
            if con_validacion
            else None
        ),
        archivo=(
            TrazaArchivo(hash_parte=HASH, estado=archivo)
            if archivo is not None
            else None
        ),
    )


def _cerrar(
    ctx: ContextoParte | None = None,
    *,
    erp: ErpEnMemoria | None = None,
    repositorio: RepositorioEnMemoria | None = None,
    usuarios: UsuariosEnMemoria | None = None,
    preferencias: PreferenciasEnMemoria | None = None,
    commit: bool = False,
    confirmado: bool = False,
) -> ContextoParte:
    """Ejecuta el paso con dobles, dejando afinar solo lo que el test mire."""
    return paso_cierre(
        ctx if ctx is not None else _contexto(),
        erp if erp is not None else ErpEnMemoria(_reclamacion()),
        repositorio if repositorio is not None else RepositorioEnMemoria(),
        usuarios if usuarios is not None else UsuariosEnMemoria(),
        preferencias if preferencias is not None else PreferenciasEnMemoria(),
        commit=commit,
        confirmado=confirmado,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R16, R17 · las dos precondiciones propias, antes de tocar el ERP
# --------------------------------------------------------------------------


def test_f009_r16_un_parte_sin_veredicto_no_cierra_nada():
    """R16 · nadie ha mirado ese parte, así que no se da nada por resuelto."""
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoApto):
        _cerrar(_contexto(con_validacion=False), erp=erp)

    assert erp.lecturas == []


def test_f009_r16_un_parte_no_apto_no_cierra_nada():
    """R16 · el veredicto dice que no, y eso manda sobre cualquier otra cosa."""
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoApto) as fallo:
        _cerrar(
            _contexto(
                veredicto=Veredicto.NO_APTO,
                destino=Destino.COLA_VALIDACION_HUMANA,
            ),
            erp=erp,
        )

    assert erp.lecturas == []
    assert "cola" in fallo.value.motivo.lower()


def test_f009_r17_un_parte_que_no_consta_archivado_no_cierra_nada():
    """R17 · **el orden del procedimiento de Posventa**: primero el documento.

    Si el PDF no está guardado en ninguna parte, cerrar la incidencia la da por
    resuelta sin dejar la prueba en ningún sitio. Y es lo que sostiene el
    riesgo aceptado de `design.md` §2: solo es asumible porque el parte existe.
    """
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(ParteNoArchivado):
        _cerrar(_contexto(archivo=None), erp=erp)

    assert erp.lecturas == []


@pytest.mark.parametrize(
    "estado", [EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR]
)
def test_f009_r17_un_archivo_a_medias_tampoco_vale(estado):
    """R17 · `pendiente` y `error` **no** son «archivado».

    Son exactamente los dos estados en los que el fichero puede no estar
    arriba, que es cuando más importa no cerrar.
    """
    with pytest.raises(ParteNoArchivado):
        _cerrar(_contexto(archivo=estado))


def test_f009_r17_las_precondiciones_van_en_orden_apto_y_luego_archivado():
    """El orden importa para el mensaje: revalidar y archivar no son lo mismo.

    Un parte que no es apto **y** no está archivado tiene que decir que no es
    apto: archivarlo no arreglaría nada.
    """
    with pytest.raises(ParteNoApto):
        _cerrar(_contexto(veredicto=Veredicto.NO_APTO, archivo=None))


# --------------------------------------------------------------------------
# R8, R10 · el dry-run va primero, y sin él no se escribe
# --------------------------------------------------------------------------


def test_f009_r8_el_dry_run_lee_y_no_escribe_nada():
    """R8 · con `commit` en falso se lee la reclamación y ahí acaba."""
    erp = ErpEnMemoria(_reclamacion())

    ctx = _cerrar(erp=erp, commit=False)

    assert erp.lecturas == ["RS26.08/0123"]
    assert erp.cierres == []
    assert ctx.cierre.estado == EstadoCierre.DRY_RUN_OK


def test_f009_r6_el_codigo_del_parte_se_convierte_al_formato_de_sigrid():
    """R6 · en el fichero va con guion; al ERP se le pregunta con barra."""
    erp = ErpEnMemoria(_reclamacion())

    _cerrar(erp=erp)

    assert erp.lecturas == ["RS26.08/0123"]


def test_f009_r10_el_commit_va_siempre_despues_de_la_lectura():
    """R10 · nunca se escribe sin haber leído antes en esa misma ejecución.

    El plan que recibe `cerrar` **solo** lo puede producir el dry-run: no hay
    forma de pedir un cierre a secas.
    """
    erp = ErpEnMemoria(_reclamacion())

    _cerrar(erp=erp, commit=True, confirmado=True)

    assert erp.lecturas == ["RS26.08/0123"]
    assert len(erp.cierres) == 1


def test_f009_r7_una_incidencia_que_no_esta_en_el_erp_no_cierra_nada():
    """R7 · el código no existe: se dice, y no se escribe."""
    erp = ErpEnMemoria(None)

    with pytest.raises(ReclamacionNoLocalizada) as fallo:
        _cerrar(erp=erp, commit=True, confirmado=True)

    assert erp.cierres == []
    assert "RS26.08/0123" in fallo.value.motivo


def test_f009_r47_sin_numero_de_incidencia_no_se_pregunta_al_erp():
    """Sin código no hay a quién preguntar, y preguntar por «» sería absurdo."""
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(CuerpoDeCierreInvalido):
        paso_cierre(
            _contexto(),
            erp,
            RepositorioEnMemoria(),
            UsuariosEnMemoria(),
            PreferenciasEnMemoria(),
            commit=False,
            confirmado=False,
            usuario_oid=OID,
            correo=CORREO,
            numero_incidencia="   ",
            ahora=AHORA,
        )

    assert erp.lecturas == []


# --------------------------------------------------------------------------
# R20 · la precondición es PROPIA, y ninguna otra
# --------------------------------------------------------------------------


def test_f009_r20_el_paso_no_consulta_nada_de_graficos():
    """R20 · el puerto del ERP **no tiene** ninguna operación de gráficos.

    Es el control negativo más barato posible: no se puede consultar lo que no
    existe. Tras la decisión del humano del 2026-08-26 el orden es validar →
    cerrar → subir el PDF, y F-012 se ocupa de lo último.
    """
    from domain.ports.erp import ErpPort

    operaciones = [
        nombre for nombre in dir(ErpPort) if not nombre.startswith("_")
    ]

    assert sorted(operaciones) == ["cerrar", "existe_usuario", "leer_reclamacion"]


def test_f009_r20_el_modulo_del_paso_no_menciona_las_tablas_de_graficos():
    """R20 · ni de pasada, y menos como precondición."""
    import re
    from pathlib import Path

    modulo = (
        Path(__file__).resolve().parent.parent
        / "application"
        / "pipelines"
        / "paso_cierre.py"
    )

    assert re.findall(r"\b(rcg|gra)\b", modulo.read_text(encoding="utf-8")) == []


# --------------------------------------------------------------------------
# R18, R19 · lo que dice el dominio, aplicado
# --------------------------------------------------------------------------


def test_f009_r18_una_reclamacion_ya_cerrada_no_es_un_error():
    """R18 · se registra `ya_cerrada` y **no se escribe nada en Sigrid**."""
    erp = ErpEnMemoria(_reclamacion(est=90, cod_origen="CER"))
    repositorio = RepositorioEnMemoria()

    ctx = _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=True)

    assert erp.cierres == []
    assert ctx.cierre.estado == EstadoCierre.YA_CERRADA
    assert repositorio.cierres[-1].estado == EstadoCierre.YA_CERRADA


def test_f009_r19_un_estado_que_no_admite_cierre_aborta_nombrandolo():
    """R19 · `NPR` (NO PROCEDE) es el caso que más importa.

    Alguien decidió que esa reclamación no procede, y cerrarla la daría por
    resuelta.
    """
    erp = ErpEnMemoria(_reclamacion(est=7, cod_origen="NPR"))

    with pytest.raises(EstadoNoCerrable) as fallo:
        _cerrar(erp=erp, commit=True, confirmado=True)

    assert erp.cierres == []
    assert "NPR" in fallo.value.motivo


def test_f009_r19_un_estado_no_cerrable_tambien_corta_el_dry_run():
    """R19 · no se enseña un dry-run de algo que no se va a poder cerrar."""
    erp = ErpEnMemoria(_reclamacion(est=7, cod_origen="NPR"))

    with pytest.raises(EstadoNoCerrable):
        _cerrar(erp=erp, commit=False)


# --------------------------------------------------------------------------
# R12, R13, R14 · la confirmación y el auto-cierre
# --------------------------------------------------------------------------


def test_f009_r12_sin_confirmacion_y_sin_auto_cierre_no_se_escribe():
    """R12 · **el requisito que impide cerrar por un error de flujo.**

    Quien pide `commit` sin haber confirmado no obtiene un cierre: obtiene un
    400 que dice qué le falta.
    """
    erp = ErpEnMemoria(_reclamacion())

    with pytest.raises(CuerpoDeCierreInvalido) as fallo:
        _cerrar(erp=erp, commit=True, confirmado=False)

    assert erp.cierres == []
    assert "confirmado" in fallo.value.motivo


def test_f009_r12_con_confirmacion_explicita_si_se_escribe():
    """R12 · el camino normal: el usuario confirma en el front."""
    erp = ErpEnMemoria(_reclamacion())

    ctx = _cerrar(erp=erp, commit=True, confirmado=True)

    assert len(erp.cierres) == 1
    assert ctx.cierre.estado == EstadoCierre.CERRADO


def test_f009_r13_el_auto_cierre_encadena_sin_pedir_confirmacion():
    """R13 · quien lo tiene activo no confirma cada vez."""
    erp = ErpEnMemoria(_reclamacion())

    ctx = _cerrar(
        erp=erp,
        preferencias=PreferenciasEnMemoria(auto_cierre=True),
        commit=True,
        confirmado=False,
    )

    assert len(erp.cierres) == 1
    assert ctx.cierre.estado == EstadoCierre.CERRADO


def test_f009_r13_el_auto_cierre_no_se_salta_el_dry_run():
    """R13 · **ni el dry-run ni ninguna validación.**

    El auto-cierre ahorra un clic, no una comprobación. Si se saltara el
    dry-run, se escribiría en el ERP sin haber leído el estado de origen y el
    control optimista de R11 no tendría contra qué comparar.
    """
    erp = ErpEnMemoria(_reclamacion())

    _cerrar(
        erp=erp,
        preferencias=PreferenciasEnMemoria(auto_cierre=True),
        commit=True,
        confirmado=False,
    )

    assert erp.lecturas == ["RS26.08/0123"]


def test_f009_r13_el_auto_cierre_tampoco_se_salta_las_precondiciones():
    """R13 · un parte no archivado no se cierra ni con auto-cierre activo."""
    with pytest.raises(ParteNoArchivado):
        _cerrar(
            _contexto(archivo=None),
            preferencias=PreferenciasEnMemoria(auto_cierre=True),
            commit=True,
            confirmado=False,
        )


def test_f009_r14_quien_no_ha_decidido_nada_no_tiene_auto_cierre():
    """R14 · el valor por omisión es **falso**, y por eso no cierra solo.

    Es el comportamiento que se hereda sin hacer nada, y detrás hay el ERP de
    producción.
    """
    preferencias = PreferenciasEnMemoria()

    with pytest.raises(CuerpoDeCierreInvalido):
        _cerrar(preferencias=preferencias, commit=True, confirmado=False)

    assert preferencias.consultas == [OID]


def test_f009_r12_el_dry_run_no_necesita_confirmacion():
    """R12 · lo que se prohíbe sin confirmar es **escribir**, no mirar."""
    ctx = _cerrar(commit=False, confirmado=False)

    assert ctx.cierre.estado == EstadoCierre.DRY_RUN_OK


# --------------------------------------------------------------------------
# El login, resuelto antes de tocar nada
# --------------------------------------------------------------------------


def test_f009_r32_sin_login_confirmado_no_se_escribe_en_el_erp():
    """R32 · y se descubre **antes** del cierre, no a mitad.

    El login se resuelve al principio: si el ERP no lo confirma, no se ha
    llegado a componer ninguna escritura.
    """

    class SinCorrespondencia:
        def resolver_login(self, *, usuario_oid: str):
            return None

        def guardar_login(self, *, correspondencia):  # pragma: no cover
            raise AssertionError("no se guarda un login sin verificar")

    erp = ErpEnMemoria(_reclamacion(), existe_login=False)

    with pytest.raises(UsuarioSigridInexistente):
        paso_cierre(
            _contexto(),
            erp,
            RepositorioEnMemoria(),
            SinCorrespondencia(),
            PreferenciasEnMemoria(),
            commit=True,
            confirmado=True,
            usuario_oid=OID,
            correo=CORREO,
            numero_incidencia=INCIDENCIA,
            ahora=AHORA,
        )

    assert erp.cierres == []


def test_f009_r28_el_plan_lleva_el_login_con_el_que_se_firma():
    """R28 · el que se resolvió para esa persona, nunca una constante."""
    erp = ErpEnMemoria(_reclamacion())

    ctx = _cerrar(erp=erp, usuarios=UsuariosEnMemoria(login="menganita"))

    assert ctx.cierre.plan.login_sigrid == "menganita"


# --------------------------------------------------------------------------
# R40, R41, R42 · la traza local
# --------------------------------------------------------------------------


def test_f009_r40_un_dry_run_correcto_deja_su_traza():
    """R40 · con estado `dry_run_ok` y su marca de tiempo."""
    repositorio = RepositorioEnMemoria()

    _cerrar(repositorio=repositorio, commit=False)

    traza = repositorio.cierres[-1]
    assert traza.estado == EstadoCierre.DRY_RUN_OK
    assert traza.dry_run_at_utc == AHORA
    assert traza.hash_parte == HASH


def test_f009_r41_un_cierre_con_exito_deja_su_traza_completa():
    """R41 · el `oid` de quien confirmó, los dos códigos de estado y la hora."""
    repositorio = RepositorioEnMemoria()

    _cerrar(repositorio=repositorio, commit=True, confirmado=True)

    traza = repositorio.cierres[-1]
    assert traza.estado == EstadoCierre.CERRADO
    assert traza.confirmado_por == OID
    assert traza.estado_origen_sigrid == "PTE"
    assert traza.estado_destino_sigrid == "CER"
    assert traza.cerrado_at_utc == AHORA


def test_f009_r43_la_traza_del_cierre_guarda_el_oid_y_nunca_el_login():
    """R43 · **tres sitios distintos, tres datos distintos.**

    En el log del ERP va el login, porque es el ERP quien necesita saber quién
    ejecutó el proceso. En la traza del cierre va solo el `oid`, porque para
    reconstruir qué hicimos no hace falta saber quién es. Y el par vive en la
    tabla de correspondencias, que es su razón de existir.
    """
    repositorio = RepositorioEnMemoria()

    _cerrar(
        repositorio=repositorio,
        usuarios=UsuariosEnMemoria(login="menganita"),
        commit=True,
        confirmado=True,
    )

    traza = repositorio.cierres[-1]
    campos = [str(valor) for valor in vars(traza).values()]
    assert "menganita" not in campos
    assert CORREO not in campos
    assert traza.confirmado_por == OID


def test_f009_r42_una_traza_ya_cerrada_no_se_pisa():
    """R42 · `cerrado` es **terminal**, y quien lo garantiza es la base.

    El repositorio devuelve `SIN_CAMBIOS` cuando la fila ya estaba en
    `cerrado`, y el paso lo trata como lo que es: no había nada que hacer, que
    no es lo mismo que no haber podido.
    """
    repositorio = RepositorioEnMemoria(ResultadoGuardado.SIN_CAMBIOS)

    ctx = _cerrar(repositorio=repositorio, commit=True, confirmado=True)

    assert ctx.cierre.estado == EstadoCierre.CERRADO


def test_f009_r42_el_sql_de_la_traza_sigue_protegiendo_el_estado_terminal():
    """R42 · y se comprueba en el SQL, que es donde vive la garantía.

    Sin el `WHERE` del `DO UPDATE`, volver a ejecutar el cierre reescribiría la
    traza de una escritura real en el ERP de producción.
    """
    from domain.models.persistencia import TrazaCierre
    from infrastructure.persistencia.sentencias import upsert_cierre

    sql, parametros = upsert_cierre(
        esquema="postventa",
        traza=TrazaCierre(
            hash_parte=HASH,
            numero_incidencia="RS26.08/0123",
            estado=EstadoCierre.CERRADO,
        ),
    )

    assert "WHERE postventa.cierres.estado <> %s" in sql
    assert EstadoCierre.CERRADO.value in parametros


def test_f009_r27_un_cierre_fallido_deja_traza_de_error_y_no_se_reintenta():
    """R27 · se registra el motivo y **no se vuelve a intentar solo**."""
    erp = ErpEnMemoria(
        _reclamacion(), fallo_al_cerrar=CierreFallido("la pasarela respondió 500")
    )
    repositorio = RepositorioEnMemoria()

    with pytest.raises(CierreFallido):
        _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=True)

    assert len(erp.cierres) == 1
    traza = repositorio.cierres[-1]
    assert traza.estado == EstadoCierre.ERROR
    assert "500" in traza.motivo


def test_f009_r22_un_cierre_que_no_afecta_a_dos_filas_no_se_da_por_bueno():
    """R22 · el paso comprueba el recuento aunque el adaptador ya lo haga.

    Es una red de seguridad: un doble del ERP, o un adaptador futuro, podrían
    devolver otra cosa, y dar por cerrado lo que no lo está es el fallo más
    caro de esta feature.
    """
    erp = ErpEnMemoria(_reclamacion(), filas_afectadas=1)
    repositorio = RepositorioEnMemoria()

    with pytest.raises(CierreFallido):
        _cerrar(erp=erp, repositorio=repositorio, commit=True, confirmado=True)

    assert repositorio.cierres[-1].estado == EstadoCierre.ERROR


def test_f009_r41_la_traza_guarda_el_codigo_de_la_incidencia_en_formato_sigrid():
    """La traza local y el ERP tienen que hablar del mismo código.

    Guardar el del nombre del fichero obligaría a convertir cada vez que
    alguien quisiera cruzar las dos cosas.
    """
    repositorio = RepositorioEnMemoria()

    _cerrar(repositorio=repositorio, commit=True, confirmado=True)

    assert repositorio.cierres[-1].numero_incidencia == "RS26.08/0123"
