# services/postventa-api/tests/test_f033_l1_desde_el_almacen.py
"""L1 se lee del almacén, nunca del llamante (F-033, bloque 2).

Cubre R7–R11, R13–R16 y R18–R21 de
`specs/F-033-l1-traza-archivo/requirements.md` sobre **el paso**, con dobles:

- R7, R8 · la traza para L1 sale de la situación que ya leyó la puerta; el
  paso no la acepta por parámetro y no pregunta nada más.
- R9 · el orden de F-006 y F-019: puerta → nombrado → L1 → traza previa → …
- R10, R11 · `archivado` corta y devuelve la traza guardada; `pendiente` y
  `error` no.
- R13–R15 · se corta por `hash` + estado; si la traza apunta a otro destino,
  aviso propio, sin identificadores de biblioteca.
- R16 · nada se mueve, copia, borra ni renombra.
- R18, R19 · la carrera: `SIN_CAMBIOS` en la traza previa relee y no sube; en
  la final, se registra y no es fallo.
- R20 · un `pendiente` en otra ruta sigue, con aviso y log.
- R21 · no hay forma de forzar el re-archivo; un escaneo nuevo es otro parte.

Los símbolos nuevos del paso se consultan **por atributo** (`paso.X`) y no con
`from … import`: mientras no existan, cada caso falla por su cuenta y dice qué
le falta, en vez de tumbar la recogida del fichero entero.

Ni un dato real: los identificadores de biblioteca son inventados y
reconocibles (`drive-inventado-it`, `drive-inventado-posventa`), para que un
log o un aviso que los filtrara se viera.
"""

from __future__ import annotations

import dataclasses
import inspect
import logging
from datetime import UTC, datetime

import application.pipelines.paso_archivo as paso
import pytest
from domain.models.errores import (
    ArchivoFallido,
    NombradoImposible,
    ParteNoApto,
    PersistenciaNoDisponible,
)
from domain.models.estado import SituacionParte
from domain.models.persistencia import (
    EstadoArchivo,
    ResultadoGuardado,
    TrazaArchivo,
)

from tests.utiles_sharepoint import (
    CARPETA_BASE,
    HOST_FALSO,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    preexistente,
)
from tests.utiles_validacion import HASH_DE_PRUEBA

AHORA = datetime(2026, 9, 18, 11, 0, tzinfo=UTC)
#: Cuándo se archivó la traza que ya consta: **otro** instante que `AHORA`,
#: para que se vea si alguien la rehace en vez de devolverla.
ARCHIVADO_EN = datetime(2026, 9, 1, 9, 30, tzinfo=UTC)

CARPETA_ESPERADA = "Postventa/0677"
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"

#: Bibliotecas **inventadas** y reconocibles: si aparecen en un log o en un
#: aviso, el caso lo ve.
DRIVE_IT = "drive-inventado-it"
DRIVE_POSVENTA = "drive-inventado-posventa"
ITEM_GUARDADO = "item-guardado-f033"
WEB_URL_GUARDADA = f"{HOST_FALSO}/centinela-f033"

#: Lo que la traza previa apunta en el registro compartido (F-019).
TRAZA_PREVIA = "repositorio.guardar_archivo(pendiente)"
TRAZA_FINAL = "repositorio.guardar_archivo(archivado)"


# --------------------------------------------------------------------------
# Material
# --------------------------------------------------------------------------


def _archivada(**cambios) -> TrazaArchivo:
    """La traza que ya consta `archivado` de este parte, con sus ocho campos."""
    valores = {
        "hash_parte": HASH_DE_PRUEBA,
        "estado": EstadoArchivo.ARCHIVADO,
        "nombre_fichero": NOMBRE_ESPERADO,
        "carpeta": CARPETA_ESPERADA,
        "drive_id": DRIVE_POSVENTA,
        "item_id": ITEM_GUARDADO,
        "web_url": WEB_URL_GUARDADA,
        "archivado_at_utc": ARCHIVADO_EN,
    }
    valores.update(cambios)
    return TrazaArchivo(**valores)


