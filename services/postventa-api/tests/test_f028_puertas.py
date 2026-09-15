# services/postventa-api/tests/test_f028_puertas.py
"""Las tres puertas del circuito, fijadas **antes** de moverlas (F-028, T1).

Este fichero es el bloque 0 de la feature y su único trabajo es de red de
seguridad. F-028 hace cirugía sobre F-026 —que se cerró el 2026-09-15 y está
verificada contra el ERP de producción, con dos incidencias reales cerradas—:
mueve la decisión humana al modelo de estados, retira el atajo del parte apto
y borra media docena de piezas. Lo que aquí se escribe es **lo que no puede
cambiar** mientras eso ocurre, escrito antes de tocar una sola línea de
producción, para que los bloques 4 y 5 no puedan aflojar una puerta sin que
la suite se entere.

Lo que fija, y son tres prohibiciones que sobreviven enteras al cambio de
modelo:

- **R33 · sin decisión no se pasa.** Un parte no apto del que **no consta
  ninguna decisión humana** no se archiva, no se adjunta y no se cierra. Da
  igual cómo se llame por dentro lo que consulta la puerta —hoy
  `consultar_aprobacion`, mañana `consultar_situacion`—: el resultado
  observable es el mismo y es este.
- **R33 · la decisión no viaja en el cuerpo.** Ni los tres pasos la reciben
  por parámetro, ni los tres handlers la leen del cuerpo de la petición. Si
  viniera de ahí, quien llama podría afirmar que alguien aprobó lo que nadie
  aprobó, y con eso se cierra en el ERP de producción una reclamación que la
  validación había rechazado. Es el argumento que escribió F-012 para
  `traza_grafico` y que F-026 heredó en su R24.
- **R34 · «no hay veredicto» sigue teniendo error propio.** Es un motivo
  distinto de «el veredicto dice que no» y se arregla de otra forma
  —revalidando, no decidiendo—, así que ninguna de las tres puertas puede
  fundirlo con el resto (`design.md` §3, punto 4).

Los partes que se usan son justo los que **sí** pueden acabar decidiéndose a
mano —uno por observaciones manuscritas, otro por firma no humana—: un
control negativo con material que nunca va a ser decidible no vigilaría nada.

Sin red, sin base de datos y sin IA: los tres pasos hablan con puertos y se
ejercitan con los dobles de siempre. Y a los dobles se les pregunta **si
fueron llamados**, que es la única forma de comprobar que no se tocó el ERP.

Ni un dato real: el material sale de `tests/utiles_validacion.py`, inventado
de cabo a rabo.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_grafico import paso_grafico
from domain.models.cierre import CorrespondenciaSigrid
from domain.models.errores import ParteNoApto
from domain.models.grafico import FIRMA_PDF
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import CodigoMotivo, Destino, validar_parte

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sharepoint import ArchivoPortFalso
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

#: El servicio, para leer el código fuente de los handlers.
SERVICIO = Path(__file__).resolve().parent.parent

AHORA = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f028"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
OBRA = "0000"
INCIDENCIA = "XX00.00 - 0000"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"

#: Los dos destinos no aptos: los que una persona puede acabar decidiendo.
DESTINOS_NO_APTOS = (Destino.COLA_VALIDACION_HUMANA, Destino.REVISION_MANUAL)

#: Las palabras que **no** pueden aparecer en la firma de los tres pasos.
#:
#: Cubren el vocabulario de las dos generaciones a propósito: `aprob` es como
#: se llamaba la decisión en F-026 y `decision`, `situacion` y `estado` es como
#: se llama a partir de F-028. Si mañana la decisión entrara por parámetro, se
#: llamaría de alguna de estas formas. `estado` no está de adorno: el estado
#: del parte se **deriva de lo que hay en el almacén** (R16, R33), así que
#: recibirlo de fuera sería exactamente la puerta que esta feature cierra.
PALABRAS_DE_DECISION = ("aprob", "rechaz", "decision", "situacion", "estado")

#: Las palabras que no puede mencionar el **código** de los tres handlers.
#:
#: Es la misma lista menos `estado`, y la resta está razonada: los tres
#: endpoints hablan legítimamente del estado de la traza de archivo y del
#: estado de la reclamación en Sigrid —`estado_archivo` viaja en el cuerpo de
#: `/api/cerrar` desde F-009 y `estado` sale en las respuestas—, así que
#: prohibir la palabra entera sería prohibir lo que ya existe. Lo que se
#: vigila es el vocabulario de la **decisión sobre el parte**, que hoy no
#: aparece en ninguno de los tres y no puede aparecer después.
PALABRAS_DE_DECISION_EN_EL_BORDE = ("aprob", "rechaz", "decision", "situacion")


class UsuariosConLogin:
    """Correspondencia ya confirmada: el camino corto de R29 de F-009."""

    def __init__(self) -> None:
        self.consultas: list[str] = []

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid:
        self.consultas.append(usuario_oid)
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid="logininventado",
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid):
        return ResultadoGuardado.CREADO


class PreferenciasSinAutoCierre:
    """Lo que devuelve quien no ha decidido nada: sin auto-cierre."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def _parte() -> ParteTroceado:
    """El parte troceado de F-002 que comparten todos los casos."""
    return ParteTroceado(
        hash=HASH,
        origen="remesa-de-mentira.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=PDF,
    )


