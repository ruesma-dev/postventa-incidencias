# services/postventa-api/tests/test_f030_veredicto_persistido.py
"""La red de seguridad de F-030, escrita **antes** de tocar producción (T1, T2).

Este fichero es el bloque 0 de la feature y hoy tiene que estar en **ROJO**.
No prueba nada nuevo: reproduce una **regresión que está viva en producción**
desde el despliegue del 2026-09-16 a las 07:33 UTC, y la deja fijada para que
los bloques siguientes no puedan darla por arreglada sin estarlo.

## Qué reproduce, y por qué hacía falta escribirlo antes

`POST /api/archivar`, `POST /api/adjuntar` y `POST /api/cerrar` **no reciben
la extracción** del parte —pedirla obligaría al front a reenviar el DNI y las
observaciones manuscritas del cliente en cada llamada—, así que no pueden
emitir el veredicto. Hasta hoy lo fabrican de todas formas: un
`ResultadoValidacion` con `motivos=()`, `clasificacion_firma=HUMANA`,
`observaciones=None`, `codigo_obra=""` y `numero_incidencia=""`, del que solo
son del parte el `veredicto` y el `destino` que traiga el formulario
(`archivar.py:190-198`, `adjuntar.py:244-249`, `cerrar.py:212-217`).

Desde F-028 T11 la puerta **recomputa la huella** sobre ese objeto de pega, y
de ahí salen las dos caras del defecto, que son los dos casos de T1:

- **(a) la aprobación humana no sobrevive**: la huella apuntada es la del
  veredicto **guardado** y la recomputada es la del stub, así que no coinciden
  nunca, la aprobación no cuenta y el parte vuelve a `pendiente`. Es lo que le
  pasó al parte de la incidencia RS26.09/0178, aprobado a mano y sin archivar;
- **(b) el cuerpo manda, y eso es un agujero de seguridad**: un cuerpo que
  mienta con `veredicto=apto` y `destino=archivo_y_cierre` pasa las tres
  puertas **aunque la validación guardada haya mandado el parte a
  `revision_manual`** (§0.9 de `requirements.md`). Hoy lo único que lo impide
  es que el front mande la verdad.

El test de F-028 no podía cazar ninguna de las dos: construía la decisión y la
puerta **a partir del mismo objeto**, así que las dos huellas coincidían por
construcción. Aquí las dos fuentes están **separadas a propósito** —el cuerpo
en el contexto, el veredicto en el almacén— y es lo único que hace que el caso
sirva de algo.

T2 añade la otra mitad: que el veredicto **recompuesto desde las columnas**
dé exactamente la misma huella que el que estuvo en memoria (R10). Sin esa
garantía, leer de la base no arreglaría nada: la aprobación seguiría sin
contar, solo que por otro motivo.

Sin red, sin base de datos y sin IA: los tres pasos hablan con puertos y se
ejercitan con los dobles de siempre. A los dobles se les pregunta **qué salió
de aquí**, que es la única forma de comprobar que no se tocó SharePoint ni el
ERP de producción.

Ni un dato real: el material sale de `tests/utiles_validacion.py`, inventado
de cabo a rabo.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

import pytest
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_archivo import paso_archivo
from application.pipelines.paso_cierre import paso_cierre
from application.pipelines.paso_grafico import paso_grafico
from domain.models.aprobacion import huella_de_veredicto
from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.errores import ParteNoApto
from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import ClasificacionFirma
from domain.models.grafico import FIRMA_PDF, EstadoGrafico, TrazaGrafico
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import (
    Destino,
    ResultadoValidacion,
    Veredicto,
    validar_parte,
)
from domain.ports.persistencia import RepositorioPartesPort

# Se importa el **módulo** y no la función: `fila_a_validacion_y_cierre` es de
# T4 y todavía no existe, y un `from ... import` dejaría en rojo el fichero
# entero —incluidos los casos de T1, que fallan por su propio motivo y no por
# un import—. Así el rojo de T2 es suyo y se lee solo.
from infrastructure.persistencia import mapeo

from tests.utiles_pg import RepositorioComoLaBase, RepositorioEnMemoria
from tests.utiles_sharepoint import ArchivoPortFalso
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

AHORA = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
HASH = "hash-inventado-del-parte-f030"
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
OBRA = "0000"
INCIDENCIA = "XX00.00 - 0000"

#: El código de la incidencia tal y como lo espera Sigrid.
CODIGO_EN_SIGRID = "XX00.00/0000"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"

#: Los dos destinos no aptos: los que una persona puede acabar decidiendo.
DESTINOS_NO_APTOS = (Destino.COLA_VALIDACION_HUMANA, Destino.REVISION_MANUAL)


# --------------------------------------------------------------------------
# Los dobles que necesitan las dos puertas que hablan con el ERP
# --------------------------------------------------------------------------


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


@dataclass
class Dobles:
    """Los tres sitios por los que un parte puede salir de aquí.

    Van juntos a propósito: lo que se afirma después de cada puerta cerrada no
    es «no se llamó a este método» sino **que no salió nada a ninguna parte**.
    Una puerta que se aflojara y dejara subir el PDF a SharePoint sin cerrar la
    incidencia dejaría el parte a medio camino, que es peor que no empezar.
    """

    archivador: ArchivoPortFalso
    erp: ErpEnMemoria
    graficos: GraficoEnMemoria


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


# --------------------------------------------------------------------------
# El veredicto **guardado**: el que emitió F-004 y está en la base
# --------------------------------------------------------------------------


def _material(destino: Destino):
    """La extracción y la firma que producen **de verdad** ese destino.

    - `cola_validacion_humana`: completo y firmado, con observaciones del
      cliente. Es el destino «hay algo que decidir», y el de RS26.09/0178.
    - `revision_manual`: completo y sin observaciones, pero con una marca en
      la casilla de la firma en vez de una firma.

    Los dos campos decisivos se fijan a los del formulario que manda el front
    (`OBRA`, `INCIDENCIA`): así el cuerpo de la petición dice **la verdad** y
    el único desajuste posible entre las dos huellas es el que introduce el
    stub, que es lo que estos casos vienen a enseñar.
    """
    if destino is Destino.COLA_VALIDACION_HUMANA:
        return (
            extraccion_de_ejemplo(
                hash_parte=HASH, codigo_obra=OBRA, numero_incidencia=INCIDENCIA
            ),
            lectura_de_firma("humana", hash_parte=HASH),
        )
    return (
        extraccion_de_ejemplo(
            hash_parte=HASH,
            codigo_obra=OBRA,
            numero_incidencia=INCIDENCIA,
            observaciones=None,
        ),
        lectura_de_firma("marca_simple", hash_parte=HASH),
    )


def _veredicto_guardado(destino: Destino) -> ResultadoValidacion:
    """El veredicto que **emitió F-004 de verdad** y que está en la base.

    Sale de `validar_parte` y no de un `ResultadoValidacion` montado a mano: si
    mañana F-004 cambiara sus reglas, estos casos se enterarían en vez de
    seguir vigilando un destino que ya no existe.
    """
    extraccion, firma = _material(destino)
    validacion = validar_parte(extraccion, firma)
    assert validacion.destino is destino, "el material del test ya no da ese destino"
    assert validacion.veredicto is Veredicto.NO_APTO
    return validacion


# --------------------------------------------------------------------------
# El contexto que arma el borde: el stub del cuerpo, letra por letra
# --------------------------------------------------------------------------


def _contexto_del_borde(
    *, veredicto: Veredicto, destino: Destino, archivado: bool
) -> ContextoParte:
    """El `ContextoParte` que hoy construyen los tres endpoints del circuito.

    Es `archivar.py:149-199` copiado aquí a propósito —y `adjuntar.py` y
    `cerrar.py`, que lo tienen letra por letra—: del parte real solo sobreviven
    el `veredicto` y el `destino` del formulario, más los dos campos decisivos
    que deciden el nombre del fichero. Todo lo demás del veredicto es
    inventado: sin motivos, firma `humana` fija, sin observaciones y con los
    dos campos decisivos **vacíos** dentro del `ResultadoValidacion`.

    Se escribe aquí y no se importa de `archivar.py` porque T10 va a retirar
    esa construcción del borde, y lo que estos casos tienen que seguir
    vigilando después es otra cosa y más fuerte: que **aunque alguien vuelva a
    meter un veredicto en el contexto**, la puerta no lo mire (R1,
    `design.md` §5.3).

    `archivado` prepara la traza que cada puerta necesita para que el único
    motivo posible de rechazo sea el estado del parte: la del archivo exige que
    **no** conste archivado —si constara, la idempotencia de F-006 cortaría
    antes y el caso daría verde sin probar la puerta— y las del gráfico y el
    cierre exigen justo lo contrario.
    """
    campos = {
        nombre: CampoExtraido(valor=None, confianza_pct=0) for nombre in CAMPOS_DEL_PARTE
    }
    campos["codigo_obra"] = CampoExtraido(valor=OBRA, confianza_pct=100)
    campos["numero_incidencia"] = CampoExtraido(valor=INCIDENCIA, confianza_pct=100)

    return ContextoParte(
        parte=ParteTroceado(
            hash=HASH,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=PDF,
        ),
        extraccion=ExtraccionParte(
            hash_parte=HASH,
            campos=campos,
            traza=TrazaExtraccion(
                proveedor="",
                modelo="",
                prompt_key="",
                version_prompt="",
                huella_prompt="",
            ),
        ),
        validacion=ResultadoValidacion(
            hash_parte=HASH,
            veredicto=veredicto,
            destino=destino,
            motivos=(),
            clasificacion_firma=ClasificacionFirma.HUMANA,
            observaciones=None,
            confianza_observaciones=0,
        ),
        archivo=(
            TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.ARCHIVADO)
            if archivado
            else None
        ),
    )


# --------------------------------------------------------------------------
# El almacén: la situación con el veredicto guardado dentro
# --------------------------------------------------------------------------


def _situacion(
    validacion: ResultadoValidacion | None,
    decision: DecisionEstado | None = None,
    *,
    cierre: str | None = None,
) -> SituacionParte:
    """La situación tal y como la devolverá el repositorio a partir de T6.

    Las cuatro cosas juntas, que es lo que pide R2: el veredicto guardado, la
    última decisión humana y el estado de la traza de cierre salen de la misma
    consulta, y quien deriva el estado no puede mezclar una fuente con otra.

    El andamio de T1 —colgar `validacion` del objeto con `object.__setattr__`
    porque el campo todavía no existía— se retiró en **T3**, que es cuando
    `SituacionParte` ganó su cuarto campo. Aquí ya se construye normal.
    """
    return SituacionParte(
        decision_humana=decision, estado_cierre=cierre, validacion=validacion
    )


def _aprobacion_de_una_persona(validacion: ResultadoValidacion) -> DecisionEstado:
    """La aprobación humana tal y como la dejó apuntada `POST /api/estado`.

    La huella es la del **veredicto guardado**, porque eso es lo que apunta el
    escritor: `estado.py:162` emite el veredicto con la extracción entera y
    `:198` guarda `huella_de_veredicto(validacion)` en la fila del histórico.
    """
    return DecisionEstado(
        hash_parte=HASH,
        estado=EstadoParte.APROBADO,
        decidido_at_utc=AHORA,
        decidido_por=OID,
        motivo="lo miró una persona y lo aprobó",
        huella_veredicto=huella_de_veredicto(validacion),
    )


#: La traza del gráfico **adjuntado**, que F-012 hizo precondición del cierre.
#:
#: No es material de F-030: es el estado del mundo en el que el cierre ocurre.
#: Se inyecta en el caso del cuerpo que miente para que la puerta del gráfico
#: de F-012 no corte antes y el caso pueda enseñar lo que viene a enseñar —que
#: hoy **se llega a escribir en el ERP**—. Sin ella, el parte se pararía en la
#: puerta de al lado y el rojo no diría nada del defecto.
GRAFICO_ADJUNTADO = TrazaGrafico(
    hash_parte=HASH,
    numero_incidencia=CODIGO_EN_SIGRID,
    estado=EstadoGrafico.ADJUNTADO,
    adjuntado_at_utc=AHORA,
)


def _repositorio(
    situacion: SituacionParte, *, con_grafico: bool = False
) -> RepositorioEnMemoria:
    """Un repositorio que responde esa situación, y **solo** por esa vía."""
    return RepositorioEnMemoria(
        situacion=situacion,
        traza_grafico=GRAFICO_ADJUNTADO if con_grafico else None,
    )


# --------------------------------------------------------------------------
# Las tres puertas, llamadas con la misma forma
# --------------------------------------------------------------------------


def _puerta_de_archivo(ctx, repositorio, dobles, *, commit=True):
    return paso_archivo(
        ctx,
        dobles.archivador,
        repositorio,
        carpeta_base="Postventa",
        ahora=AHORA,
    )


def _puerta_del_grafico(ctx, repositorio, dobles, *, commit=True):
    return paso_grafico(
        ctx,
        dobles.erp,
        dobles.graficos,
        repositorio,
        UsuariosConLogin(),
        PreferenciasSinAutoCierre(),
        commit=commit,
        confirmado=True,
        usuario_oid=OID,
        correo=CORREO,
        numero_incidencia=INCIDENCIA,
        codigo_obra=OBRA,
        gratipide=35,
        tope_bytes=10 * 1024 * 1024,
        ahora=AHORA,
    )


def _puerta_del_cierre(ctx, repositorio, dobles, *, commit=True):
    return paso_cierre(
        ctx,
        dobles.erp,
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


#: Las tres puertas del circuito, llamadas con la misma forma.
#:
#: Van parametrizadas y no escritas tres veces porque el requisito es de las
#: tres a la vez: abrir una sola ya deja el parte a medio camino, y cerrar una
#: sola deja la aprobación humana sin efecto igualmente.
PUERTAS = (
    pytest.param(_puerta_de_archivo, id="archivo"),
    pytest.param(_puerta_del_grafico, id="grafico"),
    pytest.param(_puerta_del_cierre, id="cierre"),
)


def _contexto_para(puerta, *, veredicto: Veredicto, destino: Destino) -> ContextoParte:
    """El contexto del borde, con la traza de archivo que esa puerta exige."""
    return _contexto_del_borde(
        veredicto=veredicto,
        destino=destino,
        archivado=puerta is not _puerta_de_archivo,
    )


def _ha_pasado(puerta, dobles: Dobles) -> None:
    """La prueba de que la puerta se abrió, mirada desde fuera.

    Cada puerta deja su huella en un sitio distinto: el archivo, en la
    biblioteca; el gráfico y el cierre, en la lectura de la reclamación que
    hacen nada más pasar. Se mira el efecto y no el retorno del paso a
    propósito: lo que importa es que el parte **siguió su camino**.
    """
    if puerta is _puerta_de_archivo:
        assert dobles.archivador.biblioteca.elementos != {}
    else:
        assert dobles.erp.lecturas == [CODIGO_EN_SIGRID]


# --------------------------------------------------------------------------
# T3 · la situación reúne las cuatro cosas (R2)
# --------------------------------------------------------------------------


def test_f030_r2_la_situacion_reune_las_cuatro_cosas_y_ninguna_mas():
    """R2 · el veredicto guardado viaja **dentro** de la situación.

    Los cuatro hechos que consume `estado_del_parte` salen de la misma
    consulta y del mismo almacén, y por eso quien deriva el estado no puede
    mezclar una fuente con otra. Un quinto campo aquí volvería a abrir la
    pregunta «¿de dónde salió este dato?», que es la que costó la regresión.

    `validacion` va **la última**, y el orden se afirma: todo el código
    construye `SituacionParte` por palabra clave, pero una construcción
    posicional que apareciera por el camino tiene que seguir leyendo los tres
    campos de antes en su sitio.
    """
    nombres = tuple(campo.name for campo in fields(SituacionParte))

    assert nombres == (
        "decision_humana",
        "ultimo_estado_registrado",
        "estado_cierre",
        "validacion",
    )


def test_f030_r2_una_situacion_vacia_sigue_siendo_valida_y_sin_veredicto():
    """Los cuatro huecos vacíos **no son un error**: es el primer día.

    Un parte nace sin veredicto, sin decisión, sin fila y sin traza de cierre.
    Que el campo nuevo tenga valor por defecto es lo que impide que las decenas
    de sitios que hoy construyen la situación con tres argumentos tengan que
    acordarse del cuarto — y lo que hace que el que se olvidara acabara con un
    veredicto inventado, que es justo lo que F-030 viene a quitar.
    """
    situacion = SituacionParte()

    assert situacion.decision_humana is None
    assert situacion.ultimo_estado_registrado is None
    assert situacion.estado_cierre is None
    assert situacion.validacion is None


# --------------------------------------------------------------------------
# T1 (a) · la aprobación humana no sobrevive a la puerta — **el defecto**
# --------------------------------------------------------------------------


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r11_un_parte_no_apto_aprobado_a_mano_pasa_las_tres_puertas(
    puerta, destino
):
    """R11 · lo que aprobó una persona sobre el veredicto guardado, pasa.

    **Este es el caso que está roto en producción.** Todo está en su sitio: el
    veredicto guardado en la base, la aprobación de una persona con la huella
    de **ese** veredicto y el cuerpo real del formulario, que dice la verdad.
    La puerta tiene que abrirse en las tres.

    Hoy no se abre, y el motivo es que la puerta recompone la huella sobre el
    veredicto de pega que arma el borde: la apuntada es la del veredicto
    guardado y la recomputada, la de un objeto sin motivos, sin observaciones
    y con los dos campos decisivos vacíos. No coinciden nunca, la aprobación
    no cuenta y el parte vuelve a `pendiente`.

    Es la incidencia **RS26.09/0178**: aprobada a mano el 2026-09-16 a las
    18:09:33 y todavía sin archivar.
    """
    guardado = _veredicto_guardado(destino)
    ctx = _contexto_para(puerta, veredicto=guardado.veredicto, destino=guardado.destino)
    repositorio = _repositorio(
        _situacion(guardado, _aprobacion_de_una_persona(guardado))
    )
    dobles = _dobles()

    puerta(ctx, repositorio, dobles, commit=False)

    _ha_pasado(puerta, dobles)
    assert repositorio.situaciones_consultadas == [HASH], (
        "la puerta tiene que preguntarle al almacén: decidir con lo que traiga "
        "el cuerpo es el defecto entero"
    )


def test_f030_r1_la_huella_del_stub_del_cuerpo_no_depende_del_parte():
    """R1 · la huella con la que se juzga hoy es **una constante**.

    Es la medida que explica por qué el caso de arriba falla, y por qué falla
    igual para los 22 partes de una remesa: de los seis campos de la cadena
    canónica, el stub del borde solo varía el `destino` —los otros cinco son
    fijos—, así que la huella recomputada es una de tres y no dice nada del
    parte que se está juzgando.

    Que la huella con la que se juzga sea la misma para dos partes distintos es
    la forma más corta de decir que no se está juzgando nada.
    """
    guardado = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    stub_de_este_parte = _contexto_del_borde(
        veredicto=guardado.veredicto, destino=guardado.destino, archivado=False
    ).validacion
    stub_de_otro_parte = replace(
        stub_de_este_parte,
        hash_parte="otro-hash-inventado",
        observaciones="otro texto que el stub tira igual",
    )

    assert huella_de_veredicto(stub_de_este_parte) == huella_de_veredicto(
        replace(stub_de_otro_parte, observaciones=None)
    )
    assert huella_de_veredicto(stub_de_este_parte) != huella_de_veredicto(guardado)


# --------------------------------------------------------------------------
# T1 (b) · el cuerpo que miente — **la segunda cara, y es de seguridad**
# --------------------------------------------------------------------------


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r7_un_cuerpo_que_miente_no_pasa_ninguna_de_las_tres_puertas(puerta):
    """R7 · quien llama no puede declararse apto a sí mismo (§0.9).

    El parte está guardado con el veredicto que emitió F-004: **no apto**, a
    `revision_manual`, y nadie lo ha decidido. El cuerpo de la petición dice
    `veredicto=apto` y `destino=archivo_y_cierre`. Ninguna de las tres puertas
    puede abrirse, y no puede salir nada a SharePoint ni al ERP.

    Hoy se abren las tres: como la puerta deriva el estado del veredicto del
    cuerpo, `estado_de_la_maquina(stub)` devuelve `aprobado` sin que ninguna
    persona haya decidido nada. Lo único que lo impide en producción es que el
    front mande la verdad, y eso no es una puerta: es una costumbre.
    """
    guardado = _veredicto_guardado(Destino.REVISION_MANUAL)
    ctx = _contexto_para(
        puerta, veredicto=Veredicto.APTO, destino=Destino.ARCHIVO_Y_CIERRE
    )
    repositorio = _repositorio(_situacion(guardado), con_grafico=True)
    dobles = _dobles()

    with pytest.raises(ParteNoApto) as fallo:
        puerta(ctx, repositorio, dobles)

    _nada_ha_salido(dobles)
    assert repositorio.archivos == []
    assert repositorio.graficos == []
    assert repositorio.cierres == []
    assert fallo.value.motivo, "el rechazo tiene que decir por qué"


# --------------------------------------------------------------------------
# T8 · la puerta juzga el veredicto **guardado** (R1, R8, R17)
# --------------------------------------------------------------------------
#
# Los casos de T1 comprueban el resultado —el parte pasa, o no pasa—. Estos
# comprueban **de dónde sale la decisión**, que es lo que la feature cambia y
# lo único que impide que el defecto vuelva: la puerta lee
# `ctx.situacion.validacion` y no vuelve a mirar `ctx.validacion`
# (`design.md` §5.3).

#: El final propio de cada puerta: la parte del mensaje que le dice a quien lo
#: lee **qué se ha quedado sin hacer** (R17).
FINALES = {
    _puerta_de_archivo: "no se archiva",
    _puerta_del_grafico: "no se adjunta a la reclamación",
    _puerta_del_cierre: "no se cierra la incidencia",
}


def _veredicto_apto_guardado() -> ResultadoValidacion:
    """El veredicto **apto** que emitiría F-004, con los dos campos del cuerpo.

    Completo, firmado por una persona y sin observaciones manuscritas: es el
    parte que recorre el circuito sin que nadie decida nada (R14).
    """
    extraccion = extraccion_de_ejemplo(
        hash_parte=HASH,
        codigo_obra=OBRA,
        numero_incidencia=INCIDENCIA,
        observaciones=None,
    )
    validacion = validar_parte(extraccion, lectura_de_firma("humana", hash_parte=HASH))
    assert validacion.veredicto is Veredicto.APTO
    assert validacion.destino is Destino.ARCHIVO_Y_CIERRE
    return validacion


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r1_un_stub_apto_en_el_contexto_no_abre_ninguna_puerta(puerta):
    """R1 · el contexto dice `apto`, el almacén dice `revision_manual`: no pasa.

    Es **el caso decisivo de la feature**, y lleva las dos fuentes a la
    contradicción máxima a propósito: el veredicto del contexto es apto con
    destino `archivo_y_cierre` —el que abriría la puerta sin que nadie haya
    decidido nada— y el guardado es no apto a `revision_manual`, sin decisión
    humana ninguna.

    Manda el guardado. Y el blindaje que fija este caso es más fuerte que «el
    borde ya no fabrica el veredicto», que es lo que retira T10: aunque
    **alguien vuelva a meter un veredicto en el contexto** —un endpoint nuevo,
    un rebase infeliz, una prueba a mano que se quedó—, esta puerta no lo
    mira. El centinela estructural de T12 vigila que nadie lo fabrique; este
    vigila que, si lo fabrican, no sirva de nada.
    """
    guardado = _veredicto_guardado(Destino.REVISION_MANUAL)
    ctx = _contexto_para(
        puerta, veredicto=Veredicto.APTO, destino=Destino.ARCHIVO_Y_CIERRE
    )
    repositorio = _repositorio(_situacion(guardado), con_grafico=True)
    dobles = _dobles()

    with pytest.raises(ParteNoApto):
        puerta(ctx, repositorio, dobles)

    _nada_ha_salido(dobles)
    assert ctx.validacion is not None, (
        "el contexto sigue trayendo su veredicto: lo que se afirma es que la "
        "puerta no lo mira, no que nadie se lo haya puesto"
    )


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r1_un_stub_no_apto_en_el_contexto_no_cierra_una_puerta_abierta(puerta):
    """R1 · y al revés: el contexto dice que no y el almacén que sí. Pasa.

    La otra mitad, y sin ella la anterior no demuestra lo que dice: una puerta
    que se limitara a rechazarlo todo también pasaría aquel caso. Aquí el
    veredicto guardado es **apto a `archivo_y_cierre`** y el del contexto es
    no apto a `revision_manual`; si la puerta mirase el contexto —o los dos, o
    el más estricto de los dos—, el parte no pasaría.

    Nadie ha decidido nada: pasa por ser apto, que es el camino normal de R14
    y el que tiene que seguir funcionando igual que ayer.
    """
    ctx = _contexto_para(
        puerta, veredicto=Veredicto.NO_APTO, destino=Destino.REVISION_MANUAL
    )
    repositorio = _repositorio(_situacion(_veredicto_apto_guardado()))
    dobles = _dobles()

    puerta(ctx, repositorio, dobles, commit=False)

    _ha_pasado(puerta, dobles)


@pytest.mark.parametrize("destino", DESTINOS_NO_APTOS)
@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r17_el_mensaje_de_pendiente_nombra_el_destino_guardado(puerta, destino):
    """R17 · el mensaje dice el destino **guardado**, y acaba como el suyo.

    El motivo importa porque cada estado se arregla de una forma distinta y
    quien lee el error es quien va a arreglarlo: darle el destino del cuerpo
    sería mandarle a mirar un dato que no ha decidido nada. El cuerpo miente
    aquí a propósito con `archivo_y_cierre`, y ese literal **no puede
    aparecer** en el mensaje.

    Y los tres finales siguen siendo los suyos —«no se archiva», «no se
    adjunta a la reclamación», «no se cierra la incidencia»—, que es la parte
    del mensaje que dice qué se ha quedado sin hacer.
    """
    guardado = _veredicto_guardado(destino)
    ctx = _contexto_para(
        puerta, veredicto=Veredicto.APTO, destino=Destino.ARCHIVO_Y_CIERRE
    )
    repositorio = _repositorio(_situacion(guardado), con_grafico=True)

    with pytest.raises(ParteNoApto) as fallo:
        puerta(ctx, repositorio, _dobles())

    motivo = fallo.value.motivo
    assert "este parte está pendiente" in motivo
    assert f"«{destino.value}»" in motivo
    assert Destino.ARCHIVO_Y_CIERRE.value not in motivo, (
        "el destino del cuerpo no pinta nada en el mensaje: manda el guardado"
    )
    assert motivo.endswith(f"así que {FINALES[puerta]}")


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r8_sin_veredicto_guardado_cada_puerta_dice_lo_suyo(puerta):
    """R8, R17 · «no hay veredicto» sigue siendo el primer motivo, y el suyo.

    Al mudarse la fuente, el orden se invierte: **primero se consulta** y
    después se mira si hay veredicto, porque no hay forma de saber si consta
    validación sin preguntar. Lo que no cambia es la precedencia de los
    motivos ni lo que se le cuenta a quien lee el error: «no consta que este
    parte haya pasado la validación» sigue yendo el primero y sigue siendo un
    motivo propio, que se arregla **revalidando** el parte y no decidiendo
    sobre él.

    El cuerpo trae un veredicto apto y no sirve de nada: es la misma lectura
    de R1 desde el otro lado.
    """
    ctx = _contexto_para(
        puerta, veredicto=Veredicto.APTO, destino=Destino.ARCHIVO_Y_CIERRE
    )
    repositorio = _repositorio(_situacion(None), con_grafico=True)
    dobles = _dobles()

    with pytest.raises(ParteNoApto) as fallo:
        puerta(ctx, repositorio, dobles)

    motivo = fallo.value.motivo
    assert motivo.startswith("no consta que este parte haya pasado la validación")
    assert "pendiente" not in motivo, "el de «sin veredicto» es un motivo propio"
    _nada_ha_salido(dobles)
    assert repositorio.situaciones_consultadas == [HASH], (
        "se consulta **antes** de decir que no: es el precio de no poder "
        "saberlo sin preguntar (`design.md` §5.3, punto 2)"
    )


# --------------------------------------------------------------------------
# T2 · la ida y vuelta de la huella (R10)
# --------------------------------------------------------------------------
#
# Leer el veredicto de la base solo arregla el defecto si el veredicto
# recompuesto desde las columnas produce **exactamente la misma huella** que el
# que estuvo en memoria. Si derivara aunque fuera en un espacio, la aprobación
# seguiría sin contar y solo habríamos cambiado el motivo.
#
# Las tres equivalencias que lo sostienen (`design.md` §2) son las que esta
# tabla recorre: `None` y «solo espacios» dan la misma huella, el orden de los
# motivos da igual porque la huella los ordena, y el recorte de los avisos a
# 240 caracteres no entra en la cadena canónica.

#: «Esta columna de `partes` trae lo mismo que el veredicto en memoria».
IGUAL = object()


@dataclass(frozen=True)
class CasoDeHuella:
    """Un veredicto en memoria y las columnas con las que se recompone.

    `observaciones`, `codigo_obra` y `numero_incidencia` son las tres columnas
    que la consulta trae de `postventa.partes` con un `JOIN`, y son justo
    donde aparecen las diferencias que no deben caducar una aprobación: la base
    guarda **el literal que leyó el modelo** y el veredicto guarda lo que
    `validar_parte` hizo con él.
    """

    nombre: str
    validacion: ResultadoValidacion
    observaciones: Any = IGUAL
    codigo_obra: Any = IGUAL
    numero_incidencia: Any = IGUAL
    motivos_al_reves: bool = False

    def columnas_de_partes(self) -> tuple[Any, ...]:
        """Las cuatro columnas que salen de `postventa.partes`."""
        return (
            self.validacion.observaciones
            if self.observaciones is IGUAL
            else self.observaciones,
            self.validacion.confianza_observaciones,
            self.validacion.codigo_obra
            if self.codigo_obra is IGUAL
            else self.codigo_obra,
            self.validacion.numero_incidencia
            if self.numero_incidencia is IGUAL
            else self.numero_incidencia,
        )


def _fila_de_la_consulta(caso: CasoDeHuella) -> tuple[Any, ...]:
    """La fila que devolverá `select_veredicto_y_cierre` (`design.md` §3).

    Las cinco primeras columnas se sacan de `mapeo.valores_de_validacion`, que
    es **la misma función que escribió la fila**: si mañana cambiara el orden
    de lo que se guarda, este test se enteraría en vez de comparar contra una
    copia del orden escrita a mano.
    """
    _, veredicto, destino, clasificacion, motivos, avisos, _ = (
        mapeo.valores_de_validacion(caso.validacion, AHORA)
    )
    if caso.motivos_al_reves:
        motivos = mapeo.json_de_motivos(tuple(reversed(caso.validacion.motivos)))

    return (veredicto, destino, clasificacion, motivos, avisos) + (
        caso.columnas_de_partes()
    ) + (None,)


def _casos_de_huella() -> tuple[CasoDeHuella, ...]:
    """La tabla de casos borde de R10, cada uno con su porqué.

    Ninguno es rebuscado: los seis salen de cómo lee el modelo y de cómo
    guarda la base. El que se dejara fuera sería el que caducara una
    aprobación humana el día que apareciera.
    """
    con_observaciones = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    con_dos_motivos = validar_parte(
        extraccion_de_ejemplo(
            hash_parte=HASH, codigo_obra=OBRA, numero_incidencia=INCIDENCIA
        ),
        lectura_de_firma("marca_simple", hash_parte=HASH),
    )
    assert len(con_dos_motivos.motivos) >= 2, "el caso del orden necesita dos motivos"

    return (
        CasoDeHuella(
            nombre="motivos_en_orden_inverso",
            validacion=con_dos_motivos,
            motivos_al_reves=True,
        ),
        CasoDeHuella(
            nombre="observaciones_con_saltos_de_linea_y_mayusculas",
            validacion=con_observaciones,
            observaciones=(
                f"  {con_observaciones.observaciones.upper().replace(' ', chr(10))}  "
            ),
        ),
        CasoDeHuella(
            nombre="observaciones_none_frente_a_solo_espacios",
            validacion=replace(con_observaciones, observaciones=None),
            observaciones="   ",
        ),
        CasoDeHuella(
            nombre="codigo_obra_con_espacio_final",
            validacion=con_observaciones,
            codigo_obra=f"{OBRA} ",
        ),
        CasoDeHuella(
            nombre="numero_incidencia_con_espacios_en_el_separador",
            validacion=con_observaciones,
            numero_incidencia=INCIDENCIA.replace(" - ", "  -  "),
        ),
        CasoDeHuella(
            nombre="campos_decisivos_vacios_guardados_como_null",
            validacion=replace(con_observaciones, codigo_obra="", numero_incidencia=""),
            codigo_obra=None,
            numero_incidencia=None,
        ),
        CasoDeHuella(
            nombre="un_aviso_de_mas_de_240_caracteres",
            validacion=replace(con_observaciones, avisos=("A" * 300,)),
        ),
    )


@pytest.mark.parametrize(
    "caso", [pytest.param(caso, id=caso.nombre) for caso in _casos_de_huella()]
)
def test_f030_r10_el_veredicto_recompuesto_da_la_misma_huella(caso: CasoDeHuella):
    """R10 · lo guardado basta para recomponer la huella, y da la misma.

    Es lo que sostiene D3 —«sin columna nueva»— y lo que hace que la aprobación
    de RS26.09/0178 siga valiendo en cuanto se despliegue F-030: la huella que
    apuntó el escritor salió del veredicto que esa misma llamada guardó, así
    que la recompuesta desde esas dos filas tiene que ser la misma.

    Hoy falla porque `mapeo.fila_a_validacion_y_cierre` es de T4 y todavía no
    existe. Ese rojo es el esperado en el bloque 0.
    """
    recompuesto, estado_cierre = mapeo.fila_a_validacion_y_cierre(
        _fila_de_la_consulta(caso), hash_parte=HASH
    )

    assert huella_de_veredicto(recompuesto) == huella_de_veredicto(caso.validacion)
    assert recompuesto.hash_parte == HASH
    assert recompuesto.veredicto is caso.validacion.veredicto
    assert recompuesto.destino is caso.validacion.destino
    assert estado_cierre is None


# --------------------------------------------------------------------------
# T7 · el contrato del puerto dice lo que pasa ahora
# --------------------------------------------------------------------------
#
# Lo que se vigila aquí **no es un documento técnico, es la memoria de una
# decisión**, y se sigue la regla del proyecto: lo que se deroga **no se
# borra**, se enmienda con un recuadro fechado que cita la premisa original
# literal. El motivo, aquí, es más concreto que de costumbre: la premisa que
# `guardar_validacion` sostenía —«los tres pasos del circuito … no puede[n]
# recomputar la huella»— es la **descripción literal del defecto**. Quien la
# leyera dentro de seis meses tendría delante el razonamiento que llevó a
# fabricar un veredicto de pega, escrito en el sitio donde se declaran los
# contratos.

#: La premisa retirada, literal. Sigue en el puerto, **dentro del recuadro**.
PREMISA_RETIRADA = "no puede** recomputar la huella"

#: Lo que el puerto afirmaba y ya no es cierto desde F-028 T15.
REVOCACION_RETIRADA = "revoca la aprobación humana cuyo veredicto ya no es este"


def _llano(texto: str) -> str:
    """El texto con los saltos de línea colapsados, para buscar frases en él."""
    return " ".join(texto.split())


def _afirmado(docstring: str) -> str:
    """El contrato **sin** las líneas citadas en el recuadro de enmienda.

    Un recuadro cita el texto viejo entero, así que buscarlo en la docstring
    completa no distingue «lo sigue afirmando» de «lo cita para decir que ya no
    vale». Lo que se afirma es lo que queda fuera del `>`.
    """
    return _llano(
        "\n".join(
            linea
            for linea in docstring.splitlines()
            if not linea.strip().startswith(">")
        )
    )


def test_f030_r1_el_puerto_no_gana_ningun_metodo():
    """El contrato no crece: la cuarta cosa viaja en la respuesta que ya había.

    Un `consultar_validacion` aparte habría costado tres consultas más por
    parte —una por paso del circuito— contra un PostgreSQL compartido con otros
    proyectos (R18). Que el puerto tenga los mismos métodos que antes es la
    forma de comprobar que la lectura del veredicto no se ha ido por su cuenta.
    """
    metodos = {
        nombre for nombre in vars(RepositorioPartesPort) if not nombre.startswith("_")
    }

    assert "consultar_validacion" not in metodos
    assert "consultar_situacion" in metodos
    assert "consultar_estado_cierre" in metodos


def test_f030_r2_el_puerto_promete_cuatro_cosas_y_no_tres():
    """`consultar_situacion` documenta las cuatro, y de dónde salen.

    El contrato es lo que lee quien implemente otro adaptador —o el doble de un
    test—: si siguiera prometiendo tres, el veredicto volvería a ser algo que
    cada consumidor se busca por su cuenta, que es exactamente como empezó
    esto.
    """
    afirmado = _afirmado(inspect.getdoc(RepositorioPartesPort.consultar_situacion))

    assert "**cuatro** cosas de vuelta" in afirmado
    assert "el veredicto guardado" in afirmado
    assert "nunca del cuerpo de la petición" in afirmado


def test_f030_r1_el_puerto_ya_no_afirma_la_revocacion_ni_la_premisa_del_defecto():
    """Las dos frases que `guardar_validacion` sostenía y ya no son ciertas.

    La primera la retiró **F-028 T15**: la vigencia de una aprobación se
    resuelve al derivar el estado, no con una escritura que marca la fila. El
    adaptador llevaba su enmienda desde entonces; el puerto se había quedado
    sin ella.

    La segunda es **la descripción literal del defecto**: era cierta cuando se
    escribió y dejó de serlo hoy. Los tres pasos del circuito no recomponen la
    huella del cuerpo — la recomponen del veredicto **guardado**.
    """
    afirmado = _afirmado(inspect.getdoc(RepositorioPartesPort.guardar_validacion))

    assert REVOCACION_RETIRADA not in afirmado
    assert PREMISA_RETIRADA not in afirmado


def test_f030_r1_las_dos_premisas_retiradas_siguen_citadas_y_fechadas():
    """Control negativo: enmendar es **añadir un recuadro**, no borrar el texto.

    Si alguien reescribe el contrato y se lleva por delante la cita, se pierde
    lo único que explica por qué el código hacía lo que hacía — y el siguiente
    que lea `_como_contexto` sin ese rastro volverá a fabricar el veredicto,
    que es precisamente lo que pasó.
    """
    contrato = _llano(inspect.getdoc(RepositorioPartesPort.guardar_validacion))

    assert "Enmienda del 2026-09-16 · F-030 T7" in contrato
    assert REVOCACION_RETIRADA in contrato
    assert PREMISA_RETIRADA in contrato
    assert "RS26.09/0178" in contrato


# --------------------------------------------------------------------------
# T12 · el centinela estructural (R3)
# --------------------------------------------------------------------------
#
# Todo lo de arriba vigila el **comportamiento**: que la puerta decida con lo
# guardado. Esto vigila la **causa**: que nadie vuelva a fabricar un veredicto
# en el borde. Son cosas distintas y hacen falta las dos —un stub que nadie
# mire no rompe nada hoy, pero es el material con el que se reconstruye el
# defecto—, y esta es la barata: no se puede esquivar sin verla, y ataca la
# construcción a mano y no el síntoma.
#
# Mismo patrón que
# `test_f028_persistencia.py::test_f028_t15_ningun_modulo_de_produccion_escribe_en_la_tabla_de_f026`,
# y por el mismo motivo: lo que no se puede mutar hay que mirarlo.

#: La carpeta del borde HTTP, la que este centinela recorre entera.
BORDE_HTTP = Path(__file__).resolve().parents[1] / "interface_adapters" / "api"


def _construcciones_de(ruta: Path) -> list[int]:
    """Las líneas de ese módulo que **construyen** un `ResultadoValidacion`.

    Se mira el árbol y no el texto: `"ResultadoValidacion"` aparece en las
    anotaciones de tipo de `parte.py`, `validar.py` y `estado_serializado.py`
    —que son legítimas— y en las cabeceras de los tres endpoints, que cuentan
    lo que pasó. Un `grep` las cazaría todas y el centinela nacería inútil o
    lleno de excepciones. Lo que se busca es una **llamada**, que es la única
    forma de fabricar uno.

    Se acepta tanto `ResultadoValidacion(...)` como
    `validacion.ResultadoValidacion(...)`: cambiar la forma del import no
    puede ser la manera de esquivar esto.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    llamadas = (nodo for nodo in ast.walk(arbol) if isinstance(nodo, ast.Call))
    return sorted(
        llamada.lineno
        for llamada in llamadas
        if (
            isinstance(llamada.func, ast.Name)
            and llamada.func.id == "ResultadoValidacion"
        )
        or (
            isinstance(llamada.func, ast.Attribute)
            and llamada.func.attr == "ResultadoValidacion"
        )
    )


