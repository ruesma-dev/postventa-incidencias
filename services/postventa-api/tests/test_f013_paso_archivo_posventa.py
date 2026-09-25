# services/postventa-api/tests/test_f013_paso_archivo_posventa.py
"""F-013 T10 · el paso de archivo con el resolutor de Posventa (`design.md` §5).

Cubre R4, R5, R15, R18, R20–R22, R40, R45 y R47 de
`specs/F-013-archivo-posventa/requirements.md` sobre **el paso**, con dobles.

## El orden es el requisito, y se afirma con el registro entero

`design.md` §5 enmendado fija el orden del paso con el resolutor:

    puerta → cotejo (1 bis) → nombre → L1 → **resolver** → aviso del intento
    anterior → traza previa → **crear carpetas** → buscar → subir → traza final

Nada de eso se ve mirando solo el resultado. Todos los dobles de este fichero
—repositorio, archivador, explorador y ubicaciones— y el **log** del paso
apuntan en **una misma lista** (`registro`), y los casos comparan la lista
**entera**: mover cualquier puerta un paso respecto de cualquier colaborador
pone un caso en rojo (`.claude/agents/reviewer.md`, punto 7).

## Un archivador que también es explorador

La firma del paso gana **un** parámetro, `resolver_destino` (T10 bis). Las
carpetas las crea el paso con el **mismo** archivador, que en `posventa` es el
adaptador de Graph y implementa los dos puertos (`design.md` §3.2: «la fábrica
devuelve la misma instancia y el borde la pasa por los dos lados»). Aquí eso es
`ArchivadorDePosventaFalso`: el `ArchivoPortFalso` de F-006 más el
`ExploradorFalso` de T8, con el mismo registro. El resolutor recibe **esa
misma instancia** como explorador, como hará el borde (T13).

Los símbolos nuevos del paso se consultan **por atributo** (`paso.X`) y no con
`from … import`: mientras no existan, cada caso falla por su cuenta.

Sin red, sin Graph y sin Sigrid; ni un dato real (bibliotecas inventadas y
reconocibles, el árbol medido de la 0677 sin nombres de persona).
"""

from __future__ import annotations

import dataclasses
import functools
import inspect
import logging
from datetime import UTC, datetime

import application.pipelines.paso_archivo as paso
import pytest
from application.pipelines.codigos_del_parte import CodigosDelParte
from application.pipelines.destino_archivo import resolver_destino_posventa
from domain.models.destino_posventa import MotivoDestino
from domain.models.errores import (
    ArchivoFallido,
    CodigosNoCoinciden,
    ConfiguracionSigridIncompleta,
    DestinoNoResuelto,
    NombradoImposible,
    ParteNoApto,
    ReferenciaNoConsta,
)
from domain.models.estado import SituacionParte
from domain.models.nombrado import nombre_de_archivo
from domain.models.persistencia import EstadoArchivo, ResultadoGuardado, TrazaArchivo
from domain.ports.archivo import ArchivoPort
from domain.ports.biblioteca import ExploradorBibliotecaPort

from tests.utiles_destino import (
    ALTERNATIVA,
    CARPETA_OBRA_0677,
    FICHEROS_SUELTOS_VILLA_04,
    FIRMADOS,
    INCIDENCIAS,
    RAIZ_0677,
    RES_OBRA_0677,
    ExploradorFalso,
    UbicacionesFalsas,
    arbol_0677,
    reclamacion_0677,
    ubicacion_0677,
    ubicaciones_0677,
)
from tests.utiles_sharepoint import (
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    contexto_no_apto,
    preexistente,
)
from tests.utiles_validacion import HASH_DE_PRUEBA, extraccion_de_ejemplo

AHORA = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)
ARCHIVADO_EN = datetime(2026, 9, 1, 9, 30, tzinfo=UTC)

#: Bibliotecas **inventadas** y reconocibles: si aparecen en un log o en un
#: aviso, el caso lo ve.
DRIVE_IT = "drive-inventado-it"
DRIVE_POSVENTA = "drive-inventado-posventa"

OBRA = CARPETA_OBRA_0677
INC = f"{OBRA}/{INCIDENCIAS}"
OBRA_NUEVA = f"0677 {RES_OBRA_0677}"

#: Lo que apuntan en el registro los dobles de F-019 (`utiles_sharepoint.py`).
TRAZA_PREVIA = "repositorio.guardar_archivo(pendiente)"
TRAZA_FINAL = "repositorio.guardar_archivo(archivado)"
TRAZA_ERROR = "repositorio.guardar_archivo(error)"
BUSCAR = "archivador.buscar"
SUBIR = "archivador.subir"

#: El prefijo de R40, literal.
LOG_CARPETA_CREADA = "F-013 carpeta creada: "

LOGGER_DEL_PASO = "application.pipelines.paso_archivo"


# --------------------------------------------------------------------------
# Material
# --------------------------------------------------------------------------


def _villa(n: int) -> str:
    return f"{INC}/VILLA {n:02d}"


def _hoja(n: int, hoja: str = FIRMADOS) -> str:
    return f"{_villa(n)}/{hoja}"


