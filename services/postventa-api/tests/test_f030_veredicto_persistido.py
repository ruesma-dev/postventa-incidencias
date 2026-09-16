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

from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
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

# Se importa el **módulo** y no la función: `fila_a_validacion_y_cierre` es de
# T4 y todavía no existe, y un `from ... import` dejaría en rojo el fichero
# entero —incluidos los casos de T1, que fallan por su propio motivo y no por
# un import—. Así el rojo de T2 es suyo y se lee solo.
from infrastructure.persistencia import mapeo

from tests.utiles_pg import RepositorioEnMemoria
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