def _material(destino: Destino):
    """La extracción y la firma que producen **de verdad** ese destino.

    - `cola_validacion_humana`: completo y firmado, con observaciones del
      cliente. Es el destino «hay algo que decidir».
    - `revision_manual`: completo y sin observaciones, pero con una marca en
      la casilla de la firma en vez de una firma.
    """
    if destino is Destino.COLA_VALIDACION_HUMANA:
        return (
            extraccion_de_ejemplo(hash_parte=HASH),
            lectura_de_firma("humana", hash_parte=HASH),
        )
    return (
        extraccion_de_ejemplo(hash_parte=HASH, observaciones=None),
        lectura_de_firma("marca_simple", hash_parte=HASH),
    )


def _contexto(destino: Destino) -> ContextoParte:
    """Un parte cuyo veredicto **lo emite F-004 de verdad**, no el test.

    El veredicto sale de `validar_parte` y no de un `ResultadoValidacion`
    montado a mano: si mañana F-004 cambiara sus reglas, este control negativo
    se enteraría en vez de seguir vigilando un destino que ya no existe.

    `archivo` va en `archivado` **a propósito**: así el único motivo posible de
    rechazo es la puerta de aptitud, y el test no puede dar verde por la puerta
    equivocada.
    """
    extraccion, firma = _material(destino)
    validacion = validar_parte(extraccion, firma)
    assert validacion.destino is destino, "el material del test ya no produce ese destino"

    return ContextoParte(
        parte=_parte(),
        extraccion=extraccion,
        lectura_firma=firma,
        validacion=validacion,
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


def _contexto_sin_veredicto() -> ContextoParte:
    """El mismo parte, leído y con su firma, pero **sin validar**.

    No es un caso raro: es lo que hay entre la extracción y la validación, y
    lo que queda si alguien llama al archivado antes de tiempo. Tiene que
    fallar por su motivo, no por el de «la validación dice que no».
    """
    extraccion, firma = _material(Destino.COLA_VALIDACION_HUMANA)
    return ContextoParte(
        parte=_parte(),
        extraccion=extraccion,
        lectura_firma=firma,
        validacion=None,
        archivo=TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO),
    )


# --------------------------------------------------------------------------
# Los tres pasos, llamados igual en todos los casos
# --------------------------------------------------------------------------


def _archivar(ctx: ContextoParte, repositorio, archivador) -> ContextoParte:
    return paso_archivo(
        ctx,
        archivador,
        repositorio,
        carpeta_base="Postventa",
        ahora=AHORA,
    )


def _adjuntar(ctx: ContextoParte, repositorio, erp, graficos) -> ContextoParte:
    return paso_grafico(
        ctx,
        erp,
        graficos,
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=True,
        confirmado=True,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        codigo_obra=OBRA,
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )


def _cerrar(ctx: ContextoParte, repositorio, erp) -> ContextoParte:
    return paso_cierre(
        ctx,
        erp,
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=True,
        confirmado=True,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        ahora=AHORA,
    )