def _nombre(n: int) -> str:
    """El nombre del fichero de la reclamación de la villa `n` (R5)."""
    return nombre_de_archivo(codigo_obra="0677", numero_incidencia=reclamacion_0677(n))


def _listar(ruta: str) -> str:
    return f"explorador.listar_carpetas:{ruta}"


def _crear(padre: str, nombre: str) -> str:
    return f"explorador.crear_subcarpeta:{padre}|{nombre}"


def _sigrid(n: int) -> list[str]:
    """Las dos lecturas de Sigrid del resolutor, en su orden."""
    return [
        f"ubicaciones.leer_ubicacion:{reclamacion_0677(n)}",
        "ubicaciones.leer_unidades_del_numero:0677",
    ]


#: Los tres listados hasta el de las unidades, que son los mismos para todas.
LISTADOS_HASTA_LA_UNIDAD = [_listar(""), _listar(OBRA), _listar(INC)]


class ArchivadorDePosventaFalso(ArchivoPortFalso):
    """`ArchivoPort` **y** `ExploradorBibliotecaPort` en una sola instancia.

    Es lo que será el adaptador de Graph en `posventa` (`design.md` §3.2): la
    subida va a la `BibliotecaFalsa` de F-006 y las carpetas al
    `ExploradorFalso` de T8, y los dos apuntan en el **mismo** registro.
    """

    def __init__(self, explorador: ExploradorFalso, **extra) -> None:
        super().__init__(registro=explorador.registro, **extra)
        self.explorador = explorador

    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        return self.explorador.listar_carpetas(carpeta=carpeta)

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        self.explorador.crear_subcarpeta(padre=padre, nombre=nombre)


class _AlRegistro(logging.Handler):
    """Apunta cada línea de log del paso en el registro compartido."""

    def __init__(self, registro: list[str]) -> None:
        super().__init__(level=logging.DEBUG)
        self.registro = registro

    def emit(self, record: logging.LogRecord) -> None:
        self.registro.append(f"log:{record.getMessage()}")


@dataclasses.dataclass
class Montaje:
    ctx: object
    registro: list[str]
    explorador: ExploradorFalso
    archivador: ArchivadorDePosventaFalso
    ubicaciones: UbicacionesFalsas
    repositorio: RepositorioFalso
    resolutor: object
    #: Los argumentos con los que el paso llamó al resolutor, en orden.
    resoluciones: list[dict]

    def archivar(self, **extra):
        return paso.paso_archivo(
            self.ctx,
            self.archivador,
            self.repositorio,
            carpeta_base="",
            ahora=AHORA,
            resolver_destino=self.resolutor,
            **extra,
        )

    @property
    def log(self) -> list[str]:
        return [linea for linea in self.registro if linea.startswith("log:")]


@pytest.fixture
def montar(request):
    """Monta el paso con la 0677 medida; quita el handler de log al acabar."""
    handlers: list[logging.Handler] = []
    logger = logging.getLogger(LOGGER_DEL_PASO)
    nivel = logger.level

    def _montar(
        n: int = 5,
        *,
        archivo: TrazaArchivo | None = None,
        arbol=None,
        crear_carpetas: bool = True,
        ctx=None,
        explorador_cls=ExploradorFalso,
        repositorio_cls=RepositorioFalso,
        ubicaciones: UbicacionesFalsas | None = None,
        **repo_extra,
    ) -> Montaje:
        registro: list[str] = []
        explorador = explorador_cls(
            arbol if arbol is not None else arbol_0677(),
            ficheros={_villa(4): FICHEROS_SUELTOS_VILLA_04},
            registro=registro,
        )
        archivador = ArchivadorDePosventaFalso(explorador)
        if ubicaciones is None:
            ubicaciones = ubicaciones_0677(registro=registro)
        else:
            ubicaciones.registro = registro
        ctx = ctx if ctx is not None else contexto_apto(numero_incidencia=reclamacion_0677(n))
        repositorio = repositorio_cls(
            registro=registro,
            situacion=SituacionParte(validacion=ctx.validacion, archivo=archivo),
            **repo_extra,
        )
        resolutor = functools.partial(
            resolver_destino_posventa,
            explorador=archivador,
            ubicaciones=ubicaciones,
            base="",
            incidencias=INCIDENCIAS,
            firmados=FIRMADOS,
            firmados_alternativa=ALTERNATIVA,
            crear_carpetas=crear_carpetas,
        )
        resoluciones: list[dict] = []

        def espia(**argumentos):
            resoluciones.append(argumentos)
            return resolutor(**argumentos)

        handler = _AlRegistro(registro)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        handlers.append(handler)
        return Montaje(
            ctx, registro, explorador, archivador, ubicaciones, repositorio, espia, resoluciones
        )

    yield _montar
    for handler in handlers:
        logger.removeHandler(handler)
    logger.setLevel(nivel)


