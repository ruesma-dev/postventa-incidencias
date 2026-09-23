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
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from pathlib import Path

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_grafico import paso_grafico
from domain.models.aprobacion import huella_de_veredicto
from domain.models.cierre import (
    CorrespondenciaSigrid,
    Reclamacion,
    a_codigo_de_sigrid,
)
from domain.models.errores import ParteNoApto
from domain.models.estado import (
    ESTADOS_DE_CIERRE_EN_FIRME,
    DecisionEstado,
    EstadoParte,
    SituacionParte,
)
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

from tests.utiles_ia import CAMPOS_DE_EJEMPLO
from tests.utiles_pg import (
    RepositorioEnMemoria,
    con_el_archivo_guardado,
    con_el_veredicto_guardado,
)
from tests.utiles_sharepoint import ArchivoPortFalso, contexto_apto
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
#
# **Enmienda del 2026-09-16 (F-030 T9).** Desde F-030 la puerta deriva el
# estado del veredicto **guardado** —`ctx.situacion.validacion`— y ya no mira
# el del contexto. Los casos de este fichero preparaban el veredicto solo en el
# contexto, porque hasta ayer era de ahí de donde salía, así que los tres
# ayudantes lo dejan ahora también en el doble antes de llamar al paso.
#
# Es un cambio en los **tres ayudantes** y en ninguno de los 48 casos: ni un
# aserto cambia, ni se afloja ninguna puerta. `con_el_veredicto_guardado` no
# inventa veredictos —si el contexto no trae ninguno, el doble se queda sin él,
# que es lo que exige el caso de `_contexto_sin_veredicto()`— y no pisa la
# situación que un caso haya preparado a propósito. Su porqué entero está en
# `tests/utiles_pg.py`.


def _archivar(ctx: ContextoParte, repositorio, archivador) -> ContextoParte:
    con_el_veredicto_guardado(repositorio, ctx)
    return paso_archivo(
        ctx,
        archivador,
        repositorio,
        carpeta_base="Postventa",
        ahora=AHORA,
    )


def _adjuntar(
    ctx: ContextoParte, repositorio, erp, graficos, *, commit: bool = True
) -> ContextoParte:
    """El gráfico, con el veredicto **y** la traza de archivo en el doble.

    **Enmienda del 2026-09-23 (F-034).** Desde F-034 el gráfico lee también la
    traza de archivo de lo guardado, así que se deja en el doble igual que el
    veredicto (`con_el_archivo_guardado`, mismas dos reglas). Y ya no recibe
    los códigos sueltos: los que decide son los **guardados**, y estos casos
    no hablan de cuerpos, así que no declaran ninguno (`codigos_declarados`
    queda en `None`, que es para lo que es opcional, `design.md` §4.2). El
    cotejo de lo declarado se prueba en `test_f034_codigos_en_el_erp.py`.
    """
    con_el_veredicto_guardado(repositorio, ctx)
    con_el_archivo_guardado(repositorio, ctx)
    return paso_grafico(
        ctx,
        erp,
        graficos,
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=commit,
        confirmado=True,
        usuario_oid=OID,
        correo=CORREO,
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )


def _cerrar(
    ctx: ContextoParte, repositorio, erp, *, commit: bool = True
) -> ContextoParte:
    con_el_veredicto_guardado(repositorio, ctx)
    return paso_cierre(
        ctx,
        erp,
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=commit,
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


# --------------------------------------------------------------------------
# T11 · los cuatro estados contra las tres puertas
# --------------------------------------------------------------------------
#
# Lo de arriba es el bloque 0: lo que **no puede cambiar**. Lo de aquí abajo es
# lo que T11 hace posible, y es medio encargo de la feature: que una persona
# pueda **rechazar un parte verde** y que ese rechazo se note en las tres
# puertas. Hasta T11 era imposible —`_exigir_admitido` devolvía «pasa» en
# cuanto el veredicto era apto, sin consultar nada (`design.md` §0.5 y §6)— y
# el botón de rechazar habría sido un botón que no hace nada.
#
# El criterio de las tres puertas pasa a ser uno y es el del dominio:
# `estado_del_parte(...) is EstadoParte.APROBADO`. De los cuatro estados, pasa
# **uno**.

#: El código de la incidencia tal y como lo espera Sigrid.
CODIGO_EN_SIGRID = "XX00.00/0000"

#: F-034 · el código con el que el **gráfico** busca la reclamación: el nº de
#: incidencia **guardado** del parte, que es el que F-004 leyó del material de
#: ejemplo (`CAMPOS_DE_EJEMPLO`), en el formato de Sigrid. Hasta F-034 salía
#: del cuerpo (`INCIDENCIA`, de ahí `CODIGO_EN_SIGRID`).
CODIGO_GUARDADO_EN_SIGRID = a_codigo_de_sigrid(CAMPOS_DE_EJEMPLO["numero_incidencia"][0])


def _reclamacion() -> Reclamacion:
    """Una reclamación abierta e inventada, en el tipo de posventa."""
    return Reclamacion(
        ide=111_222,
        emp=1,
        tip=708,
        est=3,
        codigo=CODIGO_EN_SIGRID,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


@dataclass
class Dobles:
    """Los tres sitios por los que un parte puede salir de aquí.

    Van juntos a propósito: lo que se afirma después de cada puerta cerrada no
    es «no se llamó a este método» sino **que no salió nada a ninguna parte**,
    y eso hay que mirarlo en los tres a la vez. Una puerta que se aflojara y
    dejara subir el PDF a SharePoint sin cerrar la incidencia dejaría el parte
    a medio camino, que es peor que no haber empezado.
    """

    archivador: ArchivoPortFalso
    erp: ErpEnMemoria
    graficos: GraficoEnMemoria


def _dobles() -> Dobles:
    return Dobles(ArchivoPortFalso(), ErpEnMemoria(_reclamacion()), GraficoEnMemoria())


def _nada_ha_salido(dobles: Dobles) -> None:
    """Ni un byte a SharePoint, ni una lectura del ERP, ni un cierre."""
    assert dobles.archivador.llamadas == []
    assert dobles.archivador.biblioteca.elementos == {}
    assert dobles.archivador.biblioteca.carpetas == set()
    assert dobles.erp.lecturas == []
    assert dobles.erp.cierres == []
    assert dobles.graficos.llamadas == []


def _puerta_de_archivo(ctx, repositorio, dobles, *, commit=True):
    return _archivar(ctx, repositorio, dobles.archivador)


def _puerta_del_grafico(ctx, repositorio, dobles, *, commit=True):
    return _adjuntar(ctx, repositorio, dobles.erp, dobles.graficos, commit=commit)


def _puerta_del_cierre(ctx, repositorio, dobles, *, commit=True):
    return _cerrar(ctx, repositorio, dobles.erp, commit=commit)


#: Las tres puertas del circuito, llamadas con la misma forma.
#:
#: Van parametrizadas y no escritas tres veces porque el requisito es de las
#: tres a la vez (R33): abrir una sola ya deja el parte a medio camino.
PUERTAS = (
    pytest.param(_puerta_de_archivo, id="archivo"),
    pytest.param(_puerta_del_grafico, id="grafico"),
    pytest.param(_puerta_del_cierre, id="cierre"),
)


def _contexto_apto() -> ContextoParte:
    """El parte **verde**: firmado, completo y sin observaciones.

    Es el que hasta T11 no consultaba nada, y por eso es el material del caso
    que la feature viene a arreglar: un parte que la máquina declaró apto y
    que una persona rechaza.
    """
    ctx = contexto_apto(hash_parte=HASH, contenido=PDF)
    assert ctx.validacion.destino is Destino.ARCHIVO_Y_CIERRE
    return ctx


def _contexto_para(puerta, *, apto: bool = True) -> ContextoParte:
    """El contexto que esa puerta necesita para que el ÚNICO motivo sea el estado.

    La puerta del archivo exige que el parte **no** conste archivado —si
    constara, la idempotencia de F-006 cortaría antes de subir nada y el caso
    daría verde sin haber probado la puerta—; las del gráfico y el cierre
    exigen justo lo contrario (F-006 R15, F-009 R17). Así, si mañana alguien
    retirase la puerta de aptitud, estos casos fallarían **por lo que hay que
    fallar** y no por la puerta de al lado.
    """
    ctx = _contexto_apto() if apto else _contexto(Destino.COLA_VALIDACION_HUMANA)
    ctx.archivo = (
        None
        if puerta is _puerta_de_archivo
        else TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO)
    )
    return ctx


def _ha_pasado(puerta, dobles: Dobles) -> None:
    """La prueba de que la puerta se abrió, mirada desde fuera.

    Cada puerta deja su huella en un sitio distinto: el archivo, en la
    biblioteca; el gráfico y el cierre, en la lectura de la reclamación que
    hacen nada más pasar. Se mira el efecto y no el retorno del paso a
    propósito: lo que importa es que el parte **siguió su camino**.
    """
    if puerta is _puerta_de_archivo:
        assert dobles.archivador.biblioteca.elementos != {}
    elif puerta is _puerta_del_grafico:
        # F-034 (2026-09-23) · el gráfico busca con el nº **guardado**, no con
        # el del cuerpo: se exige exactamente esa lectura, ni más ni otra.
        assert dobles.erp.lecturas == [CODIGO_GUARDADO_EN_SIGRID]
    else:
        assert dobles.erp.lecturas == [CODIGO_EN_SIGRID]


def _decision(estado: EstadoParte, *, validacion=None, huella=None) -> DecisionEstado:
    """La decisión de **una persona**, tal y como la devuelve el histórico.

    `validacion` compone la huella del veredicto que se decidió, que es lo que
    R19 compara: una aprobación vale para el veredicto sobre el que se tomó y
    no para el siguiente. `huella` permite escribir a mano la de otro
    veredicto, que es el caso que la puerta tiene que rechazar.
    """
    return DecisionEstado(
        hash_parte=HASH,
        estado=estado,
        decidido_at_utc=AHORA,
        decidido_por=OID,
        motivo="motivo inventado para el test",
        huella_veredicto=(
            huella if validacion is None else huella_de_veredicto(validacion)
        ),
    )


def _con(decision=None, *, cierre: str | None = None) -> RepositorioEnMemoria:
    """Un repositorio que responde esa situación, y **solo** por esa vía.

    Se le pasa la situación y **no** una aprobación de F-026: si la puerta
    siguiera leyendo `consultar_aprobacion`, estos casos no encontrarían nada
    y el test lo diría enseguida.
    """
    return RepositorioEnMemoria(
        situacion=SituacionParte(decision_humana=decision, estado_cierre=cierre)
    )


# --- `aprobado` pasa, y son los dos caminos de llegar ----------------------


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r3_el_parte_apto_sigue_pasando_las_tres_puertas(puerta):
    """R3 · el verde nace `aprobado` y circula como circulaba desde F-006.

    Es el control de que T11 no ha estrechado la puerta: el trabajo diario de
    Posventa —22 partes verdes archivados en bloque— no cambia, y nadie tiene
    que aprobar nada a mano. Lo que F-028 añade no es un permiso más: es poder
    **rechazar** uno antes de que se archive.
    """
    dobles = _dobles()

    puerta(_contexto_para(puerta), _con(), dobles, commit=False)

    _ha_pasado(puerta, dobles)


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r9_un_parte_no_apto_que_una_persona_aprobo_pasa(puerta):
    """R9 · la decisión de una persona manda sobre la máquina.

    Es el reverso exacto de los seis control-negativo de arriba: mismo parte,
    misma llamada, mismo cuerpo. Lo único que cambia es que en el histórico
    consta que alguien lo miró y lo aprobó — y que la huella apuntada es la
    del veredicto que hay guardado ahora (R19).
    """
    ctx = _contexto_para(puerta, apto=False)
    dobles = _dobles()
    aprobado = _decision(EstadoParte.APROBADO, validacion=ctx.validacion)

    puerta(ctx, _con(aprobado), dobles, commit=False)

    _ha_pasado(puerta, dobles)


# --- `rechazado` no pasa, **aunque el veredicto sea apto** -----------------


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r5_un_parte_apto_rechazado_a_mano_no_pasa_ninguna_puerta(puerta):
    """R5 · **el caso que la feature viene a hacer posible.**

    Un parte que la máquina declaró apto y que una persona miró y rechazó no
    se archiva, no se adjunta y no se cierra. Hasta T11 esto era imposible: la
    puerta devolvía «pasa» en cuanto el veredicto era apto y no consultaba
    nada, así que el rechazo no tenía por dónde llegar (`design.md` §0.5).

    El rechazo **no caduca** y no necesita huella: lo automático puede retirar
    un permiso, nunca concederlo. Si caducara, bastaría con volver a lanzar la
    remesa para que un parte que alguien rechazó volviera a entrar en la tanda.
    """
    dobles = _dobles()

    with pytest.raises(ParteNoApto) as fallo:
        puerta(_contexto_para(puerta), _con(_decision(EstadoParte.RECHAZADO)), dobles)

    _nada_ha_salido(dobles)
    assert "rechaz" in fallo.value.motivo.lower()


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r5_el_rechazo_tampoco_caduca_cuando_trae_otra_huella(puerta):
    """R5 · ni siquiera si el veredicto cambió desde que se rechazó.

    La asimetría es deliberada (`design.md` §3): una **aprobación** con otra
    huella deja de contar, un **rechazo** con otra huella sigue contando. Si
    las dos caducaran igual, reprocesar la remesa sería la forma de deshacer
    un rechazo sin que constara que alguien lo deshizo.
    """
    dobles = _dobles()
    rechazo = _decision(EstadoParte.RECHAZADO, huella="huella-de-otro-veredicto")

    with pytest.raises(ParteNoApto):
        puerta(_contexto_para(puerta), _con(rechazo), dobles)

    _nada_ha_salido(dobles)


# --- `pendiente`: la aprobación que dejó de valer --------------------------


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r19_una_aprobacion_sobre_otro_veredicto_no_abre_nada(puerta):
    """R19 · se aprobó *ese* veredicto, y este no es *ese* veredicto.

    Es F-026 R30 conservada entera: el parte vuelve a estar `pendiente` y
    decide la máquina. Que una aprobación deje de contar no es que nadie haya
    rechazado el parte —la pantalla lo distingue (R43)—, pero la puerta hace
    lo mismo con los dos: no se abre.
    """
    dobles = _dobles()
    caducada = _decision(EstadoParte.APROBADO, huella="huella-de-otro-veredicto")

    with pytest.raises(ParteNoApto):
        puerta(_contexto_para(puerta, apto=False), _con(caducada), dobles)

    _nada_ha_salido(dobles)


# --- `cerrado`: terminal, y no se escribe dos veces ------------------------


@pytest.mark.parametrize("estado_cierre", ESTADOS_DE_CIERRE_EN_FIRME)
@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r7_un_parte_ya_cerrado_no_vuelve_a_escribir_nada(puerta, estado_cierre):
    """R7 · `cerrado` es terminal, y de ahí no sale ninguna flecha.

    El parte es **apto**, la llamada trae `commit` y confirmación, y aun así
    no se toca nada: la reclamación ya está cerrada en el ERP y volver a
    recorrer el circuito solo puede escribir dos veces lo que ya está escrito
    —subir otra vez el PDF, adjuntarlo otra vez, pedir otro cierre—.

    Se parametriza sobre `ESTADOS_DE_CIERRE_EN_FIRME` y no sobre dos cadenas
    escritas aquí: el dueño de qué cuenta como cerrado es el dominio, y si
    mañana entrara un tercero este control lo cubriría solo.
    """
    dobles = _dobles()

    with pytest.raises(ParteNoApto) as fallo:
        puerta(_contexto_para(puerta), _con(cierre=estado_cierre), dobles)

    _nada_ha_salido(dobles)
    assert "cerrad" in fallo.value.motivo.lower()


# --- R33 · la situación se lee del almacén, y el atajo del apto se retira --


@pytest.mark.parametrize("puerta", PUERTAS)
@pytest.mark.parametrize("apto", [True, False])
def test_f028_r33_las_tres_puertas_preguntan_por_la_situacion(puerta, apto):
    """R33 · se **pregunta**, y se pregunta por el `hash` del parte.

    Comprobar que se preguntó es la mitad del requisito: una puerta que
    decidiera sin consultar estaría creyéndose lo que le llega.

    Y se pregunta **también para el parte apto**, que es la retirada del atajo
    de `design.md` §6. El coste está declarado y aceptado —una consulta por
    parte y paso, 66 en una tanda de 22— porque sin ella el rechazo de un
    parte verde no funciona, que es medio encargo. Mientras el atajo existió,
    este caso daba `[]` para el apto.

    Se pregunta **una vez** por parte y paso, que es como se acota el coste
    (`design.md` §11.1): lo leído se queda en `ContextoParte.situacion`.
    """
    ctx = _contexto_para(puerta, apto=apto)
    repositorio = _con(_decision(EstadoParte.APROBADO, validacion=ctx.validacion))

    puerta(ctx, repositorio, _dobles(), commit=False)

    assert repositorio.situaciones_consultadas == [HASH]
    assert ctx.situacion is not None


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f028_r33_ninguna_puerta_consulta_ya_la_tabla_de_f026(puerta):
    """La decisión sale del histórico, y de un solo sitio (`design.md` §4).

    `postventa.aprobaciones` se congela: deja de escribirse y deja de leerse,
    y su contenido vigente se sembró en el histórico. Si alguna puerta
    siguiera consultándola, habría **dos** fuentes de la misma decisión y el
    día que divergieran ganaría la que cada puerta hubiera elegido mirar.

    La tabla no se borra y sigue consultable; lo que no puede es decidir.
    """
    repositorio = _con()

    puerta(_contexto_para(puerta), repositorio, _dobles(), commit=False)

    assert repositorio.aprobaciones_consultadas == []