# --------------------------------------------------------------------------
# R33 · los seis casos: dos destinos por tres puertas, sin decisión humana
# --------------------------------------------------------------------------


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f028_r33_un_parte_no_apto_sin_decision_no_se_archiva(destino):
    """R33 · sin decisión humana no se sube nada a SharePoint.

    Y se comprueba contra la biblioteca falsa, no contra un mock: lo que se
    afirma es que **no hay ningún fichero arriba** y que no se creó ni la
    carpeta, no que alguien no llamara a un método.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioEnMemoria()

    with pytest.raises(ParteNoApto) as fallo:
        _archivar(_contexto(destino), repositorio, archivador)

    assert archivador.llamadas == []
    assert archivador.biblioteca.elementos == {}
    assert archivador.biblioteca.carpetas == set()
    assert repositorio.archivos == []
    assert fallo.value.motivo, "el rechazo tiene que decir por qué"


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f028_r33_un_parte_no_apto_sin_decision_no_se_adjunta(destino):
    """R33 · sin decisión humana no entra un documento en el ERP."""
    erp, graficos = ErpEnMemoria(), GraficoEnMemoria()
    repositorio = RepositorioEnMemoria()

    with pytest.raises(ParteNoApto):
        _adjuntar(_contexto(destino), repositorio, erp, graficos)

    assert erp.lecturas == []
    assert graficos.llamadas == []
    assert repositorio.graficos == []


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
def test_f028_r33_un_parte_no_apto_sin_decision_no_cierra_la_incidencia(destino):
    """R33 · sin decisión humana no se cambia el estado de nada en Sigrid.

    Con `commit` y `confirmado`, que es exactamente el caso que hay que
    vigilar: «el usuario pulsó dos veces» no es una decisión sobre el parte.
    """
    erp, repositorio = ErpEnMemoria(), RepositorioEnMemoria()

    with pytest.raises(ParteNoApto):
        _cerrar(_contexto(destino), repositorio, erp)

    assert erp.lecturas == []
    assert erp.cierres == []
    assert repositorio.cierres == []


def test_f028_r33_el_material_del_control_negativo_es_decidible_a_mano():
    """Los dos partes de arriba traen **solo** motivos que una persona resuelve.

    Sin esto, el control negativo podría estar vigilando un parte al que le
    falta el nº de incidencia y seguiría en verde después de los bloques 4 y 5
    sin haber comprobado nada de lo que importa: ese parte no se archiva por
    otro motivo, y el test no distinguiría una puerta cerrada de una puerta
    abierta con el material equivocado delante.
    """
    decidibles = {
        CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
        CodigoMotivo.FIRMA_NO_HUMANA,
    }

    for destino in DESTINOS_NO_APTOS:
        validacion = _contexto(destino).validacion
        codigos = {motivo.codigo for motivo in validacion.motivos}
        assert codigos, destino
        assert codigos <= decidibles, destino


# --------------------------------------------------------------------------
# R34 · «no hay veredicto» sigue siendo un motivo propio
# --------------------------------------------------------------------------


def test_f028_r34_un_parte_sin_veredicto_no_se_archiva_y_lo_dice():
    """R34 · el error nombra el veredicto, porque eso es lo que hay que arreglar.

    Un parte sin validación no se arregla decidiendo sobre él: se arregla
    revalidándolo. Si esta puerta lo fundiera con «el veredicto dice que no»,
    quien lea el error iría a decidir sobre un parte del que nadie ha dicho
    nada.
    """
    archivador, repositorio = ArchivoPortFalso(), RepositorioEnMemoria()

    with pytest.raises(ParteNoApto) as fallo:
        _archivar(_contexto_sin_veredicto(), repositorio, archivador)

    assert "veredicto" in fallo.value.motivo.lower()
    assert archivador.llamadas == []
    assert repositorio.archivos == []


def test_f028_r34_un_parte_sin_veredicto_no_se_adjunta_y_lo_dice():
    """R34 · lo mismo en la puerta del gráfico."""
    erp, graficos = ErpEnMemoria(), GraficoEnMemoria()
    repositorio = RepositorioEnMemoria()

    with pytest.raises(ParteNoApto) as fallo:
        _adjuntar(_contexto_sin_veredicto(), repositorio, erp, graficos)

    assert "veredicto" in fallo.value.motivo.lower()
    assert erp.lecturas == []
    assert graficos.llamadas == []


def test_f028_r34_un_parte_sin_veredicto_no_cierra_y_lo_dice():
    """R34 · y en la del cierre, que es la que escribe en producción."""
    erp, repositorio = ErpEnMemoria(), RepositorioEnMemoria()

    with pytest.raises(ParteNoApto) as fallo:
        _cerrar(_contexto_sin_veredicto(), repositorio, erp)

    assert "veredicto" in fallo.value.motivo.lower()
    assert erp.lecturas == []
    assert erp.cierres == []


# --------------------------------------------------------------------------
# R33 · la decisión no entra por el cuerpo de la petición
# --------------------------------------------------------------------------


@pytest.mark.parametrize("paso", [paso_archivo, paso_grafico, paso_cierre])
def test_f028_r33_ningun_paso_recibe_la_decision_por_parametro(paso):
    """R33 · la decisión y el estado se leen del almacén, nunca de fuera.

    Se mira la **firma** del paso, que es el contrato con el borde: si algún
    día apareciera ahí un `estado=` o un `decision=`, quien llama podría
    afirmar que alguien aprobó lo que nadie aprobó. Lo que sí puede aparecer
    es un campo en `ContextoParte`, que rellena el propio paso leyendo la
    base — el precedente exacto es `traza_grafico` (F-012, R49).
    """
    parametros = inspect.signature(paso).parameters

    sospechosos = [
        nombre
        for nombre in parametros
        if any(palabra in nombre.lower() for palabra in PALABRAS_DE_DECISION)
    ]

    assert sospechosos == []


def _vocabulario_del_codigo(fuente: str) -> set[str]:
    """Los nombres y los literales que usa el **código**, sin las docstrings.

    Se mira el árbol y no el texto plano a propósito: los tres handlers
    explican en prosa lo que hacen, y un control sobre el texto crudo se
    pondría rojo porque `cerrar.py` dice «rechaza y punto» en una docstring.
    Lo que hay que vigilar no es lo que el módulo **cuenta**, es lo que
    **hace**: los identificadores que nombra y las claves que lee y escribe.

    Es el mismo tipo de control que usa F-005 sobre el texto del DDL —lo que
    no se puede mutar hay que mirarlo—, con el árbol en vez de la cadena.
    """
    arbol = ast.parse(fuente)

    docstrings = set()
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            primera = nodo.body[0] if nodo.body else None
            if (
                isinstance(primera, ast.Expr)
                and isinstance(primera.value, ast.Constant)
                and isinstance(primera.value.value, str)
            ):
                docstrings.add(id(primera.value))

    vocabulario: set[str] = set()
    for nodo in ast.walk(arbol):
        match nodo:
            case ast.Name():
                vocabulario.add(nodo.id)
            case ast.Attribute():
                vocabulario.add(nodo.attr)
            case ast.arg():
                vocabulario.add(nodo.arg)
            case ast.keyword() if nodo.arg is not None:
                vocabulario.add(nodo.arg)
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                vocabulario.add(nodo.name)
            case ast.alias():
                vocabulario.add(nodo.name)
            case ast.Constant() if isinstance(nodo.value, str) and id(nodo) not in docstrings:
                vocabulario.add(nodo.value)
    return {palabra.lower() for palabra in vocabulario}


@pytest.mark.parametrize("handler", ["archivar.py", "adjuntar.py", "cerrar.py"])
def test_f028_r33_ningun_handler_lee_la_decision_del_cuerpo(handler):
    """R33 · el contrato de los tres endpoints **no gana ni una clave**.

    Los tres handlers leen su cuerpo de formas distintas —`archivar.py` por
    parámetros con nombre, `cerrar.py` por claves de un diccionario—, así que
    lo que se mira es el vocabulario entero de su código: si alguien sacara la
    decisión del cuerpo de la petición, la palabra estaría en un nombre de
    parámetro o en una clave, y las dos cosas caen aquí.
    """
    fuente = (SERVICIO / "interface_adapters" / "api" / handler).read_text(
        encoding="utf-8"
    )

    vocabulario = _vocabulario_del_codigo(fuente)
    sospechosas = sorted(
        palabra
        for palabra in vocabulario
        if any(prohibida in palabra for prohibida in PALABRAS_DE_DECISION_EN_EL_BORDE)
    )

    assert sospechosas == []


# --------------------------------------------------------------------------
# T10 · el hueco del contexto es la **situación**, y dice de dónde viene
# --------------------------------------------------------------------------


def test_f028_r33_el_contexto_lleva_la_situacion_y_no_la_aprobacion():
    """R33 · lo que los tres pasos dejan en el contexto es la **situación**.

    F-026 dejaba ahí `aprobacion`; F-028 la sustituye, y no es un cambio de
    nombre: lo que las puertas consultan a partir de ahora es la situación
    entera —última decisión humana, último estado registrado y traza de
    cierre—, que es lo único con lo que se puede derivar el estado (R2, R16).

    Que queden las dos sería tener el mismo hecho en dos huecos del mismo
    objeto, y el día que uno de los dos se quedara viejo nadie se enteraría.
    """
    campos = {campo.name: campo.type for campo in fields(ContextoParte)}

    assert "situacion" in campos
    assert "aprobacion" not in campos
    assert "SituacionParte" in str(campos["situacion"])


def test_f028_r33_el_contexto_dice_que_la_situacion_no_viene_del_cuerpo():
    """R33 · la docstring lo dice, y decirlo es parte de la tarea.

    Es el tercer caso de lo mismo que `traza_grafico` (F-012 R49) y que la
    `aprobacion` de F-026 (su R24), y la advertencia escrita es lo que ha
    impedido las dos veces anteriores que alguien «simplificara» el paso
    aceptando el dato por parámetro. Sin ella, quien llama podría afirmar que
    alguien aprobó lo que nadie aprobó, y con eso se cierra en el ERP de
    producción una reclamación que la validación había rechazado.
    """
    documentacion = (ContextoParte.__doc__ or "").lower()

    assert "situacion" in documentacion or "situación" in documentacion
    assert "nunca del cuerpo" in documentacion