def _traza(**cambios) -> TrazaArchivo:
    valores = {
        "hash_parte": HASH_DE_PRUEBA,
        "estado": EstadoArchivo.ARCHIVADO,
        "nombre_fichero": _nombre(5),
        "carpeta": _hoja(5),
        "drive_id": DRIVE_POSVENTA,
        "item_id": "item-guardado-f013",
        "web_url": "https://ejemplo.invalido/centinela-f013",
        "archivado_at_utc": ARCHIVADO_EN,
    }
    valores.update(cambios)
    return TrazaArchivo(**valores)


def _pendiente(carpeta: str, nombre: str, **cambios) -> TrazaArchivo:
    return TrazaArchivo(
        hash_parte=cambios.pop("hash_parte", HASH_DE_PRUEBA),
        estado=cambios.pop("estado", EstadoArchivo.PENDIENTE),
        nombre_fichero=nombre,
        carpeta=carpeta,
        **cambios,
    )


def _aviso_creada(ruta: str) -> str:
    return paso.AVISO_CARPETA_CREADA.format(ruta=ruta)


def _sin_crear(m: Montaje) -> None:
    assert m.explorador.creaciones == []
    assert m.explorador.carpetas_nuevas == []


# ==========================================================================
# La firma (T10 bis) y la composición
# ==========================================================================


def test_f013_t10_resolver_destino_es_opcional_y_por_palabra_clave():
    """R2 · sin él, el paso es el de hoy; con él, solo por nombre."""
    parametro = inspect.signature(paso.paso_archivo).parameters["resolver_destino"]

    assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
    assert parametro.default is None


def test_f013_t10_el_archivador_de_prueba_cumple_los_dos_puertos():
    """El doble es lo que el borde pasará: una instancia con los dos puertos."""
    archivador = ArchivadorDePosventaFalso(ExploradorFalso())

    assert isinstance(archivador, ArchivoPort)
    assert isinstance(archivador, ExploradorBibliotecaPort)


def test_f013_t10_con_resolutor_y_un_archivador_que_no_crea_carpetas_no_se_toca_nada(montar):
    """Composición rota: el resolutor sin un archivador que sepa crear carpetas.

    Es un error de programación del borde, no del parte, y sale **antes de
    nada**: ni la puerta, ni Sigrid, ni la biblioteca, ni una traza. El
    repositorio de este caso apunta también **la lectura** de la puerta, que
    los dobles de F-019 no apuntan.
    """
    m = montar(5, repositorio_cls=_RepositorioQueApuntaLaLectura)
    solo_archivo = ArchivoPortFalso(registro=m.registro)

    with pytest.raises(TypeError, match="crear_subcarpeta"):
        paso.paso_archivo(
            m.ctx, solo_archivo, m.repositorio, carpeta_base="", ahora=AHORA,
            resolver_destino=m.resolutor,
        )

    assert m.registro == []
    assert m.resoluciones == []


def test_f013_t10_el_repositorio_que_apunta_la_lectura_la_apunta(montar):
    """El control del control: sin el `TypeError`, la puerta sí se vería."""
    m = montar(5, repositorio_cls=_RepositorioQueApuntaLaLectura)

    m.archivar()

    assert m.registro[0] == "repositorio.consultar_situacion"


class _RepositorioQueApuntaLaLectura(RepositorioFalso):
    """`RepositorioFalso` que apunta también `consultar_situacion` en el registro."""

    def consultar_situacion(self, *, hash_parte: str) -> SituacionParte:
        self.registro.append("repositorio.consultar_situacion")
        return super().consultar_situacion(hash_parte=hash_parte)


# ==========================================================================
# R4, R5 · la ruta de Posventa, con los nombres tal y como existen
# ==========================================================================


def test_f013_r4_archiva_en_la_hoja_de_su_unidad_con_el_orden_entero(montar):
    """R4, R21, R22 · villa 5, todo existe: el orden de §5, llamada a llamada."""
    m = montar(5)

    ctx = m.archivar()

    assert m.registro == [
        *_sigrid(5),
        *LISTADOS_HASTA_LA_UNIDAD,
        _listar(_villa(5)),
        TRAZA_PREVIA,
        BUSCAR,
        SUBIR,
        TRAZA_FINAL,
    ]
    assert m.archivador.llamadas[-1] == (
        "subir",
        {"carpeta": _hoja(5), "nombre": _nombre(5), "bytes": len(ctx.parte.contenido),
         "mime": paso.MIME_PDF},
    )
    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert ctx.archivo.carpeta == _hoja(5)
    assert ctx.avisos == []
    _sin_crear(m)


def test_f013_r4_la_carpeta_de_obra_va_tal_y_como_existe(montar):
    """R4 · `677  MIRASIERRA`, con sus dos blancos, no `0677`."""
    m = montar(3)

    ctx = m.archivar()

    assert ctx.archivo.carpeta == f"677  MIRASIERRA/PARTES INCIDENCIAS/VILLA 03/{FIRMADOS}"


def test_f013_r4_la_hoja_alternativa_de_villa_02_se_usa_con_su_nombre(montar):
    """R4, R49 · VILLA 02 tiene `PARTES FIRMADO`: se archiva ahí, sin crear."""
    m = montar(2)

    ctx = m.archivar()

    assert ctx.archivo.carpeta == _hoja(2, ALTERNATIVA)
    _sin_crear(m)