class RepositorioQueCuenta(RepositorioFalso):
    """`RepositorioFalso` que además **cuenta las consultas de situación**.

    Es lo único con lo que se puede afirmar R8 —L1 no cuesta ninguna consulta
    propia— y la relectura única de R18. Cada consulta son las dos sentencias
    de `consultar_situacion` (R3, bloque 1).
    """

    def __init__(self, **extra) -> None:
        super().__init__(**extra)
        self.consultas: list[str] = []

    def consultar_situacion(self, *, hash_parte: str) -> SituacionParte:
        self.consultas.append(hash_parte)
        return super().consultar_situacion(hash_parte=hash_parte)


class RepositorioEnCarrera(RepositorioQueCuenta):
    """La carrera de R18: **otra petición** archiva el parte por medio.

    En la primera escritura de la traza —la previa en `pendiente`— la otra
    petición ya ha dejado su traza `archivado`: a partir de ahí, la situación
    la trae. El resultado de esa escritura lo programa el caso con
    `resultados` (el `SIN_CAMBIOS` del `WHERE` de R17).
    """

    def __init__(self, *, la_de_la_otra: TrazaArchivo | None, **extra) -> None:
        super().__init__(**extra)
        self.la_de_la_otra = la_de_la_otra

    def guardar_archivo(self, *, traza: TrazaArchivo) -> ResultadoGuardado:
        resultado = super().guardar_archivo(traza=traza)
        if self.llamadas_guardar_archivo == 1 and self.la_de_la_otra is not None:
            self.situacion = dataclasses.replace(
                self.situacion, archivo=self.la_de_la_otra
            )
        return resultado


def _dobles(archivo: TrazaArchivo | None = None, *, clase=RepositorioQueCuenta, **extra):
    """Archivador y repositorio **con el mismo registro**, y la situación
    guardada: el veredicto apto de este parte y, si se pasa, su traza.

    La traza se **siembra en la situación**, que es de donde la lee L1 desde
    F-033: el paso ya no la recibe por parámetro.
    """
    registro: list[str] = []
    ctx = contexto_apto()
    archivador = ArchivoPortFalso(
        extra.pop("biblioteca", None), registro=registro, **extra.pop("archivador", {})
    )
    repositorio = clase(
        registro=registro,
        situacion=SituacionParte(validacion=ctx.validacion, archivo=archivo),
        **extra,
    )
    return archivador, repositorio, registro


def _archivar(archivador, repositorio, ctx=None, **extra):
    """El paso con la carpeta base y la hora de siempre."""
    return paso.paso_archivo(
        ctx if ctx is not None else contexto_apto(),
        archivador,
        repositorio,
        carpeta_base=CARPETA_BASE,
        ahora=AHORA,
        **extra,
    )


def _aviso_intento_anterior(carpeta: str, nombre: str) -> str:
    return paso.AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA.format(carpeta=carpeta, nombre=nombre)


# ==========================================================================
# R7 · L1 se lee de la situación, y de ningún otro sitio
# ==========================================================================


def test_f033_r7_el_paso_ya_no_acepta_la_traza_por_parametro():
    """R7 · `traza_previa` desaparece de la firma (D-2)."""
    parametros = inspect.signature(paso.paso_archivo).parameters

    assert "traza_previa" not in parametros


def test_f033_r7_pasarle_una_traza_es_un_error_de_tipo():
    """R7 · no hay un camino viejo que siga funcionando a escondidas."""
    archivador, repositorio, _ = _dobles()

    with pytest.raises(TypeError):
        _archivar(archivador, repositorio, traza_previa=_archivada())

    assert archivador.llamadas == []


def test_f033_r7_drive_id_vigente_es_opcional_y_por_palabra_clave():
    """R7, R15 · entra `drive_id_vigente`, con `None` por omisión."""
    parametro = inspect.signature(paso.paso_archivo).parameters["drive_id_vigente"]

    assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
    assert parametro.default is None


def test_f033_r7_la_traza_archivada_de_la_situacion_corta():
    """R7 · **el defecto**: con la traza en el almacén, hoy se volvía a subir."""
    archivador, repositorio, _ = _dobles(_archivada())

    ctx = _archivar(archivador, repositorio)

    assert archivador.llamadas == []
    assert archivador.biblioteca.subidas == 0
    assert paso.AVISO_YA_ARCHIVADO in ctx.avisos