def test_f030_r3_ningun_modulo_del_borde_construye_un_veredicto():
    """R3 · el veredicto lo emite F-004 con la extracción, o no existe.

    **Lo que falló no fue un cálculo mal hecho: fue una construcción a mano.**
    `archivar.py`, `adjuntar.py` y `cerrar.py` montaban un `ResultadoValidacion`
    con el `veredicto` y el `destino` del formulario y valores fijos para el
    resto, sobre un parte que desde ese endpoint no había mirado nadie. De ahí
    salieron las dos caras del defecto: una huella que no dependía del parte y
    un cuerpo que podía declararse apto a sí mismo.

    El control recorre **la carpeta entera** y no los tres ficheros de la
    feature: el fallo que este caso existe para cazar es que mañana aparezca un
    endpoint nuevo que vuelva a fabricarlo, y un control apuntado a tres
    nombres no lo vería.

    Quien sí puede emitir un veredicto es quien trae la extracción, y lo hace
    llamando a `validar_parte` —`parte.py`, `validar.py`, `estado.py`—, que es
    justo lo que esta comprobación deja pasar: `validar_parte(...)` es una
    llamada a otra cosa.
    """
    modulos = sorted(BORDE_HTTP.glob("*.py"))
    assert modulos, "la carpeta del borde no puede estar vacía: el control se cayó"

    culpables = {
        ruta.name: lineas
        for ruta in modulos
        if (lineas := _construcciones_de(ruta))
    }

    assert culpables == {}, (
        "estos módulos del borde fabrican un ResultadoValidacion, y eso es "
        "exactamente lo que rompió el circuito en F-030: el veredicto lo emite "
        f"F-004 con la extracción, o se lee de la base. {culpables}"
    )