def test_f013_r5_el_nombre_es_el_de_nombrado_y_el_resolutor_lo_recibe_hecho(montar):
    """R5 · el nombre no cambia con la estrategia: `nombre_de_archivo` tal cual."""
    m = montar(5)

    ctx = m.archivar()

    assert ctx.archivo.nombre_fichero == _nombre(5)
    assert m.resoluciones == [
        {
            "codigo_obra": "0677",
            "numero_incidencia": reclamacion_0677(5),
            "nombre_fichero": _nombre(5),
        }
    ]


def test_f013_r5_sin_codigos_guardados_no_hay_nombre_y_no_se_llama_a_nadie(montar):
    """R5 · `NombradoImposible` sale antes de L1 y antes de resolver."""
    ctx = contexto_apto(numero_incidencia=reclamacion_0677(5))
    ctx.validacion = dataclasses.replace(ctx.validacion, numero_incidencia="")
    m = montar(5, ctx=ctx)

    with pytest.raises(NombradoImposible):
        m.archivar()

    assert m.registro == []
    assert m.resoluciones == []


# ==========================================================================
# R15, R40 · crear: después de la traza previa, en orden, un nivel por llamada
# ==========================================================================


def test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden(montar):
    """R15, R34, R40 · villa 8: `VILLA 08` y su hoja, después de `pendiente`."""
    m = montar(8)

    ctx = m.archivar()

    assert m.registro == [
        *_sigrid(8),
        *LISTADOS_HASTA_LA_UNIDAD,
        TRAZA_PREVIA,
        _crear(INC, "VILLA 08"),
        f"log:{LOG_CARPETA_CREADA}{_villa(8)}",
        _crear(_villa(8), FIRMADOS),
        f"log:{LOG_CARPETA_CREADA}{_hoja(8)}",
        BUSCAR,
        SUBIR,
        TRAZA_FINAL,
    ]
    assert m.explorador.carpetas_nuevas == [_villa(8), _hoja(8)]
    assert ctx.archivo.carpeta == _hoja(8)
    assert ctx.avisos == [_aviso_creada(_villa(8)), _aviso_creada(_hoja(8))]


def test_f013_r15_sin_ninguna_carpeta_se_crean_los_cuatro_niveles_uno_a_uno(montar):
    """R15, R36 · la obra no existe: cuatro creaciones, cada una en su padre."""
    arbol = arbol_0677()
    arbol[""] = tuple(nombre for nombre in RAIZ_0677 if nombre != OBRA)
    m = montar(5, arbol={"": arbol[""]})

    ctx = m.archivar()

    nueva_inc = f"{OBRA_NUEVA}/{INCIDENCIAS}"
    creaciones = [
        ("", OBRA_NUEVA),
        (OBRA_NUEVA, INCIDENCIAS),
        (nueva_inc, "VILLA 05"),
        (f"{nueva_inc}/VILLA 05", FIRMADOS),
    ]
    assert m.explorador.creaciones == creaciones
    assert all("/" not in nombre for _, nombre in creaciones)
    assert m.registro[: len(_sigrid(5)) + 2] == [*_sigrid(5), _listar(""), TRAZA_PREVIA]
    assert ctx.archivo.carpeta == f"{nueva_inc}/VILLA 05/{FIRMADOS}"
    rutas = [OBRA_NUEVA, nueva_inc, f"{nueva_inc}/VILLA 05", f"{nueva_inc}/VILLA 05/{FIRMADOS}"]
    assert ctx.avisos == [_aviso_creada(ruta) for ruta in rutas]
    assert m.log == [f"log:{LOG_CARPETA_CREADA}{ruta}" for ruta in rutas]


def test_f013_r15_en_posventa_nunca_se_llama_a_asegurar_carpeta(montar):
    """R15 · `asegurar_carpeta` crea intermedias a ciegas: en `posventa`, jamás."""
    m = montar(8)

    m.archivar()

    assert "asegurar_carpeta" not in m.archivador.operaciones
    assert "archivador.asegurar_carpeta" not in m.registro


def test_f013_r48_villa_04_gana_su_hoja_y_sus_ficheros_sueltos_siguen(montar):
    """R48 · solo se crea `PARTES FIRMADOS`; los 142 sueltos, intactos."""
    m = montar(4)

    ctx = m.archivar()

    assert m.explorador.creaciones == [(_villa(4), FIRMADOS)]
    assert m.explorador.ficheros_en(_villa(4)) == FICHEROS_SUELTOS_VILLA_04
    assert ctx.archivo.carpeta == _hoja(4)
    assert ctx.avisos == [_aviso_creada(_hoja(4))]


def test_f013_r40_el_aviso_de_carpeta_creada_lleva_la_ruta_y_ningun_identificador():
    """R40, R23 · la ruta sí; biblioteca, elemento o URL, no."""
    aviso = paso.AVISO_CARPETA_CREADA

    assert "{ruta}" in aviso
    assert "drive" not in aviso.lower()
    assert "http" not in aviso.lower()
    assert "Posventa" in aviso