# ==========================================================================
# R8 · L1 no cuesta ninguna consulta propia
# ==========================================================================


def test_f033_r8_el_corte_cuesta_una_consulta_y_ninguna_escritura():
    """R8 · la situación de la puerta, y nada más: ni lectura ni escritura."""
    archivador, repositorio, registro = _dobles(_archivada())

    _archivar(archivador, repositorio)

    assert repositorio.consultas == [HASH_DE_PRUEBA]
    assert repositorio.llamadas_guardar_archivo == 0
    assert registro == []


def test_f033_r8_el_camino_normal_tampoco_pregunta_de_mas():
    """R8 · sin traza, una sola consulta: L1 reutiliza la de la puerta."""
    archivador, repositorio, _ = _dobles()

    _archivar(archivador, repositorio)

    assert repositorio.consultas == [HASH_DE_PRUEBA]
    assert archivador.biblioteca.subidas == 1


# ==========================================================================
# R9 · el orden
# ==========================================================================


def test_f033_r9_l1_va_antes_que_la_traza_previa():
    """R9 · al revés, un parte archivado quedaría degradado a `pendiente`."""
    archivador, repositorio, registro = _dobles(_archivada())

    _archivar(archivador, repositorio)

    assert TRAZA_PREVIA not in registro
    assert registro == []


def test_f033_r9_sin_corte_el_orden_es_el_de_f019():
    """R9 · traza previa, carpeta, homónimo, subida y traza final."""
    archivador, repositorio, registro = _dobles()

    _archivar(archivador, repositorio)

    assert registro == [
        TRAZA_PREVIA,
        "archivador.asegurar_carpeta",
        "archivador.buscar",
        "archivador.subir",
        TRAZA_FINAL,
    ]


def test_f033_r9_la_puerta_va_antes_que_l1():
    """R9 · un parte sin veredicto guardado no llega a L1, aunque haya traza."""
    archivador = ArchivoPortFalso()
    repositorio = RepositorioQueCuenta(situacion=SituacionParte(archivo=_archivada()))

    with pytest.raises(ParteNoApto):
        _archivar(archivador, repositorio)

    assert archivador.llamadas == []


def test_f033_r9_el_nombrado_va_antes_que_l1():
    """R9 · un nombre imposible sale antes de mirar la traza.

    > **Enmienda del 2026-09-22 (F-031).** Hasta hoy el caso vaciaba el código
    > de obra **del contexto** (`contexto_apto(codigo_obra=None)`), porque el
    > nombrado leía de ahí. Desde F-031 el nombre sale del código **guardado**,
    > así que un contexto sin código ya no produce ningún nombre imposible: es
    > la situación la que tiene que traerlo vacío. R9 no cambia —el nombrado
    > sigue yendo antes que L1—, cambia de dónde se le quita la entrada.
    """
    archivador, repositorio, registro = _dobles(_archivada())
    repositorio.situacion = dataclasses.replace(
        repositorio.situacion,
        validacion=dataclasses.replace(
            repositorio.situacion.validacion, codigo_obra=""
        ),
    )

    with pytest.raises(NombradoImposible):
        _archivar(archivador, repositorio)

    assert registro == []


# ==========================================================================
# R10, R11 · qué corta y qué no
# ==========================================================================


def test_f033_r10_devuelve_la_traza_guardada_tal_cual():
    """R10 · **la** traza del almacén: su carpeta, su nombre y su `web_url`."""
    guardada = _archivada()
    archivador, repositorio, _ = _dobles(guardada)

    ctx = _archivar(archivador, repositorio, drive_id_vigente=DRIVE_POSVENTA)

    assert ctx.archivo is guardada
    assert ctx.archivo.web_url == WEB_URL_GUARDADA
    assert ctx.archivo.archivado_at_utc == ARCHIVADO_EN
    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]


def test_f033_r10_una_traza_archivada_de_otro_parte_no_corta():
    """R10 · «de **este** `hash_parte`»: la de otro no dice nada de este."""
    archivador, repositorio, _ = _dobles(_archivada(hash_parte="hash-de-otro-parte"))

    ctx = _archivar(archivador, repositorio)

    assert archivador.biblioteca.subidas == 1
    assert ctx.archivo.hash_parte == HASH_DE_PRUEBA
    assert paso.AVISO_YA_ARCHIVADO not in ctx.avisos