def test_f030_r3_el_centinela_sabe_ver_una_construccion():
    """El control del control: un centinela que no se ha visto fallar no vale.

    Se le da un módulo escrito aquí mismo con la construcción de pega que
    tenía `archivar.py` —la misma, letra por letra— y tiene que verla. Sin
    este caso, un error en el recorrido del árbol dejaría el centinela en
    verde para siempre y nadie se enteraría.

    Y el negativo al lado: una **anotación de tipo** con ese mismo nombre no
    es una construcción y no puede hacerlo saltar, que es lo que separa este
    control de un `grep`.
    """
    fabrica = dedent(
        '''
        from domain.models.validacion import ResultadoValidacion

        def _como_contexto(veredicto, destino) -> ResultadoValidacion | None:
            return ResultadoValidacion(
                hash_parte="da igual",
                veredicto=Veredicto(veredicto),
                destino=Destino(destino),
                motivos=(),
                clasificacion_firma=ClasificacionFirma.HUMANA,
                observaciones=None,
                confianza_observaciones=0,
            )
        '''
    )
    solo_anotaciones = dedent(
        '''
        from domain.models.validacion import ResultadoValidacion, validar_parte

        def _emitir(extraccion, firma) -> ResultadoValidacion:
            resultado: ResultadoValidacion = validar_parte(extraccion, firma)
            return resultado
        '''
    )

    with TemporaryDirectory() as carpeta:
        culpable = Path(carpeta) / "fabrica.py"
        culpable.write_text(fabrica, encoding="utf-8")
        inocente = Path(carpeta) / "anotaciones.py"
        inocente.write_text(solo_anotaciones, encoding="utf-8")

        assert _construcciones_de(culpable) != []
        assert _construcciones_de(inocente) == []