def test_f013_r40_sin_creaciones_no_hay_aviso_ni_log_de_carpeta(montar):
    """R40 · el aviso sale **solo** cuando de verdad se crea algo."""
    m = montar(6)

    ctx = m.archivar()

    assert ctx.avisos == []
    assert m.log == []


def test_f013_r40_el_log_de_carpeta_creada_es_un_aviso_del_logger_del_paso(montar, caplog):
    """R40 · la línea literal, en el logger del paso y con nivel de aviso."""
    m = montar(8)

    with caplog.at_level(logging.INFO, logger=LOGGER_DEL_PASO):
        m.archivar()

    creadas = [r for r in caplog.records if r.getMessage().startswith(LOG_CARPETA_CREADA)]
    assert [r.getMessage() for r in creadas] == [
        f"{LOG_CARPETA_CREADA}{_villa(8)}",
        f"{LOG_CARPETA_CREADA}{_hoja(8)}",
    ]
    assert all(r.levelno == logging.WARNING for r in creadas)
    assert all(r.name == LOGGER_DEL_PASO for r in creadas)


# ==========================================================================
# R18 · destino no resuelto: traza `error` con el código, y nada más
# ==========================================================================


def test_f013_r18_sin_destino_queda_la_traza_error_con_el_codigo_y_no_se_sube(montar):
    """R16, R18 · crear apagado y la villa 8 no existe: `sin_carpeta_unidad`."""
    m = montar(8, crear_carpetas=False)

    with pytest.raises(DestinoNoResuelto) as error:
        m.archivar()

    assert error.value.motivo == MotivoDestino.SIN_CARPETA_UNIDAD
    assert m.registro == [*_sigrid(8), *LISTADOS_HASTA_LA_UNIDAD, TRAZA_ERROR]
    assert m.repositorio.archivos == [
        TrazaArchivo(
            hash_parte=HASH_DE_PRUEBA,
            estado=EstadoArchivo.ERROR,
            nombre_fichero=_nombre(8),
            carpeta=None,
            motivo="sin_carpeta_unidad",
        )
    ]
    assert type(m.repositorio.ultima_traza.motivo) is str
    assert m.ctx.archivo == m.repositorio.ultima_traza
    assert m.archivador.operaciones == []
    _sin_crear(m)


def test_f013_r18_una_parecida_para_antes_de_crear_nada(montar):
    """R18, R35 · la carpeta de la villa 5 renombrada a `VILLA5`: parecida.

    Ni casa ni se crea otra al lado. Traza `error` con `unidad_parecida`, sin
    crear nada.
    """
    arbol = arbol_0677()
    arbol[INC] = tuple("VILLA5" if v == "VILLA 05" else v for v in arbol[INC])
    del arbol[_villa(5)]
    m = montar(5, arbol=arbol)

    with pytest.raises(DestinoNoResuelto) as error:
        m.archivar()

    assert error.value.motivo == MotivoDestino.UNIDAD_PARECIDA
    assert m.repositorio.estados == ["error"]
    assert m.repositorio.ultima_traza.motivo == "unidad_parecida"
    assert m.registro[-1] == TRAZA_ERROR
    _sin_crear(m)


def test_f013_r18_la_traza_error_no_lleva_nombres_de_la_ficha_ni_de_sigrid(montar):
    """R18, R23 · el motivo es un código: ni `con.res` ni el texto del 409."""
    ubicaciones = UbicacionesFalsas(
        {reclamacion_0677(5): (dataclasses.replace(ubicacion_0677(5), obra_codigo="0678"),)},
    )
    m = montar(5, ubicaciones=ubicaciones)

    with pytest.raises(DestinoNoResuelto) as error:
        m.archivar()

    motivo = m.repositorio.ultima_traza.motivo
    assert motivo == "obra_no_coincide" == error.value.motivo
    assert error.value.detalle not in motivo
    assert "VIVIENDAS" not in motivo
    assert m.registro == [f"ubicaciones.leer_ubicacion:{reclamacion_0677(5)}", TRAZA_ERROR]


def test_f013_r18_la_traza_error_que_no_se_aplica_se_registra_y_sube_el_409(montar, caplog):
    """F-033 R19 en este camino: `SIN_CAMBIOS` en la traza `error` no es fallo."""
    m = montar(8, crear_carpetas=False, resultados={1: ResultadoGuardado.SIN_CAMBIOS})

    with (
        caplog.at_level(logging.WARNING, logger=LOGGER_DEL_PASO),
        pytest.raises(DestinoNoResuelto),
    ):
        m.archivar()

    assert any("no se aplicó" in r.getMessage() for r in caplog.records)


# ==========================================================================
# R20 · se reintenta sin tocar la base
# ==========================================================================