@pytest.mark.parametrize("estado", (EstadoArchivo.PENDIENTE, EstadoArchivo.ERROR))
def test_f033_r11_pendiente_y_error_no_cortan(estado):
    """R11 · se reintenta: un fallo anterior no atasca el parte."""
    archivador, repositorio, _ = _dobles(
        _archivada(estado=estado, drive_id=None, item_id=None, web_url=None,
                   archivado_at_utc=None)
    )

    ctx = _archivar(archivador, repositorio)

    assert archivador.biblioteca.subidas == 1
    assert repositorio.estados == ["pendiente", "archivado"]
    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert ctx.avisos == []


# ==========================================================================
# R13, R14, R15 · la traza apunta a otro destino
# ==========================================================================


#: (cambios en la traza guardada, drive vigente, ¿otro destino?)
CASOS_DE_DESTINO = (
    pytest.param({}, DRIVE_POSVENTA, False, id="igual_en_todo"),
    pytest.param(
        {"nombre_fichero": "0677 - RS 26.08 - 0123 PARTE FIRMADO.pdf"},
        DRIVE_POSVENTA, True, id="otro_nombre_f032",
    ),
    pytest.param({"carpeta": "Postventa/0678"}, DRIVE_POSVENTA, True, id="otra_carpeta"),
    pytest.param({"drive_id": DRIVE_IT}, DRIVE_POSVENTA, True, id="otra_biblioteca_f013"),
    pytest.param({"drive_id": DRIVE_IT}, None, False, id="sin_drive_vigente"),
    pytest.param({"drive_id": None}, DRIVE_POSVENTA, False, id="traza_sin_drive"),
    pytest.param({"drive_id": None}, None, False, id="ninguno_de_los_dos_drive"),
    pytest.param({"nombre_fichero": None}, DRIVE_POSVENTA, True, id="traza_sin_nombre"),
    pytest.param({"carpeta": None}, DRIVE_POSVENTA, True, id="traza_sin_carpeta"),
)


@pytest.mark.parametrize(("cambios", "drive_vigente", "en_otro"), CASOS_DE_DESTINO)
def test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino(
    cambios, drive_vigente, en_otro
):
    """R13 · corta por `hash` + estado; R14 · si difiere, el aviso propio."""
    guardada = _archivada(**cambios)
    archivador, repositorio, registro = _dobles(guardada)

    ctx = _archivar(archivador, repositorio, drive_id_vigente=drive_vigente)

    # R13: corta en todos los casos, y sin tocar nada.
    assert archivador.llamadas == []
    assert registro == []
    assert ctx.archivo is guardada
    # R14: el aviso de otro destino solo cuando difiere, y después del de L1.
    if en_otro:
        assert ctx.avisos == [
            paso.AVISO_YA_ARCHIVADO,
            paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO,
        ]
    else:
        assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]


def test_f033_r14_el_aviso_dice_que_sigue_alli_y_que_no_se_subio():
    """R14 · lo que tiene que entender quien lo lea, y sin identificadores."""
    aviso = paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO

    assert "sigue allí" in aviso
    assert "no se ha vuelto a subir" in aviso
    assert "de entonces" in aviso
    assert "drive" not in aviso.lower()


def test_f033_r15_el_drive_id_no_sale_en_ningun_log_ni_aviso(caplog):
    """R15, R24 · la biblioteca decide el aviso pero no aparece en él."""
    archivador, repositorio, _ = _dobles(_archivada(drive_id=DRIVE_IT))

    with caplog.at_level(logging.DEBUG):
        ctx = _archivar(archivador, repositorio, drive_id_vigente=DRIVE_POSVENTA)

    texto = caplog.text + " ".join(ctx.avisos)
    assert paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO in ctx.avisos
    for centinela in (DRIVE_IT, DRIVE_POSVENTA, ITEM_GUARDADO, WEB_URL_GUARDADA):
        assert centinela not in texto


# ==========================================================================
# R16 · nada se mueve
# ==========================================================================


