# services/postventa-api/tests/test_f033_situacion_con_archivo.py
"""La traza del archivo viaja con la situación, y la de un fichero subido no se pisa (F-033).

Bloque 1 de F-033: la **persistencia**. Cubre R1–R6 y R17 de
`specs/F-033-l1-traza-archivo/requirements.md`:

- R1 · `SituacionParte` gana un quinto campo, `archivo`, el último y a `None`.
- R2 · la consulta de la situación trae las ocho columnas de la traza.
- R3 · **sin ninguna sentencia más**: siguen siendo dos por llamada.
- R4 · sin ficha del parte, los tres huecos a `None` y ningún error.
- R5 · un `estado` que el dominio no conoce **revienta**.
- R6 · al log sale el estado de la traza y nada más.
- R17 · `upsert_archivo` no pisa una fila en `archivado`.

Todo sin red, sin base de datos y sin IA: `ConexionDoble` graba lo ejecutado
y devuelve filas preparadas. Los módulos de producción se consultan **por
atributo** (`sentencias.X`, `mapeo.Y`) y no con `from … import`: así, mientras
la pieza no exista, cada caso falla por su cuenta y dice qué le falta, en vez
de tumbar la recogida del fichero entero.

Ni un dato real: los identificadores de biblioteca son inventados y
reconocibles (`drive-inventado-it`), para que un log que los filtrara se viera.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import UTC, datetime

import pytest
from domain.models.estado import SituacionParte
from domain.models.persistencia import (
    EstadoArchivo,
    ResultadoGuardado,
    TrazaArchivo,
)
from domain.models.remesa import ModoDeteccion, ParteTroceado
from infrastructure.persistencia import mapeo, sentencias
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres

from tests.utiles_pg import ConexionDoble, RepositorioComoLaBase
from tests.utiles_validacion import extraccion_de_ejemplo

ESQUEMA = "postventa"
HASH = "hash-inventado-f033"
AHORA = datetime(2026, 9, 18, 10, 0, tzinfo=UTC)
ARCHIVADO_EN = datetime(2026, 9, 1, 9, 30, tzinfo=UTC)

#: Centinelas: si cualquiera de estos textos apareciera en un log, el caso de
#: R6 lo vería. Son identificadores de biblioteca (F-006 R26) o texto libre.
DRIVE_CENTINELA = "drive-inventado-it"
ITEM_CENTINELA = "item-centinela-f033"
WEB_URL_CENTINELA = "https://inventado.example/centinela-f033"
MOTIVO_CENTINELA = "motivo-centinela-f033"
CARPETA_CENTINELA = "Carpeta-centinela-f033"
NOMBRE_CENTINELA = "nombre-centinela-f033.pdf"

#: Lo que devuelve un `RETURNING (xmax = 0) AS creado` al crear.
FILA_CREADO = (True,)


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


def _traza(estado: EstadoArchivo = EstadoArchivo.ARCHIVADO, **cambios) -> TrazaArchivo:
    """Una traza de archivo inventada, con los ocho campos rellenos."""
    valores = {
        "hash_parte": HASH,
        "estado": estado,
        "nombre_fichero": NOMBRE_CENTINELA,
        "carpeta": CARPETA_CENTINELA,
        "drive_id": DRIVE_CENTINELA,
        "item_id": ITEM_CENTINELA,
        "web_url": WEB_URL_CENTINELA,
        "motivo": MOTIVO_CENTINELA,
        "archivado_at_utc": ARCHIVADO_EN,
    }
    valores.update(cambios)
    return TrazaArchivo(**valores)


def _columnas_de_archivo(traza: TrazaArchivo | None) -> tuple:
    """Las ocho columnas de la traza, **escritas a mano** en el orden de R2.

    A mano a propósito: si se sacaran de `_COLUMNAS_ARCHIVO`, un cambio de orden
    en producción cambiaría también el test y no lo cazaría nadie.
    """
    if traza is None:
        return (None,) * 8
    return (
        traza.estado.value,
        traza.nombre_fichero,
        traza.carpeta,
        traza.drive_id,
        traza.item_id,
        traza.web_url,
        traza.motivo,
        traza.archivado_at_utc,
    )


def _fila(
    *, archivo: TrazaArchivo | None = None, cierre: str | None = None
) -> tuple:
    """Una fila de dieciocho columnas: parte sin veredicto, y lo que se pida."""
    return (None,) * 9 + (cierre,) + _columnas_de_archivo(archivo)


def _responder_situacion(conexion: ConexionDoble, fila: tuple) -> None:
    conexion.responder(f"LEFT JOIN {ESQUEMA}.archivos", [fila])


def _seleccionadas() -> tuple[str, ...]:
    """Las columnas del `SELECT` de la situación, en su orden."""
    sql, _ = sentencias.select_veredicto_y_cierre(esquema=ESQUEMA, hash_parte=HASH)
    return tuple(
        columna.strip()
        for columna in sql.split("FROM", 1)[0].replace("SELECT", "", 1).split(",")
    )


# ==========================================================================
# R1 · el quinto campo de la situación
# ==========================================================================


def test_f033_r1_la_situacion_trae_archivo_a_none_por_omision():
    """R1 · `None` es «no consta ninguna traza de archivo», y no es un error."""
    assert SituacionParte().archivo is None


def test_f033_r1_archivo_es_el_ultimo_de_cinco_campos():
    """R1 · el último, para no romper ninguna construcción posicional."""
    nombres = tuple(campo.name for campo in dataclasses.fields(SituacionParte))

    assert nombres == (
        "decision_humana",
        "ultimo_estado_registrado",
        "estado_cierre",
        "validacion",
        "archivo",
    )


def test_f033_r1_la_situacion_guarda_la_traza_que_se_le_da():
    """R1 · el campo lleva una `TrazaArchivo`, entera."""
    traza = _traza()

    assert SituacionParte(archivo=traza).archivo is traza


# ==========================================================================
# R2 · la sentencia trae las ocho columnas de la traza
# ==========================================================================


def test_f033_r2_columnas_archivo_es_la_lista_de_la_tabla_en_su_orden():
    """R2 · una sola lista para escribir y leer la traza (`design.md` §3.2)."""
    assert sentencias._COLUMNAS_ARCHIVO == (
        "hash_parte",
        "estado",
        "nombre_fichero",
        "carpeta",
        "drive_id",
        "item_id",
        "web_url",
        "motivo",
        "archivado_at_utc",
    )


def test_f033_r2_la_sentencia_hace_left_join_a_archivos_anclado_en_partes():
    """R2 · `LEFT` y anclado en `partes`: sin archivar es el caso normal."""
    sql, _ = sentencias.select_veredicto_y_cierre(esquema=ESQUEMA, hash_parte=HASH)

    assert f"FROM {ESQUEMA}.partes AS p" in sql
    assert (
        f"LEFT JOIN {ESQUEMA}.archivos AS a ON a.hash_parte = p.hash_parte" in sql
    )
    assert sql.count("LEFT JOIN") == sql.count("JOIN") == 3


def test_f033_r2_las_ocho_columnas_nuevas_van_al_final_en_su_orden():
    """R2 · las diez de antes intactas, y detrás las de la traza, sin `hash`."""
    seleccionadas = _seleccionadas()

    assert seleccionadas[:10] == (
        "v.veredicto",
        "v.destino",
        "v.clasificacion_firma",
        "v.motivos",
        "v.avisos",
        "p.observaciones",
        "p.observaciones_confianza_pct",
        "p.codigo_obra",
        "p.numero_incidencia",
        "c.estado",
    )
    assert seleccionadas[10:] == (
        "a.estado",
        "a.nombre_fichero",
        "a.carpeta",
        "a.drive_id",
        "a.item_id",
        "a.web_url",
        "a.motivo",
        "a.archivado_at_utc",
    )


def test_f033_r2_las_columnas_nuevas_salen_de_la_misma_lista_que_escribe():
    """R2 · leer y escribir con la misma lista: dos listas divergen siempre."""
    assert _seleccionadas()[10:] == tuple(
        f"a.{columna}" for columna in sentencias._COLUMNAS_ARCHIVO[1:]
    )


def test_f033_r2_el_hash_sigue_siendo_el_unico_parametro():
    """R2 · el tercer `JOIN` no añade ningún valor al texto ni a los parámetros."""
    sql, parametros = sentencias.select_veredicto_y_cierre(
        esquema=ESQUEMA, hash_parte=HASH
    )

    assert sql.count("%s") == 1
    assert parametros == (HASH,)
    assert HASH not in sql


def test_f033_r2_el_adaptador_devuelve_la_traza_con_sus_ocho_campos(
    conexion, repositorio
):
    """R2 · la traza vuelve entera, con el `hash` que se pidió."""
    guardada = _traza()
    _responder_situacion(conexion, _fila(archivo=guardada))

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.archivo == guardada
    assert situacion.archivo.estado is EstadoArchivo.ARCHIVADO


@pytest.mark.parametrize("estado", list(EstadoArchivo))
def test_f033_r2_el_adaptador_traduce_cada_estado_de_archivo(
    conexion, repositorio, estado
):
    """R2 · los tres estados de la tabla llegan como su `Enum`."""
    _responder_situacion(conexion, _fila(archivo=_traza(estado)))

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.archivo.estado is estado


def test_f033_r2_sin_fila_en_archivos_la_traza_es_none(conexion, repositorio):
    """R2 · el `LEFT JOIN` no casa: `estado` a `NULL` es «no hay traza»."""
    _responder_situacion(conexion, _fila(archivo=None, cierre="pendiente"))

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.archivo is None
    assert situacion.estado_cierre == "pendiente"


def test_f033_r2_la_traza_convive_con_el_veredicto_y_el_cierre(conexion, repositorio):
    """R2 · la traza no desplaza ni al cierre ni a nada de las diez primeras."""
    _responder_situacion(conexion, _fila(archivo=_traza(), cierre="cerrado"))

    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.estado_cierre == "cerrado"
    assert situacion.validacion is None
    assert situacion.archivo == _traza()


def test_f033_r2_fila_a_traza_archivo_toma_el_hash_por_palabra_clave():
    """R2 · el `hash` no viaja en la fila: es el que se pidió."""
    traza = mapeo.fila_a_traza_archivo(
        _columnas_de_archivo(_traza()), hash_parte="otro-hash-inventado"
    )

    assert traza == _traza(hash_parte="otro-hash-inventado")


def test_f033_r2_fila_a_traza_archivo_sin_estado_es_none():
    """R2 · `estado` es `NOT NULL` en la tabla: a `NULL` solo si no hay fila."""
    assert mapeo.fila_a_traza_archivo((None,) * 8, hash_parte=HASH) is None


def test_f033_r2_la_traza_con_campos_opcionales_a_none_se_lee_igual():
    """R2 · una traza `pendiente` sin biblioteca ni fecha no es un error."""
    pendiente = TrazaArchivo(hash_parte=HASH, estado=EstadoArchivo.PENDIENTE)

    traza = mapeo.fila_a_traza_archivo(
        _columnas_de_archivo(pendiente), hash_parte=HASH
    )

    assert traza == pendiente


def test_f033_r2_fila_a_situacion_guardada_parte_la_fila_en_sus_dos_tramos():
    """R2 · las diez primeras a su mapeo de siempre, las ocho últimas a la traza."""
    validacion, estado_cierre, archivo = mapeo.fila_a_situacion_guardada(
        _fila(archivo=_traza(), cierre="dry_run_ok"), hash_parte=HASH
    )

    assert validacion is None
    assert estado_cierre == "dry_run_ok"
    assert archivo == _traza()


# ==========================================================================
# R3 · ninguna sentencia más
# ==========================================================================


@pytest.mark.parametrize("con_traza", [True, False])
def test_f033_r3_la_situacion_sigue_costando_dos_sentencias(
    conexion, repositorio, con_traza
):
    """R3 · **dos**, con traza y sin ella: criterio 4 de la ficha."""
    _responder_situacion(
        conexion, _fila(archivo=_traza() if con_traza else None)
    )

    repositorio.consultar_situacion(hash_parte=HASH)

    assert len(conexion.ejecutadas) == 2
    assert conexion.veces_con(f"FROM {ESQUEMA}.archivos") == 0
    assert conexion.veces_con(f"LEFT JOIN {ESQUEMA}.archivos AS a") == 1
    assert conexion.veces_con(f"FROM {ESQUEMA}.partes AS p") == 1


def test_f033_r3_el_corte_del_mapeo_coincide_con_la_sentencia():
    """R3 · el corte entre tramos es el nº de columnas antes de la traza."""
    seleccionadas = _seleccionadas()
    primera_de_archivo = next(
        posicion
        for posicion, columna in enumerate(seleccionadas)
        if columna.startswith("a.")
    )

    assert mapeo.COLUMNAS_DE_VEREDICTO_Y_CIERRE == primera_de_archivo == 10
    assert mapeo.COLUMNAS_DE_TRAZA_ARCHIVO == len(seleccionadas) - 10 == 8


@pytest.mark.parametrize("columnas", [17, 19, 10])
def test_f033_r3_una_fila_de_otro_largo_revienta(columnas):
    """R3 · una fila más corta o más larga es sentencia y mapeo divergidos."""
    fila = _fila(archivo=_traza())
    fila = (fila + (None,) * columnas)[:columnas]

    with pytest.raises(ValueError, match="18"):
        mapeo.fila_a_situacion_guardada(fila, hash_parte=HASH)


# ==========================================================================
# R4 · sin ficha del parte
# ==========================================================================


def test_f033_r4_sin_ficha_los_tres_huecos_a_none_y_sin_error(conexion, repositorio):
    """R4 · no vuelve ninguna fila: veredicto, cierre y traza a `None`."""
    situacion = repositorio.consultar_situacion(hash_parte=HASH)

    assert situacion.validacion is None
    assert situacion.estado_cierre is None
    assert situacion.archivo is None
    assert situacion == SituacionParte()
    assert len(conexion.ejecutadas) == 2


# ==========================================================================
# R5 · un estado desconocido revienta
# ==========================================================================


def test_f033_r5_un_estado_de_archivo_desconocido_revienta_en_el_mapeo():
    """R5 · traducirlo «como si fuera» otro cortaría o subiría sin motivo."""
    columnas = ("estado-inventado",) + _columnas_de_archivo(_traza())[1:]

    with pytest.raises(ValueError):
        mapeo.fila_a_traza_archivo(columnas, hash_parte=HASH)


def test_f033_r5_un_estado_desconocido_revienta_en_el_adaptador(
    conexion, repositorio
):
    """R5 · y no se traga en `consultar_situacion`."""
    fila = _fila(archivo=_traza())
    fila = fila[:10] + ("estado-inventado",) + fila[11:]
    _responder_situacion(conexion, fila)

    with pytest.raises(ValueError):
        repositorio.consultar_situacion(hash_parte=HASH)


# ==========================================================================
# R6 · el log trae el estado y nada más
# ==========================================================================


def test_f033_r6_el_log_trae_el_estado_de_la_traza(caplog, conexion, repositorio):
    """R6 · el estado es lo que hace falta para diagnosticar un L1."""
    _responder_situacion(conexion, _fila(archivo=_traza()))

    with caplog.at_level(logging.DEBUG):
        repositorio.consultar_situacion(hash_parte=HASH)

    assert "archivo=archivado" in caplog.text


def test_f033_r6_el_log_dice_que_no_hay_traza(caplog, conexion, repositorio):
    """R6 · «no hay» también se dice."""
    _responder_situacion(conexion, _fila(archivo=None))

    with caplog.at_level(logging.DEBUG):
        repositorio.consultar_situacion(hash_parte=HASH)

    assert "archivo=None" in caplog.text


def test_f033_r6_el_log_no_trae_identificadores_de_biblioteca(
    caplog, conexion, repositorio
):
    """R6 · ni `drive_id`, ni `item_id`, ni `web_url`, ni `motivo` (F-006 R26)."""
    _responder_situacion(conexion, _fila(archivo=_traza()))

    with caplog.at_level(logging.DEBUG):
        repositorio.consultar_situacion(hash_parte=HASH)

    for centinela in (
        DRIVE_CENTINELA,
        ITEM_CENTINELA,
        WEB_URL_CENTINELA,
        MOTIVO_CENTINELA,
        CARPETA_CENTINELA,
        NOMBRE_CENTINELA,
    ):
        assert centinela not in caplog.text


# ==========================================================================
# R17 · la traza de un fichero subido no se pisa
# ==========================================================================


def test_f033_r17_el_upsert_no_actualiza_una_fila_archivada():
    """R17 · el `WHERE` del `DO UPDATE`, como `cierres` y `graficos`."""
    sql, _ = sentencias.upsert_archivo(esquema=ESQUEMA, traza=_traza())

    assert f"WHERE {ESQUEMA}.archivos.estado <> %s" in sql
    assert sql.index("ON CONFLICT (hash_parte) DO UPDATE SET") < sql.index(
        f"WHERE {ESQUEMA}.archivos.estado <> %s"
    ) < sql.index("RETURNING (xmax = 0) AS creado")


def test_f033_r17_el_estado_terminal_va_como_parametro():
    """R17 · `archivado` en los parámetros, nunca pegado al texto."""
    sql, parametros = sentencias.upsert_archivo(
        esquema=ESQUEMA, traza=_traza(EstadoArchivo.PENDIENTE)
    )

    assert sentencias._ESTADO_ARCHIVO_TERMINAL == EstadoArchivo.ARCHIVADO.value
    assert parametros[-1] == "archivado"
    assert "'archivado'" not in sql
    assert "archivado'" not in sql
    assert sql.count("%s") == len(parametros) == 10


def test_f033_r17_el_insert_escribe_las_columnas_de_la_lista_unica():
    """R17 · el `INSERT` no cambia de texto salvo por el `WHERE`."""
    traza = _traza()
    sql, parametros = sentencias.upsert_archivo(esquema=ESQUEMA, traza=traza)

    columnas = ", ".join(sentencias._COLUMNAS_ARCHIVO)
    assert f"INSERT INTO {ESQUEMA}.archivos ({columnas}, intentos)" in sql
    assert parametros[:9] == (HASH,) + _columnas_de_archivo(traza)


def test_f033_r17_sin_fila_de_vuelta_el_repositorio_responde_sin_cambios(conexion):
    """R17 · el `DO UPDATE` no se aplicó: no había nada que hacer."""
    conexion.responder(f"INSERT INTO {ESQUEMA}.archivos", [])
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    resultado = repositorio.guardar_archivo(traza=_traza(EstadoArchivo.PENDIENTE))

    assert resultado is ResultadoGuardado.SIN_CAMBIOS


def test_f033_r17_el_log_de_guardar_registra_sin_cambios(caplog, conexion):
    """R17 · `SIN_CAMBIOS` se registra como cualquier otro resultado."""
    conexion.responder(f"INSERT INTO {ESQUEMA}.archivos", [])
    repositorio = RepositorioPostgres(conexion, esquema=ESQUEMA)

    with caplog.at_level(logging.INFO):
        repositorio.guardar_archivo(traza=_traza(EstadoArchivo.PENDIENTE))

    assert "resultado=sin_cambios" in caplog.text
    assert DRIVE_CENTINELA not in caplog.text


# ==========================================================================
# El doble que guarda columnas (`RepositorioComoLaBase`) imita R2 y R17
# ==========================================================================


def _base_con_el_parte() -> RepositorioComoLaBase:
    base = RepositorioComoLaBase()
    base.guardar_parte(
        parte=ParteTroceado(
            hash=HASH,
            origen="remesa_inventada.pdf",
            paginas_origen=(1,),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"%PDF-inventado",
        ),
        extraccion=extraccion_de_ejemplo(hash_parte=HASH),
        remesa_id="remesa-inventada",
        ahora=AHORA,
    )
    return base


def test_f033_r17_el_doble_como_la_base_no_pisa_una_traza_archivada():
    """R17 · el doble del circuito tiene que comportarse como la tabla."""
    base = _base_con_el_parte()

    primera = base.guardar_archivo(traza=_traza())
    segunda = base.guardar_archivo(traza=_traza(EstadoArchivo.PENDIENTE))

    assert primera is ResultadoGuardado.CREADO
    assert segunda is ResultadoGuardado.SIN_CAMBIOS
    assert base.archivos[HASH].estado is EstadoArchivo.ARCHIVADO


def test_f033_r17_el_doble_como_la_base_si_pisa_una_traza_pendiente():
    """R17 · solo `archivado` es terminal: `pendiente` y `error` se reintentan."""
    base = _base_con_el_parte()

    base.guardar_archivo(traza=_traza(EstadoArchivo.PENDIENTE))
    segunda = base.guardar_archivo(traza=_traza(EstadoArchivo.ERROR))
    tercera = base.guardar_archivo(traza=_traza())

    assert segunda is ResultadoGuardado.ACTUALIZADO
    assert tercera is ResultadoGuardado.ACTUALIZADO
    assert base.archivos[HASH].estado is EstadoArchivo.ARCHIVADO


def test_f033_r2_el_doble_como_la_base_devuelve_la_traza_desde_columnas():
    """R2 · la traza vuelve recompuesta, **no** el mismo objeto que entró."""
    base = _base_con_el_parte()
    guardada = _traza()
    base.guardar_archivo(traza=guardada)

    situacion = base.consultar_situacion(hash_parte=HASH)

    assert situacion.archivo == guardada
    assert situacion.archivo is not guardada


def test_f033_r4_el_doble_como_la_base_sin_ficha_no_trae_traza():
    """R4 · sin fila en `partes` no vuelve nada, aunque haya traza."""
    base = RepositorioComoLaBase()
    base.archivos[HASH] = _traza()

    assert base.consultar_situacion(hash_parte=HASH).archivo is None
