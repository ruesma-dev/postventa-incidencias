# services/postventa-api/tests/test_f026_persistencia.py
"""La aprobación contra la base: SQL, mapeo y revocación (F-026, T7 y T8).

**Sin base de datos y sin un socket abierto.** La guarda `sin_red` de
`tests/conftest.py` sigue puesta durante toda la suite, y quien hace de
PostgreSQL es el doble de `tests/utiles_pg.py`, que graba lo que el adaptador
ejecutó y le devuelve las filas que el test haya preparado.

Lo que se demuestra aquí, y que ninguna otra pieza del proyecto puede
demostrar:

- **La revocación ocurre en la escritura, no en la lectura** (D-F de
  `design.md` §7). Guardar una validación cuya huella ya no es la aprobada
  revoca la aprobación **en la misma operación y sin que nadie tenga que
  acordarse de pedirlo** (R30); guardar una cuya huella coincide **no revoca
  nada** (R32), que es lo que hace verdad el criterio «la aprobación sobrevive
  a volver a subir la remesa».
- **Revocar no borra** (R33), y lo que se escribe como motivo es una etiqueta
  corta y cerrada, nunca el texto del cliente que la provocó (R34).
- **Volver a aprobar deja la fila viva** (R17): el `ON CONFLICT` limpia la
  revocación anterior en vez de acumular una segunda fila.
- **Lo que se guarda son códigos de motivo, no textos** (R14), y **ni una
  letra de la transcripción manuscrita** (R15).

Ni un dato real: los `oid`, los `hash` y las observaciones son inventados.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta

import pytest
from domain.models.aprobacion import (
    Aprobacion,
    MotivoRevocacion,
    huella_de_veredicto,
)
from domain.models.persistencia import ResultadoGuardado
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    ResultadoValidacion,
)
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia import sentencias
from infrastructure.persistencia.mapeo import (
    fila_a_aprobacion,
    json_de_codigos_de_motivo,
)
from infrastructure.persistencia.repositorio_pg import RepositorioPostgres

from tests.utiles_pg import ConexionDoble, RepositorioEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

ESQUEMA = "postventa"
TABLA = f"{ESQUEMA}.aprobaciones"
AHORA = datetime(2026, 9, 11, 10, 0, tzinfo=UTC)
OID = "oid-opaco-inventado-para-el-test"

#: Una observación manuscrita **inventada**, en la línea de las reales: el
#: cliente firma y a la vez dice que la reparación no está entera. Es el texto
#: que R15 prohíbe copiar a esta tabla, así que los tests lo buscan por aquí.
OBSERVACION = "Se aprecian parcheados. No se reparo la totalidad."

FILA_CREADO = (True,)


def _validacion(
    *, observaciones: str | None = OBSERVACION, firma: str = "humana", **campos
) -> ResultadoValidacion:
    """El veredicto que emite F-004 **de verdad** sobre el material que se pida.

    No se monta a mano un `ResultadoValidacion`: la huella se calcula sobre lo
    que F-004 emite, y un veredicto inventado podría tener una combinación que
    las reglas nunca producen.
    """
    from domain.models.validacion import validar_parte

    return validar_parte(
        extraccion_de_ejemplo(observaciones=observaciones, **campos),
        lectura_de_firma(firma),
    )


def _aprobacion(validacion: ResultadoValidacion, **cambios) -> Aprobacion:
    """La aprobación que dejaría una persona sobre ese veredicto."""
    argumentos = {
        "hash_parte": validacion.hash_parte,
        "aprobado_por": OID,
        "aprobado_at_utc": AHORA,
        "destino_aprobado": validacion.destino,
        "motivos_aprobados": tuple(motivo.codigo for motivo in validacion.motivos),
        "huella_aprobada": huella_de_veredicto(validacion),
        "validado_at_utc": AHORA,
    }
    argumentos.update(cambios)
    return Aprobacion(**argumentos)


@pytest.fixture
def conexion() -> ConexionDoble:
    return ConexionDoble().responder("RETURNING (xmax = 0)", [FILA_CREADO])


@pytest.fixture
def repositorio(conexion) -> RepositorioPostgres:
    return RepositorioPostgres(conexion, esquema=ESQUEMA)


# ==========================================================================
# T7 · Las sentencias
# ==========================================================================


# --------------------------------------------------------------------------
# R17 · una sola fila por parte, y volver a aprobar la deja viva
# --------------------------------------------------------------------------


def test_f026_r17_aprobar_dos_veces_actualiza_la_misma_fila():
    """R17 · `ON CONFLICT (hash_parte) DO UPDATE`, nunca una segunda fila.

    Sin el `ON CONFLICT`, aprobar dos veces el mismo parte —que es lo que pasa
    en cuanto alguien corrige una coma, revalida y vuelve a aprobar— reventaría
    contra la clave primaria, y el borde traduciría eso a un 503 que no tiene
    nada que ver con lo que ocurrió.
    """
    sql, _ = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
    )

    assert f"INSERT INTO {TABLA}" in sql
    assert "ON CONFLICT (hash_parte) DO UPDATE" in sql


def test_f026_r17_volver_a_aprobar_deja_la_aprobacion_viva():
    """R17 · el `DO UPDATE` limpia la revocación anterior.

    Es el camino normal después de una revocación: se corrigió el parte, el
    veredicto cambió, la aprobación se revocó, y alguien vuelve a mirarlo y lo
    aprueba otra vez. Si el `upsert` no pusiera `revocada_at_utc` a `NULL`, esa
    segunda aprobación nacería muerta y el parte no entraría en el circuito por
    una decisión que nadie tomó.

    Se escribe `NULL` **literal** y no `EXCLUDED.revocada_at_utc`: así lo que
    garantiza la vigencia es la sentencia, y no que quien la llame se acuerde
    de construir la dataclass sin revocar.
    """
    sql, _ = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
    )
    despues_del_conflicto = sql.split("ON CONFLICT", 1)[1]

    assert "revocada_at_utc = NULL" in despues_del_conflicto
    assert "revocada_motivo = NULL" in despues_del_conflicto


def test_f026_el_upsert_no_interpola_ni_un_valor_en_el_texto():
    """Ningún valor se pega al SQL: van todos como parámetros del driver.

    Es la regla del módulo entero, y aquí llega el `oid` de una persona y la
    huella de su decisión.
    """
    aprobacion = _aprobacion(_validacion())

    sql, parametros = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=aprobacion
    )

    assert OID not in sql
    assert aprobacion.huella_aprobada not in sql
    assert OID in parametros
    assert aprobacion.huella_aprobada in parametros


def test_f026_el_upsert_tiene_tantos_marcadores_como_parametros():
    """Un marcador de más o de menos es un `ProgrammingError` en producción.

    Se cuenta sobre el `VALUES`, que es donde el número tiene que cuadrar con
    los parámetros que se envían.
    """
    sql, parametros = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
    )
    values = sql.split("VALUES (", 1)[1].split(")\n", 1)[0]

    assert values.count("%s") == len(parametros)


def test_f026_r14_lo_que_se_guarda_son_codigos_de_motivo_y_no_textos():
    """R14, R15 · el código es contrato de F-004; el texto es redacción.

    Y el texto de un motivo es la frase que lee Posventa —«el cliente ha
    escrito observaciones a mano»—, que puede cambiar sin que cambie nada de lo
    que se aprobó. Guardarlo haría que dos aprobaciones idénticas parecieran
    distintas por una corrección de estilo.
    """
    validacion = _validacion()
    aprobacion = _aprobacion(validacion)

    _, parametros = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=aprobacion
    )
    guardado = next(
        valor
        for valor in parametros
        if isinstance(valor, str) and valor.startswith("[")
    )

    assert json.loads(guardado) == [
        CodigoMotivo.OBSERVACIONES_MANUSCRITAS.value
    ]
    for motivo in validacion.motivos:
        assert motivo.texto not in guardado


def test_f026_r15_el_upsert_no_lleva_ni_una_letra_del_texto_manuscrito():
    """R15 · la transcripción vive en `postventa.partes` y en ningún sitio más.

    Una segunda copia de texto manuscrito de un cliente dobla la exposición y
    diverge. Lo que viaja sobre «qué veredicto se aprobó» es la huella, que es
    un `sha256` y no lleva dentro ninguna subcadena del original.
    """
    _, parametros = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
    )
    escrito = " ".join(str(valor) for valor in parametros)

    assert OBSERVACION not in escrito
    assert "parcheados" not in escrito.lower()


# --------------------------------------------------------------------------
# R30, R33, R34 · el `UPDATE` de la revocación
# --------------------------------------------------------------------------


def test_f026_r33_la_revocacion_es_un_update_y_nunca_un_delete():
    """R33 · la decisión se tomó, y eso no deja de ser verdad.

    Borrar la fila dejaría un parte que vuelve a pedir aprobación sin rastro de
    que alguien ya había decidido sobre él, que es justo la mitad de lo que
    esta tabla existe para registrar.
    """
    sql, _ = sentencias.revocar_aprobacion_si_cambio(
        esquema=ESQUEMA, resultado=_validacion(), ahora=AHORA
    )

    assert sql.startswith(f"UPDATE {TABLA}")
    assert "DELETE" not in sql.upper()


def test_f026_r30_la_revocacion_solo_toca_lo_vigente_y_lo_que_cambio():
    """R30, R32 · las dos condiciones del `WHERE`, y las dos hacen falta.

    `revocada_at_utc IS NULL` evita reescribir la fecha de una revocación que
    ya estaba hecha —la primera es la que cuenta—, y `huella_aprobada <> %s` es
    lo que distingue «el veredicto cambió» de «se ha vuelto a subir la misma
    remesa», que es el gesto con el que se recupera el trabajo tras recargar.
    """
    sql, _ = sentencias.revocar_aprobacion_si_cambio(
        esquema=ESQUEMA, resultado=_validacion(), ahora=AHORA
    )
    where = sql.split("WHERE", 1)[1]

    assert "hash_parte = %s" in where
    assert "revocada_at_utc IS NULL" in where
    assert "huella_aprobada <> %s" in where


def test_f026_r30_la_huella_viaja_como_parametro_y_no_pegada_al_sql():
    """La huella es un valor, y los valores no se interpolan.

    Da igual que un `sha256` sea hexadecimal e inofensivo: el día que alguien
    copie esta sentencia para comparar otra cosa, la costumbre es lo que
    decide.
    """
    validacion = _validacion()
    huella = huella_de_veredicto(validacion)

    sql, parametros = sentencias.revocar_aprobacion_si_cambio(
        esquema=ESQUEMA, resultado=validacion, ahora=AHORA
    )

    assert huella not in sql
    assert huella in parametros
    assert validacion.hash_parte in parametros
    assert AHORA in parametros


def test_f026_r34_el_motivo_de_la_revocacion_es_una_etiqueta_corta():
    """R34 · una etiqueta cerrada, nunca el texto que la provocó.

    Lo que provoca la revocación es que el cliente escribiera otra cosa, o que
    el modelo leyera otra cosa: guardar «el motivo» de verdad sería copiar la
    transcripción manuscrita a una segunda tabla, que es exactamente lo que
    R15 prohíbe.
    """
    _, parametros = sentencias.revocar_aprobacion_si_cambio(
        esquema=ESQUEMA, resultado=_validacion(), ahora=AHORA
    )

    assert MotivoRevocacion.VEREDICTO_CAMBIADO.value in parametros
    assert OBSERVACION not in " ".join(str(valor) for valor in parametros)


def test_f026_la_revocacion_tiene_tantos_marcadores_como_parametros():
    """Cuatro marcadores, cuatro parámetros, y en el mismo orden."""
    sql, parametros = sentencias.revocar_aprobacion_si_cambio(
        esquema=ESQUEMA, resultado=_validacion(), ahora=AHORA
    )

    assert sql.count("%s") == len(parametros) == 4


# --------------------------------------------------------------------------
# El `SELECT`, y que lo que se lee es lo que se escribió
# --------------------------------------------------------------------------


def test_f026_el_select_busca_por_hash_con_parametro():
    """La consulta de la aprobación de un parte, por su `hash`."""
    sql, parametros = sentencias.select_aprobacion(
        esquema=ESQUEMA, hash_parte="hash-inventado"
    )

    assert f"FROM {TABLA}" in sql
    assert "WHERE hash_parte = %s" in sql
    assert parametros == ("hash-inventado",)


def test_f026_el_select_lee_las_mismas_columnas_que_escribe_el_upsert():
    """Una fila leída por posición se rompe en silencio si las listas divergen.

    Es el mismo cuidado que `_COLUMNAS_GRAFICO` de F-012, y por el mismo
    motivo: `fila_a_aprobacion` desempaqueta por orden, así que el día que el
    `SELECT` traiga las columnas en otro orden reconstruiría la aprobación de
    otra persona con la huella en el sitio del `oid`, y nadie lo notaría.
    """
    seleccionadas = sentencias.select_aprobacion(
        esquema=ESQUEMA, hash_parte="hash-inventado"
    )[0]
    seleccionadas = seleccionadas.split("SELECT ", 1)[1].split("\n", 1)[0]
    insertadas = sentencias.upsert_aprobacion(
        esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
    )[0]
    insertadas = insertadas.split("(", 1)[1].split(")", 1)[0]

    columnas_del_select = [nombre.strip() for nombre in seleccionadas.split(",")]
    columnas_del_insert = [nombre.strip() for nombre in insertadas.split(",")]

    assert columnas_del_select[: len(columnas_del_insert)] == columnas_del_insert
    assert columnas_del_select[len(columnas_del_insert) :] == [
        "revocada_at_utc",
        "revocada_motivo",
    ]


# --------------------------------------------------------------------------
# El mapeo
# --------------------------------------------------------------------------


def test_f026_los_codigos_se_serializan_como_lista_de_cadenas():
    """`["firma_no_humana"]`, que es lo que espera una columna `jsonb`."""
    serializado = json_de_codigos_de_motivo(
        (CodigoMotivo.FIRMA_NO_HUMANA, CodigoMotivo.OBSERVACIONES_MANUSCRITAS)
    )

    assert json.loads(serializado) == [
        "firma_no_humana",
        "observaciones_manuscritas",
    ]


def test_f026_fila_a_aprobacion_reconstruye_la_dataclass_con_sus_enum():
    """Lo que vuelve de la base es dominio, no cadenas sueltas.

    `Destino(...)` y `CodigoMotivo(...)` **revientan** si la base trae una
    etiqueta que el dominio no conoce, y eso es lo correcto: pasaría si alguien
    ampliara el `CHECK` del `.sql` sin ampliar el `Enum`, y traducirlo «como si
    fuera» otro destino haría que la puerta del paso admitiera en el circuito
    un parte aprobado para otra cosa.
    """
    fila = (
        "hash-inventado",
        OID,
        AHORA,
        Destino.COLA_VALIDACION_HUMANA.value,
        ["observaciones_manuscritas"],
        "f" * 64,
        AHORA,
        None,
        None,
    )

    aprobacion = fila_a_aprobacion(fila)

    assert aprobacion == Aprobacion(
        hash_parte="hash-inventado",
        aprobado_por=OID,
        aprobado_at_utc=AHORA,
        destino_aprobado=Destino.COLA_VALIDACION_HUMANA,
        motivos_aprobados=(CodigoMotivo.OBSERVACIONES_MANUSCRITAS,),
        huella_aprobada="f" * 64,
        validado_at_utc=AHORA,
    )
    assert aprobacion.vigente


def test_f026_fila_a_aprobacion_admite_el_jsonb_como_texto():
    """El driver devuelve `jsonb` deserializado o como texto según la consulta.

    Se admiten los dos, igual que hace `_motivos_desde_json` con la cola: que
    una aprobación se quede sin motivos por un detalle de adaptación sería un
    fallo caro y silencioso —la fila seguiría ahí, pero diría que no se aprobó
    nada—.
    """
    fila = (
        "hash-inventado",
        OID,
        AHORA,
        Destino.REVISION_MANUAL.value,
        '["firma_no_humana"]',
        "f" * 64,
        AHORA,
        None,
        None,
    )

    aprobacion = fila_a_aprobacion(fila)

    assert aprobacion.motivos_aprobados == (CodigoMotivo.FIRMA_NO_HUMANA,)


def test_f026_r33_una_fila_revocada_vuelve_del_mapeo_como_revocada():
    """R33 · la fila sigue ahí, y lo que dice es que ya no vale."""
    fila = (
        "hash-inventado",
        OID,
        AHORA,
        Destino.REVISION_MANUAL.value,
        [],
        "f" * 64,
        AHORA,
        AHORA + timedelta(minutes=5),
        MotivoRevocacion.VEREDICTO_CAMBIADO.value,
    )

    aprobacion = fila_a_aprobacion(fila)

    assert not aprobacion.vigente
    assert aprobacion.revocada_motivo == "veredicto_cambiado"


def test_f026_lo_que_escribe_el_upsert_vuelve_igual_por_el_mapeo():
    """Ida y vuelta: lo que se guarda es lo que se lee.

    Es la comprobación que une las dos mitades de T7 y la que no puede hacer
    ninguna de las dos por separado. Los parámetros del `upsert` se leen como
    si fueran la fila del `SELECT`, que es exactamente lo que serán.
    """
    original = _aprobacion(_validacion(firma="ilegible"))

    _, parametros = sentencias.upsert_aprobacion(esquema=ESQUEMA, aprobacion=original)
    recuperada = fila_a_aprobacion((*parametros, None, None))

    assert recuperada == original


# --------------------------------------------------------------------------
# El esquema, pegado al SQL pero validado
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "constructora",
    [
        lambda esquema: sentencias.select_aprobacion(
            esquema=esquema, hash_parte="h"
        ),
        lambda esquema: sentencias.revocar_aprobacion_si_cambio(
            esquema=esquema, resultado=_validacion(), ahora=AHORA
        ),
    ],
)
def test_f026_un_esquema_hostil_no_llega_al_sql(constructora):
    """Lo único que se pega al texto es el esquema, y se valida antes.

    Un `PG_SCHEMA` hostil sería una inyección con permisos de despliegue contra
    un servidor que comparten cuatro proyectos.
    """
    from domain.models.errores import DdlInseguro

    with pytest.raises(DdlInseguro):
        constructora("postventa; DROP TABLE partes")


def test_f026_las_tres_sentencias_van_al_esquema_propio():
    """Nada sin cualificar: sin esquema, la sentencia aterriza donde diga el
    `search_path`, y aquí eso es la producción de otros tres proyectos."""
    textos = (
        sentencias.upsert_aprobacion(
            esquema=ESQUEMA, aprobacion=_aprobacion(_validacion())
        )[0],
        sentencias.select_aprobacion(esquema=ESQUEMA, hash_parte="h")[0],
        sentencias.revocar_aprobacion_si_cambio(
            esquema=ESQUEMA, resultado=_validacion(), ahora=AHORA
        )[0],
    )

    for texto in textos:
        assert TABLA in texto
        assert not re.search(r"\bpublic\.", texto)


# ==========================================================================
# T8 · El puerto y el adaptador
# ==========================================================================


def test_f026_el_adaptador_cumple_el_puerto_ampliado(repositorio):
    """Las dos operaciones nuevas son parte del **contrato**, no un extra.

    Sin esto, los tres pasos del circuito podrian llamar a algo que solo
    existe en PostgreSQL, y el doble en memoria con el que se prueban dejaria
    de encajar sin que nadie lo notara hasta el despliegue.
    """
    assert isinstance(repositorio, RepositorioPartesPort)


def test_f026_el_doble_en_memoria_tambien_cumple_el_puerto_ampliado():
    """Y el doble de los tests, tambien: si no, el puerto seria papel mojado.

    `RepositorioEnMemoria` es lo que reciben los pasos del pipeline en toda la
    suite. Un doble que no implemente el puerto entero deja de poder sustituir
    al adaptador justo en la pieza nueva.
    """
    assert isinstance(RepositorioEnMemoria(), RepositorioPartesPort)


def test_f026_guardar_la_aprobacion_ejecuta_el_upsert(conexion, repositorio):
    """La decision de una persona llega a su tabla, y a ninguna otra."""
    resultado = repositorio.guardar_aprobacion(aprobacion=_aprobacion(_validacion()))

    assert resultado == ResultadoGuardado.CREADO
    assert conexion.veces_con(f"INSERT INTO {TABLA}") == 1
    assert conexion.veces_con(f"INSERT INTO {ESQUEMA}.validaciones") == 0


def test_f026_consultar_una_aprobacion_que_no_existe_devuelve_none(repositorio):
    """`None` **no es un error**: es que a ese parte no lo ha aprobado nadie.

    Que sea `None` y no una excepcion es lo que permite que los tres pasos
    pregunten siempre, sin tener que saber de antemano si el parte paso por
    revision.
    """
    assert repositorio.consultar_aprobacion(hash_parte="hash-inventado") is None


def test_f026_consultar_devuelve_la_aprobacion_del_parte(conexion, repositorio):
    """Y cuando hay fila, vuelve como dominio, no como cadenas sueltas."""
    conexion.responder(
        f"FROM {TABLA}",
        [
            (
                "hash-inventado",
                OID,
                AHORA,
                Destino.COLA_VALIDACION_HUMANA.value,
                '["observaciones_manuscritas"]',
                "f" * 64,
                AHORA,
                None,
                None,
            )
        ],
    )

    aprobacion = repositorio.consultar_aprobacion(hash_parte="hash-inventado")

    assert aprobacion is not None
    assert aprobacion.destino_aprobado == Destino.COLA_VALIDACION_HUMANA
    assert aprobacion.motivos_aprobados == (CodigoMotivo.OBSERVACIONES_MANUSCRITAS,)
    assert aprobacion.vigente


# --------------------------------------------------------------------------
# R30, R32 - la revocacion va pegada al guardado de la validacion
# --------------------------------------------------------------------------


def test_f026_r30_guardar_una_validacion_revoca_en_la_misma_operacion(
    conexion, repositorio
):
    """R30 - nadie tiene que acordarse de pedir la revocacion.

    Es el requisito entero: quien corrige un campo y revalida no sabe que
    existe una aprobacion, y el paso que despues lee la fila no puede
    recomputar la huella. Si la revocacion no viajara aqui, una aprobacion
    caducada pareceria viva hasta que alguien la mirara — y quien la mira es
    la puerta que deja cerrar una incidencia en el ERP de produccion.
    """
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)

    assert conexion.veces_con(f"UPDATE {TABLA}") == 1


def test_f026_r30_las_dos_sentencias_van_en_una_sola_transaccion(
    conexion, repositorio
):
    """«En la misma operacion» es literal: un `commit` para las dos.

    Con dos transacciones habria una ventana —corta, pero real— en la que el
    veredicto nuevo ya esta guardado y la aprobacion del viejo sigue viva. Un
    paso que leyera justo ahi admitiria en el circuito un parte que nadie ha
    aprobado.
    """
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)

    assert len(conexion.ejecutadas) == 2
    assert conexion.commits == 1


def test_f026_r30_la_revocacion_compara_con_la_huella_del_veredicto_guardado(
    conexion, repositorio
):
    """La huella que viaja es la de **este** veredicto, no otra.

    Es lo que hace que la comparacion signifique algo: la fila se revoca si y
    solo si lo aprobado no es lo que se acaba de guardar.
    """
    validacion = _validacion()

    repositorio.guardar_validacion(resultado=validacion, ahora=AHORA)

    revocacion = conexion.primera_con(f"UPDATE {TABLA}")
    assert revocacion.parametros[-1] == huella_de_veredicto(validacion)
    assert revocacion.parametros[-2] == validacion.hash_parte


def test_f026_r32_revalidar_sin_cambios_manda_la_misma_huella(conexion, repositorio):
    """R32 - volver a subir la misma remesa **no** revoca nada.

    El doble no ejecuta el `WHERE`, asi que lo que se comprueba es lo que el
    `WHERE` decide: que dos guardados del mismo veredicto mandan la misma
    huella, con lo que `huella_aprobada <> %s` no casa y la fila no se toca.

    Sin esto, el unico gesto con el que se recupera el trabajo tras recargar la
    pantalla —volver a subir la remesa, que reprocesa cada parte— invalidaria
    todas las aprobaciones.
    """
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)

    huellas = _huellas_revocadas(conexion)

    assert huellas[0] == huellas[1]


def test_f026_r30_un_veredicto_distinto_manda_otra_huella(conexion, repositorio):
    """Y la otra mitad: si el papel se lee de otra forma, la huella cambia.

    Aqui cambia la clasificacion de la firma, que es exactamente el caso que
    motivo la feature: una persona dio por buena **esa** firma dudosa, y el
    reproceso ha leido otra cosa.
    """
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)
    repositorio.guardar_validacion(resultado=_validacion(firma="ilegible"), ahora=AHORA)

    huellas = _huellas_revocadas(conexion)

    assert huellas[0] != huellas[1]


def _huellas_revocadas(conexion: ConexionDoble) -> list[str]:
    """Las huellas con las que se ha comparado, en orden."""
    return [
        ejecutada.parametros[-1]
        for ejecutada in conexion.ejecutadas
        if f"UPDATE {TABLA}" in ejecutada.sql
    ]


def test_f026_r33_la_revocacion_que_se_ejecuta_no_borra_la_fila(conexion, repositorio):
    """R33 - lo que llega a la base es un `UPDATE`, y ni un `DELETE` en toda la
    operacion."""
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)

    assert "DELETE" not in " ".join(conexion.sql_ejecutado).upper()


def test_f026_r34_lo_que_se_escribe_como_motivo_es_la_etiqueta_corta(
    conexion, repositorio
):
    """R34 - `veredicto_cambiado`, y nunca la observacion del cliente.

    La transcripcion manuscrita viaja dentro del `ResultadoValidacion` que
    recibe esta operacion, asi que la tentacion esta a mano: basta con pasarla
    como «motivo» para que la tabla de aprobaciones acabe siendo una segunda
    copia del texto del papel.
    """
    repositorio.guardar_validacion(resultado=_validacion(), ahora=AHORA)

    revocacion = conexion.primera_con(f"UPDATE {TABLA}")
    assert revocacion.parametros[1] == MotivoRevocacion.VEREDICTO_CAMBIADO.value
    assert OBSERVACION not in " ".join(str(valor) for valor in revocacion.parametros)


# --------------------------------------------------------------------------
# El log, que lo lee cualquiera que abra Application Insights
# --------------------------------------------------------------------------


def test_f026_el_log_de_la_aprobacion_no_lleva_ni_el_oid_ni_la_huella(
    conexion, repositorio, caplog
):
    """Quien aprobo se consulta en la base, no se reparte por el log (R13).

    El `oid` es un dato personal seudonimo, y la huella identifica un veredicto
    concreto: ninguno de los dos hace falta para saber que la operacion fue
    bien, que es lo unico que este log tiene que contar.
    """
    aprobacion = _aprobacion(_validacion())
    conexion.responder(
        f"FROM {TABLA}",
        [
            (
                aprobacion.hash_parte,
                OID,
                AHORA,
                aprobacion.destino_aprobado.value,
                [],
                aprobacion.huella_aprobada,
                AHORA,
                None,
                None,
            )
        ],
    )

    with caplog.at_level("INFO"):
        repositorio.guardar_aprobacion(aprobacion=aprobacion)
        repositorio.consultar_aprobacion(hash_parte=aprobacion.hash_parte)

    registrado = caplog.text
    assert OID not in registrado
    assert aprobacion.huella_aprobada not in registrado
    assert OBSERVACION not in registrado