def test_f033_r16_lo_archivado_en_otro_destino_se_queda_donde_esta():
    """R16 · ni mover, ni copiar, ni borrar, ni renombrar: la biblioteca igual."""
    biblioteca = BibliotecaFalsa()
    viejo = preexistente(
        biblioteca, carpeta=CARPETA_ESPERADA,
        nombre="0677 - RS 26.08 - 0123 PARTE FIRMADO.pdf", contenido=b"%PDF viejo",
    )
    antes = dict(biblioteca.elementos)
    subidas_antes = biblioteca.subidas
    archivador, repositorio, _ = _dobles(
        _archivada(nombre_fichero=viejo.nombre), biblioteca=biblioteca
    )

    _archivar(archivador, repositorio, drive_id_vigente=DRIVE_POSVENTA)

    assert biblioteca.elementos == antes
    assert biblioteca.subidas == subidas_antes
    assert archivador.llamadas == []


def test_f033_r16_el_paso_solo_usa_las_tres_operaciones_del_puerto():
    """R16 · en el camino que sube, solo carpeta, búsqueda y subida."""
    archivador, repositorio, _ = _dobles(
        _archivada(estado=EstadoArchivo.PENDIENTE, carpeta="Postventa/0678")
    )

    _archivar(archivador, repositorio)

    assert set(archivador.operaciones) == {"asegurar_carpeta", "buscar", "subir"}


# ==========================================================================
# R18 · la carrera en la traza previa
# ==========================================================================


def test_f033_r18_sin_cambios_en_la_previa_relee_y_no_sube():
    """R18 · otra petición lo archivó por medio: se devuelve la suya."""
    de_la_otra = _archivada()
    archivador, repositorio, registro = _dobles(
        clase=RepositorioEnCarrera,
        la_de_la_otra=de_la_otra,
        resultados={1: ResultadoGuardado.SIN_CAMBIOS},
    )

    ctx = _archivar(archivador, repositorio, drive_id_vigente=DRIVE_POSVENTA)

    assert archivador.llamadas == []
    assert registro == [TRAZA_PREVIA]
    assert repositorio.consultas == [HASH_DE_PRUEBA, HASH_DE_PRUEBA]
    assert ctx.archivo is de_la_otra
    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO]


def test_f033_r18_la_relectura_responde_como_l1_tambien_en_otro_destino():
    """R18 · «responde como L1»: si la otra archivó en otra ruta, lo dice."""
    de_la_otra = _archivada(carpeta="Postventa/0678")
    archivador, repositorio, _ = _dobles(
        clase=RepositorioEnCarrera,
        la_de_la_otra=de_la_otra,
        resultados={1: ResultadoGuardado.SIN_CAMBIOS},
    )

    ctx = _archivar(archivador, repositorio)

    assert archivador.llamadas == []
    assert ctx.avisos == [
        paso.AVISO_YA_ARCHIVADO,
        paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO,
    ]


def test_f033_r18_si_la_relectura_no_trae_archivado_no_se_sube_nada():
    """R18 · ante la duda, no se sube: error que lo dice, y ni un byte."""
    archivador, repositorio, _ = _dobles(
        clase=RepositorioEnCarrera,
        la_de_la_otra=None,
        resultados={1: ResultadoGuardado.SIN_CAMBIOS},
    )

    with pytest.raises(PersistenciaNoDisponible, match="no se ha subido"):
        _archivar(archivador, repositorio)

    assert archivador.llamadas == []
    assert repositorio.consultas == [HASH_DE_PRUEBA, HASH_DE_PRUEBA]


@pytest.mark.parametrize(
    "resultado", (ResultadoGuardado.CREADO, ResultadoGuardado.ACTUALIZADO)
)
def test_f033_r18_sin_carrera_no_hay_relectura(resultado):
    """R18 · la relectura **solo** ocurre en la carrera."""
    archivador, repositorio, _ = _dobles(resultados={1: resultado})

    _archivar(archivador, repositorio)

    assert repositorio.consultas == [HASH_DE_PRUEBA]
    assert archivador.biblioteca.subidas == 1


# ==========================================================================
# R19 · `SIN_CAMBIOS` en la traza final no es un fallo
# ==========================================================================