def test_f013_r20_tras_crear_la_carpeta_a_mano_el_reintento_archiva(montar):
    """R20 · la traza `error` no corta: Posventa crea `VILLA 08` y se sube."""
    m = montar(8, crear_carpetas=False)
    with pytest.raises(DestinoNoResuelto):
        m.archivar()
    error = m.repositorio.ultima_traza
    m.explorador.crear_subcarpeta(padre=INC, nombre="VILLA 08")
    m.explorador.crear_subcarpeta(padre=_villa(8), nombre=FIRMADOS)
    m.repositorio.situacion = dataclasses.replace(m.repositorio.situacion, archivo=error)
    m.ctx.avisos.clear()

    ctx = m.archivar()

    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert ctx.archivo.carpeta == _hoja(8)
    assert m.repositorio.estados == ["error", "pendiente", "archivado"]
    assert len(m.resoluciones) == 2


# ==========================================================================
# R21 · las garantías de F-006 y F-019, también en `posventa`
# ==========================================================================


def test_f013_r21_el_homonimo_se_reemplaza_y_se_avisa(montar):
    """R21 · L2 sigue: el homónimo se pisa y `AVISO_REEMPLAZADO` sale."""
    m = montar(5)
    preexistente(
        m.archivador.biblioteca, carpeta=_hoja(5), nombre=_nombre(5),
        contenido=b"%PDF escaneo anterior",
    )

    ctx = m.archivar()

    assert ctx.avisos == [paso.AVISO_REEMPLAZADO]
    assert len(m.archivador.biblioteca.elementos) == 1


def test_f013_r21_si_falla_la_subida_queda_la_traza_error_con_la_carpeta_resuelta(montar):
    """R21 · como hoy: `ArchivoFallido` al subir → traza `error` y se relanza."""
    m = montar(5)
    m.archivador.fallo = ArchivoFallido("el proveedor devolvió 503")

    with pytest.raises(ArchivoFallido):
        m.archivar()

    assert m.repositorio.estados == ["pendiente", "error"]
    assert m.repositorio.ultima_traza.carpeta == _hoja(5)
    assert m.repositorio.ultima_traza.motivo == "el proveedor devolvió 503"


class _FallaAlCrearLaHoja(ExploradorFalso):
    """Crea la unidad y falla en la hoja: una creación a medias (R39)."""

    fallar = True

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        if self.fallar and nombre == FIRMADOS:
            self.registro.append(f"explorador.crear_subcarpeta:{padre}|{nombre}")
            self.creaciones.append((padre, nombre))
            raise ArchivoFallido("el proveedor devolvió 423: bloqueado")
        super().crear_subcarpeta(padre=padre, nombre=nombre)


def test_f013_r21_si_falla_una_creacion_no_se_sube_y_el_reintento_sigue_donde_quedo(montar):
    """R21, R39 · la hoja falla: traza `error`, sin subir; el reintento crea solo la hoja."""
    m = montar(8, explorador_cls=_FallaAlCrearLaHoja)

    with pytest.raises(ArchivoFallido):
        m.archivar()

    assert m.registro[-4:] == [
        _crear(INC, "VILLA 08"),
        f"log:{LOG_CARPETA_CREADA}{_villa(8)}",
        _crear(_villa(8), FIRMADOS),
        TRAZA_ERROR,
    ]
    assert m.repositorio.ultima_traza.carpeta == _hoja(8)
    assert m.repositorio.ultima_traza.motivo == "el proveedor devolvió 423: bloqueado"
    assert BUSCAR not in m.registro and SUBIR not in m.registro

    m.explorador.fallar = False
    m.repositorio.situacion = dataclasses.replace(
        m.repositorio.situacion, archivo=m.repositorio.ultima_traza
    )
    m.registro.clear()
    m.ctx.avisos.clear()

    ctx = m.archivar()

    assert _listar(_villa(8)) in m.registro
    assert [linea for linea in m.registro if linea.startswith("explorador.crear")] == [
        _crear(_villa(8), FIRMADOS)
    ]
    assert m.explorador.carpetas_nuevas == [_villa(8), _hoja(8)]
    assert ctx.archivo.carpeta == _hoja(8)


def test_f013_r21_si_la_traza_previa_no_se_puede_escribir_no_se_crea_ni_se_sube(montar):
    """R21, F-019 · la traza previa va antes de crear: si falla, nada."""
    m = montar(8, fallos={1: ReferenciaNoConsta("el parte no consta guardado")})

    with pytest.raises(ReferenciaNoConsta):
        m.archivar()

    assert m.registro[-1] == TRAZA_PREVIA
    _sin_crear(m)
    assert m.archivador.operaciones == []


class _RepositorioEnCarrera(RepositorioFalso):
    """F-033 R18: otra petición archiva el parte justo al escribir `pendiente`."""

    la_de_la_otra: TrazaArchivo | None = None

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        resultado = super().guardar_archivo(traza=traza)
        if self.llamadas_guardar_archivo == 1 and self.la_de_la_otra is not None:
            self.situacion = dataclasses.replace(self.situacion, archivo=self.la_de_la_otra)
        return resultado


def test_f013_r21_en_la_carrera_de_f033_no_se_crea_ni_se_sube(montar):
    """F-033 R18 · `SIN_CAMBIOS` en la previa: ni carpetas ni subida."""
    m = montar(
        8, repositorio_cls=_RepositorioEnCarrera,
        resultados={1: ResultadoGuardado.SIN_CAMBIOS},
    )
    m.repositorio.la_de_la_otra = _traza(nombre_fichero=_nombre(8), carpeta=_hoja(8))

    ctx = m.archivar()

    assert ctx.archivo == m.repositorio.la_de_la_otra
    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]
    assert m.registro[-1] == TRAZA_PREVIA
    _sin_crear(m)
    assert m.archivador.operaciones == []