# --------------------------------------------------------------------------
# T13 · el doble que se comporta como la base (R23, `design.md` §7.1)
# --------------------------------------------------------------------------
#
# `RepositorioEnMemoria` devuelve **el mismo objeto** que se le dio, y por eso
# el test de F-028 no podía cazar la regresión ni aunque estuviera escrito: la
# decisión y la puerta salían del mismo `ResultadoValidacion` y las dos huellas
# coincidían por construcción. `RepositorioComoLaBase` no puede hacer eso
# porque **no guarda el objeto**, solo sus columnas.
#
# Este caso es el control del doble: sin él, el circuito de borde a borde de
# T14 podría pasar por la razón equivocada —que el doble devuelva lo que
# entró— y no probaría nada de lo que dice probar.


def _parte_troceado() -> ParteTroceado:
    """El parte tal y como sale de `POST /api/split`, sin los bytes."""
    return ParteTroceado(
        hash=HASH,
        origen="remesa-inventada.pdf",
        paginas_origen=(3,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"",
    )


def test_f030_r23_el_doble_de_la_base_no_devuelve_el_objeto_que_entro():
    """R23 · lo que vuelve es **otro objeto** y tiene **la misma huella**.

    Las dos mitades importan y ninguna sola vale:

    - si volviera el mismo objeto, el doble sería `RepositorioEnMemoria` con
      otro nombre y el circuito de T14 pasaría por la razón equivocada;
    - si volviera otro objeto con otra huella, la aprobación de una persona
      caducaría en cuanto el veredicto diera una vuelta por la base, que es
      justo lo que R10 impide y lo que hace que RS26.09/0178 se archive sin
      volver a decidir.

    El veredicto lleva **observaciones manuscritas** a propósito: son la
    columna que no está en `validaciones` —su DDL prohíbe copiar ahí el texto
    del cliente (R21, R39)— y la que la recomposición tiene que ir a buscar a
    `partes`. Una recomposición que las perdiera daría otra huella y este caso
    se pondría rojo.
    """
    base = RepositorioComoLaBase()
    validacion = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    extraccion, _ = _material(Destino.COLA_VALIDACION_HUMANA)
    assert validacion.observaciones, "este caso necesita observaciones manuscritas"

    base.guardar_parte(
        parte=_parte_troceado(),
        extraccion=extraccion,
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    base.guardar_validacion(resultado=validacion, ahora=AHORA)

    situacion = base.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is not validacion
    assert huella_de_veredicto(situacion.validacion) == huella_de_veredicto(validacion)
    assert situacion.validacion.observaciones == validacion.observaciones
    assert situacion.validacion.destino is validacion.destino
    assert situacion.validacion.codigo_obra == OBRA
    assert situacion.validacion.numero_incidencia == INCIDENCIA


def test_f030_r23_el_doble_de_la_base_no_guarda_ni_un_veredicto_dentro():
    """R23 · la propiedad, comprobada **por construcción** y no de oídas.

    El caso de arriba mira lo que vuelve; este mira lo que queda dentro. Si
    mañana alguien le añadiera al doble un atajo —«me quedo el objeto y lo
    devuelvo, que es más cómodo»—, el de arriba seguiría en verde y este no:
    lo que hace útil a este doble es exactamente que **no pueda** hacer eso.
    """
    base = RepositorioComoLaBase()
    extraccion, _ = _material(Destino.COLA_VALIDACION_HUMANA)
    base.guardar_parte(
        parte=_parte_troceado(),
        extraccion=extraccion,
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    base.guardar_validacion(
        resultado=_veredicto_guardado(Destino.COLA_VALIDACION_HUMANA), ahora=AHORA
    )

    guardado = [
        valor
        for fila in (
            *base.columnas_de_validaciones.values(),
            *base.columnas_de_partes.values(),
        )
        for valor in fila
    ]

    assert guardado, "el doble no ha guardado nada y el caso no probaría nada"
    assert not any(isinstance(valor, ResultadoValidacion) for valor in guardado)
    assert not any(isinstance(valor, ExtraccionParte) for valor in guardado)


def test_f030_r23_sin_ficha_del_parte_el_doble_no_devuelve_veredicto():
    """R8, R9 · la consulta se ancla en `partes`, y el doble también.

    Un parte del que no consta ni la ficha no devuelve ninguna fila, y eso son
    veredicto `None` y cierre `None` — no un error. De ahí sale el «no consta
    que este parte haya pasado la validación» de las tres puertas.
    """
    situacion = RepositorioComoLaBase().consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is None
    assert situacion.estado_cierre is None
    assert situacion.decision_humana is None
    assert situacion.ultimo_estado_registrado is None


# --------------------------------------------------------------------------
# T16 · compatibilidad hacia atrás: qué pasa con lo ya decidido (R11, R12, §8)
# --------------------------------------------------------------------------
#
# La pregunta que contesta esta sección es la que el humano va a comprobar
# mañana con su parte: **¿hay que volver a decidir lo ya decidido?** No. Y no
# porque se haya migrado nada, sino porque **la huella no cambia** (R13): la
# que apuntó `POST /api/estado` salió del veredicto que esa misma llamada
# guardó unas líneas antes, así que la recompuesta desde esas filas es la
# misma.
#
# Va contra `RepositorioComoLaBase` y no contra un `SituacionParte` montado a
# mano: lo que hay que demostrar es justamente que la decisión sobrevive **al
# viaje por las columnas**, y un doble que devolviera el objeto que entró no
# demostraría nada.


def _base_con_lo_guardado(
    validacion: ResultadoValidacion,
    *,
    decision: DecisionEstado | None = None,
) -> RepositorioComoLaBase:
    """La base tal y como la dejó `POST /api/estado` el día que se decidió.

    La ficha del parte, su veredicto y —si la hubo— la fila del histórico, en
    el mismo orden en el que las escribe el circuito de verdad.
    """
    base = RepositorioComoLaBase()
    extraccion, _ = _material(validacion.destino)
    base.guardar_parte(
        parte=_parte_troceado(),
        extraccion=extraccion,
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    base.guardar_validacion(resultado=validacion, ahora=AHORA)
    if decision is not None:
        base.registrar_decision(decision=decision)
    return base


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r11_una_decision_ya_guardada_sigue_aprobando_sin_volver_a_decidir(
    puerta,
):
    """R11, §8 · **no hay migración y no hay que volver a decidir nada.**

    Es lo que va a pasar con el parte `b7e9b037` de RS26.09/0178 en cuanto se
    despliegue F-030: la aprobación está en `postventa.historico_estado` desde
    el 2026-09-16 con su huella real, el veredicto está en
    `postventa.validaciones`, y la puerta compara por fin las dos cosas que hay
    que comparar. Se archiva sin que nadie toque nada.

    Y **sin escribir ninguna decisión nueva**: eso es lo que afirma el recuento
    del histórico. Una puerta que «arreglara» esto volviendo a apuntar algo
    estaría decidiendo por su cuenta, que es lo contrario de lo que se quiere.
    """
    guardado = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    aprobacion = _aprobacion_de_una_persona(guardado)
    base = _base_con_lo_guardado(guardado, decision=aprobacion)
    ctx = _contexto_para(puerta, veredicto=guardado.veredicto, destino=guardado.destino)
    dobles = _dobles()

    puerta(ctx, base, dobles, commit=False)

    _ha_pasado(puerta, dobles)
    assert base.decisiones == [aprobacion], (
        "la puerta no puede apuntar nada: lo suyo es dejar pasar o no"
    )


@pytest.mark.parametrize("puerta", PUERTAS)
def test_f030_r12_si_el_veredicto_guardado_cambia_la_aprobacion_deja_de_contar(
    puerta,
):
    """R12, §8 · la otra mitad, y es la que hace que R11 no sea un agujero.

    Una aprobación dice **sobre qué veredicto exacto** decidió una persona. Si
    el parte se revalida con otra lectura —el modelo lee distinto, o alguien
    corrige un campo decisivo—, lo que esa persona miró ya no es lo que hay, y
    la aprobación deja de contar: el parte vuelve a `pendiente` y hay que
    volver a mirarlo. Es lo que ya protegía R19 de F-028, y F-030 no lo afloja.

    Sin este caso, el de arriba podría estar pasando porque la huella no se
    compara en absoluto, que sería mucho peor que el defecto que se arregla.
    """
    guardado = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    aprobacion = _aprobacion_de_una_persona(guardado)
    base = _base_con_lo_guardado(guardado, decision=aprobacion)

    # El parte se vuelve a procesar y esta vez se lee otra cosa: la firma es
    # una marca y no hay observaciones, así que el destino pasa a ser otro.
    revalidado = _veredicto_guardado(Destino.REVISION_MANUAL)
    otra_extraccion, _ = _material(Destino.REVISION_MANUAL)
    base.guardar_parte(
        parte=_parte_troceado(),
        extraccion=otra_extraccion,
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    base.guardar_validacion(resultado=revalidado, ahora=AHORA)

    ctx = _contexto_para(puerta, veredicto=guardado.veredicto, destino=guardado.destino)
    dobles = _dobles()

    with pytest.raises(ParteNoApto) as fallo:
        puerta(ctx, base, dobles, commit=False)

    assert "este parte está pendiente" in str(fallo.value)
    assert Destino.REVISION_MANUAL.value in str(fallo.value)
    _nada_ha_salido(dobles)


def test_f030_r12_la_huella_apuntada_deja_de_coincidir_cuando_cambia_el_veredicto():
    """R12 · el porqué del caso de arriba, medido y no contado.

    Lo que hace que la aprobación caduque es una comparación de huellas, no un
    efecto lateral de los dobles. Aquí se ve: la apuntada es la del veredicto
    de la cola y la que se recompone después es la de `revision_manual`, y son
    distintas. Si alguien tocara `_normalizar` o `huella_de_veredicto` (R13),
    este caso y el de R11 se contradirían y habría que parar.
    """
    de_la_cola = _veredicto_guardado(Destino.COLA_VALIDACION_HUMANA)
    revisado = _veredicto_guardado(Destino.REVISION_MANUAL)

    base = _base_con_lo_guardado(de_la_cola)
    antes = base.consultar_situacion(hash_parte=HASH).validacion

    otra_extraccion, _ = _material(Destino.REVISION_MANUAL)
    base.guardar_parte(
        parte=_parte_troceado(),
        extraccion=otra_extraccion,
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    base.guardar_validacion(resultado=revisado, ahora=AHORA)
    despues = base.consultar_situacion(hash_parte=HASH).validacion

    assert huella_de_veredicto(antes) == huella_de_veredicto(de_la_cola)
    assert huella_de_veredicto(despues) == huella_de_veredicto(revisado)
    assert huella_de_veredicto(antes) != huella_de_veredicto(despues)


# --------------------------------------------------------------------------
# T17 · en esta feature no hay DDL (R20)
# --------------------------------------------------------------------------
#
# La regla dura 2 de `tasks.md` dice que aquí no se toca ni un fichero de
# `infrastructure/persistencia/sql/`, y el motivo no es de estilo: el DDL se
# aplica contra `psql-albaranes-rs9k2`, que es un PostgreSQL **compartido** con
# albaranes y compañía, y una columna nueva en una tabla de este esquema es una
# migración que hay que aplicar, revertir y explicar.
#
# La decisión D3 del humano fue explícita —«sin columna nueva»— y `design.md`
# §2 la sostiene midiendo que la huella se puede recomponer con lo que ya hay
# guardado. Este control es lo que impide que esa decisión se deshaga en un
# commit distraído.
#
# Van **dos** comprobaciones y no una, porque miran cosas distintas y fallan en
# sitios distintos: la del diff mira lo que ha cambiado esta rama y depende de
# que `dev` esté a mano; la de los nombres mira lo que hay en el árbol y no
# depende de nada.

#: La raíz del repositorio, subiendo desde este fichero.
RAIZ = Path(__file__).resolve().parents[3]

#: La carpeta del DDL, la que esta feature no puede tocar.
CARPETA_DDL = "services/postventa-api/infrastructure/persistencia/sql/"

#: Los once ficheros de DDL que dejó F-028, **y ninguno más**.
#:
#: Escritos a mano y no leídos del disco a propósito: una lista que se
#: recalculara del propio árbol daría verde ante cualquier fichero nuevo, que
#: es justo lo que viene a cazar.
DDL_DE_F028 = (
    "01_esquema.sql",
    "02_remesas.sql",
    "03_partes.sql",
    "04_validaciones.sql",
    "05_archivos.sql",
    "06_cierres.sql",
    "07_preferencias.sql",
    "08_usuarios_sigrid.sql",
    "09_graficos.sql",
    "10_aprobaciones.sql",
    "11_historico_estado.sql",
)


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only dev...HEAD`, o `None` si no se puede preguntar.

    No abre ningún socket —`git` es local— y no escribe nada: es una lectura
    del repositorio de trabajo. Devuelve `None` cuando no hay `git` a mano o
    cuando la rama `dev` no está en este clon, que es lo que pasa en un
    `checkout` superficial: eso no es un fallo de la feature y no puede poner
    la suite en rojo.
    """
    try:
        dev = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "dev"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
        if dev.returncode != 0:
            return None
        diff = subprocess.run(
            ["git", "diff", "--name-only", "dev...HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None
    if diff.returncode != 0:  # pragma: no cover - el repositorio no está sano
        return None
    return [linea.strip() for linea in diff.stdout.splitlines() if linea.strip()]


def test_f030_r20_el_diff_de_la_rama_no_toca_ni_un_fichero_de_ddl():
    """R20 · **sin columna nueva y sin migración** (D3), comprobado en el diff.

    Es la comprobación que el humano puede repetir a mano con el mismo comando,
    y por eso se usa `dev...HEAD` y no `dev..HEAD`: lo que interesa es lo que ha
    cambiado **esta rama** desde que se separó, no lo que haya pasado en `dev`
    mientras tanto.
    """
    cambiados = _ficheros_cambiados_en_la_rama()
    if cambiados is None:  # pragma: no cover - depende del clon, no del código
        pytest.skip("no hay 'git' o la rama 'dev' no está en este clon")

    culpables = [ruta for ruta in cambiados if CARPETA_DDL in ruta.replace("\\", "/")]

    assert culpables == [], (
        "esta feature no puede traer DDL: se aplica contra un PostgreSQL "
        f"compartido y la decisión D3 fue «sin columna nueva». Sobran: {culpables}"
    )


def test_f030_r20_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control del control: si el diff viniera vacío, el de arriba mentiría.

    Un `git diff` que no devolviera nada —rama equivocada, `dev` que ya
    contiene todo esto— pondría verde el caso anterior sin haber comprobado
    nada. Aquí se exige que la rama haya cambiado algo y que entre lo cambiado
    esté el módulo del que va la feature.
    """
    cambiados = _ficheros_cambiados_en_la_rama()
    if cambiados is None:  # pragma: no cover - depende del clon, no del código
        pytest.skip("no hay 'git' o la rama 'dev' no está en este clon")

    normalizados = [ruta.replace("\\", "/") for ruta in cambiados]

    assert normalizados, "el diff de la rama no puede estar vacío"
    assert any(
        ruta.endswith("application/pipelines/puerta_de_estado.py")
        for ruta in normalizados
    ), "la rama tiene que haber tocado la puerta: es de lo que va la feature"


def test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo():
    """R20 · la mitad que no depende de `git`, y por eso no se puede saltar.

    Si `dev` no estuviera a mano, el control de arriba se salta y la feature se
    quedaría sin vigilancia justo en la regla más cara de deshacer. Este mira el
    árbol: los ficheros de DDL son los once de F-028 y ninguno más.
    """
    carpeta = RAIZ / CARPETA_DDL
    nombres = tuple(sorted(ruta.name for ruta in carpeta.glob("*.sql")))

    assert nombres == DDL_DE_F028


# --------------------------------------------------------------------------
# T19 · la precisión del 2026-09-16 en `docs/ARCHITECTURE.md` (R25)
# --------------------------------------------------------------------------
#
# `ARCHITECTURE.md` es lo primero que lee quien llega al proyecto y es contra lo
# que valida el reviewer. Mientras el punto 3 de «Semántica de dominio
# imprescindible» siga diciendo solo lo de F-028 —«lo que decide es su
# estado»—, calla lo que ha costado esta regresión: **de dónde sale el
# veredicto del que ese estado se deriva**, y que los tres endpoints del
# circuito no emiten ninguno.
#
# Se sigue la regla del proyecto: lo anterior **no se borra**, se enmienda con
# una precisión fechada. Por eso van dos casos y no uno.

#: El punto 3 va de su título al del punto 4, igual que en
#: `test_f028_documentacion.py`: si alguien renumera el documento, los dos
#: ficheros se enteran a la vez.
PUNTO_3_ABRE = "3. **La firma debe ser humana.**"
PUNTO_3_CIERRA = "4. **Lo manuscrito es dato de primera"


def _punto_3_de_la_semantica() -> str:
    """El punto 3 de la semántica de dominio, aplanado a una línea.

    Se aplana para que las comprobaciones no dependan de dónde parta las líneas
    el que escriba: lo que se vigila es **lo que dice**, no cómo está
    maquetado.
    """
    texto = (
        Path(__file__).resolve().parents[3] / "docs" / "ARCHITECTURE.md"
    ).read_text(encoding="utf-8")

    assert PUNTO_3_ABRE in texto, "el punto 3 de la semántica ha cambiado de título"
    desde = texto.index(PUNTO_3_ABRE)
    assert PUNTO_3_CIERRA in texto[desde:], "no se encuentra el punto 4 tras el 3"
    hasta = texto.index(PUNTO_3_CIERRA, desde)
    return _llano(texto[desde:hasta])


def test_f030_r25_el_punto_3_dice_de_donde_sale_el_veredicto():
    """R25 · la precisión de F-030, fechada y bajo el punto que enmienda.

    Tres cosas y las tres hacen falta: que el estado se deriva del veredicto
    **guardado**, que ningún endpoint del circuito lo emite, y la fecha. Sin la
    fecha no se puede juzgar la decisión, porque no se sabe qué se sabía cuando
    se tomó.
    """
    punto = _punto_3_de_la_semantica()

    assert "Precisado por F-030 el 2026-09-16" in punto
    assert "veredicto que consta guardado" in punto
    assert "postventa.validaciones" in punto
    assert "Ningún endpoint del circuito" in punto
    assert "emite veredicto" in punto


def test_f030_r25_el_punto_3_conserva_las_dos_capas_anteriores():
    """R25 · **control negativo**: enmendar no es borrar lo de antes.

    El punto 3 acumula ya tres capas y las tres siguen haciendo falta: la regla
    general —una firma que no es humana no es conformidad— rige el 95 % de los
    partes, la de F-026 explica por qué un no apto puede archivarse y la de
    F-028, por qué un apto puede no archivarse. Quitar cualquiera para «dejarlo
    limpio» deja el documento describiendo la excepción como si fuera la norma.
    """
    punto = _punto_3_de_la_semantica()

    assert "Un parte sin firma válida no se archiva ni se cierra" in punto
    assert "Precisado por F-026 el 2026-09-12" in punto
    assert "salvo aprobación humana registrada" in punto
    assert "Precisado por F-028 el 2026-09-16" in punto
    assert "está `aprobado`" in punto