def test_f033_r19_sin_cambios_en_la_final_se_registra_y_responde(caplog):
    """R19 · se responde con lo que se subió, y queda una línea de log."""
    archivador, repositorio, _ = _dobles(resultados={2: ResultadoGuardado.SIN_CAMBIOS})

    with caplog.at_level(logging.INFO, logger=paso.__name__):
        ctx = _archivar(archivador, repositorio)

    assert archivador.biblioteca.subidas == 1
    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert ctx.archivo.archivado_at_utc == AHORA
    lineas = [r.getMessage() for r in caplog.records if r.name == paso.__name__]
    assert any(HASH_DE_PRUEBA in linea and "sin_cambios" in linea for linea in lineas)
    assert ctx.archivo.drive_id not in caplog.text
    assert ctx.archivo.web_url not in caplog.text


def test_f033_r19_sin_cambios_en_la_de_error_deja_salir_el_fallo(caplog):
    """R19 · la traza de error tampoco lo convierte en otro fallo."""
    archivador, repositorio, _ = _dobles(
        archivador={"fallo": ArchivoFallido("el proveedor no respondió")},
        resultados={2: ResultadoGuardado.SIN_CAMBIOS},
    )

    with caplog.at_level(logging.INFO, logger=paso.__name__), pytest.raises(
        ArchivoFallido, match="el proveedor no respondió"
    ):
        _archivar(archivador, repositorio)

    lineas = [r.getMessage() for r in caplog.records if r.name == paso.__name__]
    assert any(HASH_DE_PRUEBA in linea and "sin_cambios" in linea for linea in lineas)


def test_f033_r19_un_resultado_normal_en_la_final_no_deja_linea_de_carrera(caplog):
    """R19 · la línea es de la carrera, no del camino normal."""
    archivador, repositorio, _ = _dobles()

    with caplog.at_level(logging.INFO, logger=paso.__name__):
        _archivar(archivador, repositorio)

    assert "sin_cambios" not in caplog.text


# ==========================================================================
# R20 · un intento anterior en otra ruta
# ==========================================================================


def _pendiente_en(carpeta: str, nombre: str) -> TrazaArchivo:
    """Una traza `pendiente`: lo que deja la previa si no llegó la final."""
    return TrazaArchivo(
        hash_parte=HASH_DE_PRUEBA,
        estado=EstadoArchivo.PENDIENTE,
        nombre_fichero=nombre,
        carpeta=carpeta,
    )


@pytest.mark.parametrize(
    ("carpeta", "nombre"),
    (
        pytest.param("Postventa/0678", NOMBRE_ESPERADO, id="otra_carpeta"),
        pytest.param(CARPETA_ESPERADA, "0677 - RS 26.08 - 0123 PARTE FIRMADO.pdf",
                     id="otro_nombre"),
    ),
)
def test_f033_r20_pendiente_en_otra_ruta_sigue_con_aviso_y_log(caplog, carpeta, nombre):
    """R20 · se archiva, pero queda el rastro del intento anterior."""
    archivador, repositorio, _ = _dobles(_pendiente_en(carpeta, nombre))

    with caplog.at_level(logging.INFO, logger=paso.__name__):
        ctx = _archivar(archivador, repositorio)

    assert archivador.biblioteca.subidas == 1
    assert ctx.archivo.estado is EstadoArchivo.ARCHIVADO
    assert ctx.avisos == [_aviso_intento_anterior(carpeta, nombre)]
    lineas = [r.getMessage() for r in caplog.records if r.name == paso.__name__]
    assert any(
        HASH_DE_PRUEBA in linea and carpeta in linea and nombre in linea
        for linea in lineas
    )


def test_f033_r20_el_aviso_va_antes_de_escribir_la_traza_previa(caplog):
    """R20 · «antes»: el aviso y el log quedan aunque la previa pise la ruta."""
    archivador, repositorio, _ = _dobles(
        _pendiente_en("Postventa/0678", NOMBRE_ESPERADO),
        fallos={1: PersistenciaNoDisponible("la base no responde")},
    )

    with caplog.at_level(logging.INFO, logger=paso.__name__), pytest.raises(
        PersistenciaNoDisponible
    ):
        _archivar(archivador, repositorio)

    assert "Postventa/0678" in caplog.text
    assert archivador.llamadas == []