# ==========================================================================
# R22 · resolver va después de puerta, cotejo, nombre y L1; con lo guardado
# ==========================================================================


def test_f013_r22_un_parte_no_aprobado_no_llega_a_sigrid_ni_a_la_biblioteca(montar):
    """R22 · la puerta de estado va antes de resolver."""
    m = montar(5, ctx=contexto_no_apto())

    with pytest.raises(ParteNoApto):
        m.archivar()

    assert m.registro == []
    assert m.resoluciones == []


def test_f013_r22_un_cuerpo_que_no_cuadra_no_llega_a_sigrid_ni_a_la_biblioteca(montar):
    """R22 · el cotejo de F-031 (1 bis) va antes de resolver."""
    m = montar(5)

    with pytest.raises(CodigosNoCoinciden):
        m.archivar(
            codigos_declarados=CodigosDelParte(
                codigo_obra="0677", numero_incidencia=reclamacion_0677(9)
            )
        )

    assert m.registro == []
    assert m.resoluciones == []


def test_f013_r22_se_resuelve_con_lo_guardado_y_nunca_con_la_extraccion(montar):
    """R22 · la extracción dice villa 9 de otra obra; lo guardado, villa 5."""
    ctx = contexto_apto(numero_incidencia=reclamacion_0677(5))
    ctx.extraccion = extraccion_de_ejemplo(
        hash_parte=HASH_DE_PRUEBA, codigo_obra="0999", numero_incidencia=reclamacion_0677(9)
    )
    m = montar(5, ctx=ctx)

    resultado = m.archivar(
        codigos_declarados=CodigosDelParte(
            codigo_obra="0677", numero_incidencia=reclamacion_0677(5)
        )
    )

    assert m.resoluciones == [
        {
            "codigo_obra": "0677",
            "numero_incidencia": reclamacion_0677(5),
            "nombre_fichero": _nombre(5),
        }
    ]
    assert resultado.archivo.carpeta == _hoja(5)


def test_f013_r22_se_resuelve_una_sola_vez_por_parte(montar):
    """R22 · una resolución por archivado: ni antes de L1 ni dos veces."""
    m = montar(8)

    m.archivar()

    assert len(m.resoluciones) == 1
    assert m.registro.count(_sigrid(8)[0]) == 1


def test_f013_r22_el_aviso_del_intento_anterior_compara_con_la_carpeta_resuelta(montar):
    """F-033 R20 · `pendiente` en la ruta de IT: aviso y log, tras resolver."""
    anterior = _pendiente("Postventa/0677", _nombre(5), drive_id=DRIVE_IT)
    m = montar(5, archivo=anterior)

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    aviso = paso.AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA.format(
        carpeta="Postventa/0677", nombre=_nombre(5)
    )
    assert ctx.avisos == [aviso]
    lineas = [linea for linea in m.registro if linea.startswith("log:")]
    assert len(lineas) == 1 and "carpeta=Postventa/0677" in lineas[0]
    assert m.registro == [
        *_sigrid(5),
        *LISTADOS_HASTA_LA_UNIDAD,
        _listar(_villa(5)),
        lineas[0],
        TRAZA_PREVIA,
        BUSCAR,
        SUBIR,
        TRAZA_FINAL,
    ]
    assert DRIVE_IT not in lineas[0]


def test_f013_r22_un_pendiente_en_la_misma_carpeta_resuelta_no_avisa(montar):
    """F-033 R20 · la misma ruta que la resuelta: nada que avisar."""
    m = montar(5, archivo=_pendiente(_hoja(5), _nombre(5)))

    ctx = m.archivar()

    assert ctx.avisos == []
    assert m.log == []


# ==========================================================================
# R45 · L1 corta antes de resolver: lo archivado (en IT o donde sea) no lee nada
# ==========================================================================


def test_f013_r45_un_parte_archivado_en_it_no_llama_ni_a_sigrid_ni_a_la_biblioteca(montar):
    """R25, R45 · IT: los dos avisos de F-033 y **cero** llamadas."""
    en_it = _traza(carpeta="Postventa/0677", drive_id=DRIVE_IT)
    m = montar(5, archivo=en_it)

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO, paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO]
    assert ctx.archivo == en_it
    assert m.registro == []
    assert m.resoluciones == []
    assert m.ubicaciones.llamadas == []
    assert m.explorador.llamadas == []


def test_f013_r45_archivado_en_posventa_con_otra_carpeta_no_avisa_de_otro_destino(montar):
    """R45 · la carpeta **no** se compara en L1: conocerla exigiría resolver."""
    renombrada = _traza(carpeta=f"{INC}/VILLA 5 (antigua)/{FIRMADOS}")
    m = montar(5, archivo=renombrada)

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]
    assert ctx.archivo == renombrada
    assert m.registro == []