def test_f033_r20_pendiente_en_la_misma_ruta_no_avisa(caplog):
    """R20 · el mismo destino: el reintento de siempre, sin ruido."""
    archivador, repositorio, _ = _dobles(
        _pendiente_en(CARPETA_ESPERADA, NOMBRE_ESPERADO)
    )

    with caplog.at_level(logging.INFO, logger=paso.__name__):
        ctx = _archivar(archivador, repositorio)

    assert ctx.avisos == []
    assert "intento anterior" not in caplog.text


def test_f033_r20_una_traza_de_error_en_otra_ruta_no_avisa():
    """R20 · solo `pendiente` puede ser un fichero subido sin traza final."""
    archivador, repositorio, _ = _dobles(
        dataclasses.replace(
            _pendiente_en("Postventa/0678", NOMBRE_ESPERADO), estado=EstadoArchivo.ERROR
        )
    )

    ctx = _archivar(archivador, repositorio)

    assert ctx.avisos == []
    assert archivador.biblioteca.subidas == 1


def test_f033_r20_un_pendiente_de_otro_parte_no_avisa():
    """R20 · la traza de otro `hash` no dice nada de este parte."""
    archivador, repositorio, _ = _dobles(
        dataclasses.replace(
            _pendiente_en("Postventa/0678", NOMBRE_ESPERADO), hash_parte="hash-de-otro"
        )
    )

    ctx = _archivar(archivador, repositorio)

    assert ctx.avisos == []


def test_f033_r20_el_aviso_no_lleva_identificadores_de_biblioteca():
    """R20, R24 · carpeta y nombre sí; biblioteca, elemento o URL, no."""
    aviso = _aviso_intento_anterior("Postventa/0678", NOMBRE_ESPERADO)

    assert "Postventa/0678" in aviso
    assert NOMBRE_ESPERADO in aviso
    assert "drive" not in paso.AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA.lower()
    assert "http" not in paso.AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA.lower()


# ==========================================================================
# R21 · no hay re-archivo forzado; un escaneo nuevo es otro parte
# ==========================================================================


def test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar():
    """R21 · ni parámetro del paso: la firma entera, cerrada.

    > **Enmienda del 2026-09-22 (F-031).** La firma gana
    > `codigos_declarados`, y el test lo recoge en vez de relajarse a un
    > `not in`: lo que R21 exige es que **la firma entera** esté a la vista, de
    > modo que cualquier parámetro nuevo obligue a mirar si abre una puerta.
    > Éste no la abre: es lo que afirma quien llama, solo sirve para
    > **cotejarlo** contra lo guardado (F-031 R3) y no puede decidir nada
    > (F-031 R11) — mucho menos re-archivar un parte que ya consta archivado.
    """
    parametros = set(inspect.signature(paso.paso_archivo).parameters)

    assert parametros == {
        "ctx",
        "archivador",
        "repositorio",
        "carpeta_base",
        "ahora",
        "drive_id_vigente",
        "codigos_declarados",
    }


def test_f033_r21_un_escaneo_nuevo_es_otro_parte_y_se_archiva():
    """R21 · otro `hash`, mismo nombre: se sube y L2 avisa del reemplazo."""
    biblioteca = BibliotecaFalsa()
    preexistente(
        biblioteca, carpeta=CARPETA_ESPERADA, nombre=NOMBRE_ESPERADO,
        contenido=b"%PDF escaneo anterior",
    )
    nuevo = contexto_apto(hash_parte="hash-del-escaneo-nuevo")
    archivador = ArchivoPortFalso(biblioteca)
    repositorio = RepositorioQueCuenta(
        situacion=SituacionParte(validacion=nuevo.validacion)
    )

    ctx = _archivar(archivador, repositorio, ctx=nuevo)

    assert biblioteca.subidas == 2
    assert len(biblioteca.elementos) == 1
    assert ctx.archivo.hash_parte == "hash-del-escaneo-nuevo"
    assert ctx.avisos == [paso.AVISO_REEMPLAZADO]