def test_f013_r45_archivado_con_otro_nombre_si_avisa_de_otro_destino(montar):
    """R45 · el nombre sí se compara: se sabe sin resolver."""
    con_otro_nombre = _traza(nombre_fichero="0677 - RS26.08 - 5 PARTE FIRMADO.pdf")
    m = montar(5, archivo=con_otro_nombre)

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO, paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO]
    assert m.registro == []


def test_f013_r45_archivado_sin_carpeta_en_la_traza_tampoco_avisa_de_carpeta(montar):
    """R45 · una traza vieja sin carpeta: la carpeta no decide nada."""
    sin_carpeta = _traza(carpeta=None)
    m = montar(5, archivo=sin_carpeta)

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]


def test_f013_r45_el_archivado_de_otro_parte_no_corta(montar):
    """R45, F-033 R13 · la traza de otro `hash` no dice nada de este parte."""
    m = montar(5, archivo=_traza(hash_parte="hash-de-otro"))

    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert m.resoluciones != []
    assert SUBIR in m.registro


# ==========================================================================
# R41 · Sigrid o la biblioteca caídas: sube tal cual, sin traza colgada
# ==========================================================================


@pytest.mark.parametrize(
    "fallo",
    (ConfiguracionSigridIncompleta("faltan SIGRID_API_BASE_URL"), TimeoutError("sin respuesta")),
)
def test_f013_r41_sigrid_caida_sube_tal_cual_sin_trazas_ni_carpetas(montar, fallo):
    """R41 · ni traza `pendiente` colgada ni `error` con un motivo inventado."""
    m = montar(5, ubicaciones=ubicaciones_0677(fallo_al_ubicar=fallo))

    with pytest.raises(type(fallo)) as error:
        m.archivar()

    assert error.value is fallo
    assert m.registro == [f"ubicaciones.leer_ubicacion:{reclamacion_0677(5)}"]
    assert m.repositorio.archivos == []


def test_f013_r41_la_biblioteca_sin_la_base_sube_tal_cual_sin_trazas(montar):
    """Un `None` del listado es `ArchivoFallido` del resolutor: sin traza ni subida."""
    m = montar(5, arbol={"otra": ()})

    with pytest.raises(ArchivoFallido):
        m.archivar()

    assert m.registro == [*_sigrid(5), _listar("")]
    assert m.repositorio.archivos == []


# ==========================================================================
# R47 · destino no resuelto sobre un `pendiente`: el rastro, antes de pisarlo
# ==========================================================================


def test_f013_r47_el_intento_pendiente_queda_en_el_log_antes_de_la_traza_error(montar):
    """R47 · carpeta y nombre del intento anterior, antes del `error` que lo pisa."""
    anterior = _pendiente("Postventa/0677", _nombre(8), drive_id=DRIVE_IT)
    m = montar(8, archivo=anterior, crear_carpetas=False)

    with pytest.raises(DestinoNoResuelto):
        m.archivar(drive_id_vigente=DRIVE_POSVENTA)

    lineas = m.log
    assert len(lineas) == 1
    assert "carpeta=Postventa/0677" in lineas[0]
    assert f"fichero={_nombre(8)}" in lineas[0]
    assert "sin_carpeta_unidad" in lineas[0]
    assert DRIVE_IT not in lineas[0]
    assert m.registro[-2:] == [lineas[0], TRAZA_ERROR]


@pytest.mark.parametrize(
    "guardada",
    (
        None,
        _pendiente("Postventa/0677", "x.pdf", estado=EstadoArchivo.ERROR),
        _pendiente("Postventa/0677", "x.pdf", hash_parte="hash-de-otro"),
    ),
    ids=("sin-traza", "en-error", "de-otro-parte"),
)
def test_f013_r47_sin_un_pendiente_de_este_parte_no_hay_linea(montar, guardada):
    """R47 · solo `pendiente` y de este `hash`: lo demás no deja fichero."""
    m = montar(8, archivo=guardada, crear_carpetas=False)

    with pytest.raises(DestinoNoResuelto):
        m.archivar()

    assert m.log == []
    assert m.registro[-1] == TRAZA_ERROR


def test_f013_r47_la_linea_es_un_aviso_del_logger_del_paso(montar, caplog):
    """R47 · nivel de aviso, en el logger del paso, con el `hash` del parte."""
    m = montar(8, archivo=_pendiente("Postventa/0677", _nombre(8)), crear_carpetas=False)

    with (
        caplog.at_level(logging.INFO, logger=LOGGER_DEL_PASO),
        pytest.raises(DestinoNoResuelto),
    ):
        m.archivar()

    (registro,) = [r for r in caplog.records if "Postventa/0677" in r.getMessage()]
    assert registro.levelno == logging.WARNING
    assert HASH_DE_PRUEBA in registro.getMessage()


def test_f013_t10_el_doble_de_biblioteca_es_la_de_f006():
    """El doble compuesto sube a una `BibliotecaFalsa` de F-006, como siempre."""
    archivador = ArchivadorDePosventaFalso(ExploradorFalso())

    assert isinstance(archivador.biblioteca, BibliotecaFalsa)
