# services/postventa-api/tests/test_f012_dominio_grafico.py
"""El dominio del gráfico: lo que decide sin red, sin SQL y sin reloj (F-012).

`domain/models/grafico.py` es la pieza que compone **exactamente** lo que
viajará a la pasarela y la que decide si un gráfico está colgado. Las dos
cosas se pueden equivocar en silencio:

- una petición mal compuesta adjunta el parte a la reclamación equivocada, o
  con un nombre que no cruza con el de SharePoint;
- y `esta_colgado` decidido por `committed` a solas daría por **fallido** un
  éxito idempotente, que es el aviso literal que la propia pasarela pone en su
  contrato (`azure-apps/sigrid_api.md` §8.8).

Por eso `esta_colgado` es una función de una línea con sus **cuatro
cuadrantes** probados aquí, y por eso `clasificar_codigo` recorre los doce
códigos de la lista cerrada más uno inventado.

**Ni un dato real**: los bytes son un PDF sintético que empieza por `%PDF-` y
sigue con relleno; los códigos de obra e incidencia son inventados.
"""

from __future__ import annotations

import hashlib

import pytest
from domain.models.cierre import Reclamacion
from domain.models.errores import (
    CuerpoDeGraficoInvalido,
    GraficoDemasiadoGrande,
    GraficoNoEsPdf,
)
from domain.models.grafico import (
    CODIGOS_PASARELA_PRECONDICION,
    CODIGOS_PASARELA_RECHAZO,
    CODIGOS_PASARELA_REINTENTABLES,
    FILAS_ESPERADAS_GRAFICO,
    FIRMA_PDF,
    LONGITUD_MAXIMA_NOM,
    LONGITUD_MAXIMA_RES,
    LONGITUD_MAXIMA_USU,
    RES_GRAFICO_PARTE,
    PeticionGrafico,
    RespuestaGrafico,
    clasificar_codigo,
    componer_peticion,
    esta_colgado,
    validar_fichero,
)
from domain.models.nombrado import nombre_de_archivo

#: Un PDF sintético: la firma real y relleno detrás. **No es un parte.**
#: Los partes de `muestras/` llevan el DNI manuscrito de un cliente y no se
#: versionan ni se copian a la suite (`CLAUDE.md`, regla dura).
PDF = FIRMA_PDF + b"1.7\nsintetico para el test\n%%EOF\n"

#: Un tope holgado para los casos que no prueban el tope.
TOPE = 10 * 1024 * 1024

LOGIN = "loginraroinventado"
OBRA = "0677"
INCIDENCIA = "RS26.08/0123"


def _reclamacion(*, ide: int = 111_222, tip: int = 708) -> Reclamacion:
    """Una reclamación leída del ERP, con valores inventados."""
    return Reclamacion(
        ide=ide,
        emp=1,
        tip=tip,
        est=3,
        codigo=INCIDENCIA,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def _peticion(**cambios) -> PeticionGrafico:
    """La petición del caso bueno, con los cambios que pida el test."""
    tamano, huella = validar_fichero(PDF, tope_bytes=TOPE)
    argumentos = {
        "reclamacion": _reclamacion(),
        "login": LOGIN,
        "codigo_obra": OBRA,
        "numero_incidencia": INCIDENCIA,
        "gratipide": 35,
        "contenido": PDF,
        "bytes": tamano,
        "sha256": huella,
    }
    argumentos.update(cambios)
    return componer_peticion(**argumentos)


def _respuesta(**cambios) -> RespuestaGrafico:
    """Una respuesta de la pasarela, con los cambios que pida el test."""
    argumentos = {
        "ok": True,
        "committed": True,
        "idempotente": False,
        "dry_run": False,
        "filas_afectadas": 3,
        "cod": "202609061200000123.loginraroinventado",
        "ide_negocio": 5,
        "ide_documental": 6,
        "ide_enlace": 7,
        "pos": 64,
        "bytes": len(PDF),
        "sha256": hashlib.sha256(PDF).hexdigest(),
        "avisos": (),
    }
    argumentos.update(cambios)
    return RespuestaGrafico(**argumentos)


# --------------------------------------------------------------------------
# R7 · el `sha256` es el de los bytes exactos que se envían
# --------------------------------------------------------------------------


def test_f012_r7_el_sha256_es_el_de_los_bytes_exactos():
    """R7 · lo que la pasarela coteja, y lo que decide su idempotencia.

    No es el `hash` del parte (la huella de páginas de F-002): son dos
    identificadores distintos y confundirlos haría que un parte re-troceado
    pareciera el mismo documento.
    """
    tamano, huella = validar_fichero(PDF, tope_bytes=TOPE)

    assert tamano == len(PDF)
    assert huella == hashlib.sha256(PDF).hexdigest()


def test_f012_r7_el_sha256_viaja_en_la_peticion_tal_y_como_se_calculo():
    peticion = _peticion()

    assert peticion.sha256 == hashlib.sha256(PDF).hexdigest()
    assert peticion.bytes == len(PDF)


def test_f012_r7_dos_bytes_distintos_dan_dos_huellas_distintas():
    """Sin esto, un `sha256` constante pasaría los dos tests de arriba."""
    _, una = validar_fichero(PDF, tope_bytes=TOPE)
    _, otra = validar_fichero(PDF + b"x", tope_bytes=TOPE)

    assert una != otra


# --------------------------------------------------------------------------
# R9 · `nom` es EL MISMO nombre con el que el parte está en SharePoint
# --------------------------------------------------------------------------


def test_f012_r9_el_nombre_es_el_mismo_que_compone_el_archivo():
    """R9 · un documento, un nombre, dos sitios.

    Cruzar SharePoint con Sigrid tiene que ser comparar dos cadenas iguales.
    Si este nombre se compusiera aparte, divergiría el día que cambie el
    sufijo o el separador.
    """
    peticion = _peticion()

    assert peticion.nom == nombre_de_archivo(
        codigo_obra=OBRA, numero_incidencia=INCIDENCIA
    )
    assert peticion.nom == "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"


def test_f012_r9_un_guion_largo_en_la_incidencia_da_el_mismo_nombre():
    """R9 · el guion largo sale de los escaneos y de Word.

    Dos lecturas del mismo parte que solo difieran en el guion tienen que
    producir el mismo nombre, o en Sigrid acabarían dos gráficos que a ojo son
    idénticos.
    """
    con_guion_largo = _peticion(numero_incidencia="RS26.08 – 0123")

    assert con_guion_largo.nom == _peticion().nom


def test_f012_r9_un_nombre_que_no_cabe_en_el_erp_se_rechaza():
    """R9 · `gra.nom` es `varchar(255)`: lo que no cabe no se trunca.

    Un nombre truncado es otro nombre, y dejaría de cruzar con SharePoint.
    """
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _peticion(codigo_obra="X" * (LONGITUD_MAXIMA_NOM + 1))

    assert str(LONGITUD_MAXIMA_NOM) in fallo.value.motivo


def test_f012_r9_el_nombre_del_caso_normal_cabe_de_sobra():
    assert len(_peticion().nom) <= LONGITUD_MAXIMA_NOM


# --------------------------------------------------------------------------
# R10 · `res` es la descripción que teclea Posventa
# --------------------------------------------------------------------------


def test_f012_r10_la_descripcion_es_la_de_posventa_y_cabe():
    """R10 · `PARTE FIRMADO`, 3.197 de 3.680 gráficos de la clase 35 [MEDIDO].

    Es lo que la ficha de Sigrid enseña como «Descripción» a quien la abre.
    """
    peticion = _peticion()

    assert peticion.res == RES_GRAFICO_PARTE == "PARTE FIRMADO"
    assert len(peticion.res) <= LONGITUD_MAXIMA_RES == 48


# --------------------------------------------------------------------------
# R12 · el login, y su tope
# --------------------------------------------------------------------------


def test_f012_r12_el_login_viaja_tal_cual_y_cabe():
    peticion = _peticion()

    assert peticion.usu == LOGIN
    assert len(peticion.usu) <= LONGITUD_MAXIMA_USU == 24


def test_f012_r12_un_login_que_no_cabe_en_usu_cod_se_rechaza():
    """R12 · `usu.cod` es Texto 24: lo que no cabe no se trunca.

    Un login truncado es otro login, y firmaría el gráfico a nombre de nadie.
    """
    with pytest.raises(CuerpoDeGraficoInvalido) as fallo:
        _peticion(login="l" * (LONGITUD_MAXIMA_USU + 1))

    assert str(LONGITUD_MAXIMA_USU) in fallo.value.motivo


def test_f012_r12_sin_login_no_se_compone_nada():
    with pytest.raises(CuerpoDeGraficoInvalido):
        _peticion(login="   ")


# --------------------------------------------------------------------------
# R8 · `conide` y `contip` salen de la reclamación leída
# --------------------------------------------------------------------------


def test_f012_r8_el_concepto_y_su_tipo_salen_de_la_reclamacion():
    """R8 · nunca de una constante ni de la configuración.

    Es el mismo principio que R4 de F-009: la configuración sirve para
    **buscar**, y lo que se escribe sale de lo que el ERP devolvió.
    """
    peticion = _peticion(reclamacion=_reclamacion(ide=987_654, tip=708))

    assert peticion.conide == 987_654
    assert peticion.contip == 708


def test_f012_r11_la_clase_de_grafico_es_la_que_se_le_pasa():
    """R11 · `SIGRID_GRATIPIDE_PARTE`, nunca un literal en el paso."""
    assert _peticion(gratipide=35).gratipide == 35
    assert _peticion(gratipide=34).gratipide == 34


# --------------------------------------------------------------------------
# R18 · el tope, comprobado ANTES de llamar a nadie
# --------------------------------------------------------------------------


def test_f012_r18_un_byte_de_mas_aborta():
    """R18 · el tope se comprueba aquí y no en la pasarela.

    Mandar 13 MB de base64 por el proxy para que los rechacen al otro lado es
    gastar el presupuesto de 45 s en un 409 que se sabía de antemano.
    """
    contenido = FIRMA_PDF + b"y" * 100

    with pytest.raises(GraficoDemasiadoGrande):
        validar_fichero(contenido, tope_bytes=len(contenido) - 1)


def test_f012_r18_justo_en_el_tope_pasa():
    """El límite es `>`, no `>=`: un fichero de exactamente el tope cabe."""
    contenido = FIRMA_PDF + b"y" * 100

    tamano, _ = validar_fichero(contenido, tope_bytes=len(contenido))

    assert tamano == len(contenido)


def test_f012_r18_el_mensaje_dice_cuanto_ocupa_y_cual_es_el_tope():
    """R18 · sin los dos números, quien lo recibe no sabe qué corregir."""
    contenido = FIRMA_PDF + b"y" * 100

    with pytest.raises(GraficoDemasiadoGrande) as fallo:
        validar_fichero(contenido, tope_bytes=50)

    assert str(len(contenido)) in fallo.value.motivo
    assert "50" in fallo.value.motivo


# --------------------------------------------------------------------------
# R19 · la firma de PDF
# --------------------------------------------------------------------------


def test_f012_r19_lo_que_no_empieza_por_la_firma_de_pdf_se_rechaza():
    """R19 · la pasarela solo admite `%PDF-`, y se corta antes de llamarla."""
    with pytest.raises(GraficoNoEsPdf):
        validar_fichero(b"PK\x03\x04 esto es un zip", tope_bytes=TOPE)


def test_f012_r19_un_fichero_vacio_se_rechaza():
    with pytest.raises(GraficoNoEsPdf):
        validar_fichero(b"", tope_bytes=TOPE)


def test_f012_r19_la_firma_se_mira_al_principio_y_no_en_cualquier_sitio():
    """Un `%PDF-` en mitad del fichero no lo convierte en un PDF."""
    with pytest.raises(GraficoNoEsPdf):
        validar_fichero(b"basura" + FIRMA_PDF, tope_bytes=TOPE)


def test_f012_r18_r19_el_tope_se_mira_antes_que_la_firma():
    """Un fichero enorme que además no es PDF se rechaza por el tamaño.

    Da igual cuál gane mientras el orden esté decidido y probado: lo que no
    puede pasar es que haya que decodificar 13 MB para descubrir que no era
    un PDF.
    """
    with pytest.raises(GraficoDemasiadoGrande):
        validar_fichero(b"z" * 100, tope_bytes=10)


# --------------------------------------------------------------------------
# R26 · `esta_colgado`, con los cuatro cuadrantes
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ok", "committed", "idempotente", "colgado"),
    [
        (True, True, False, True),
        (True, False, True, True),
        (True, True, True, True),
        (True, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
    ],
)
def test_f012_r26_esta_colgado_recorre_los_cuatro_cuadrantes(
    ok, committed, idempotente, colgado
):
    """R26 · `ok and (committed or idempotente)`, y ni una lectura más.

    Los dos casos que sostienen el requisito:

    - `ok:true committed:false idempotente:true` → **colgado**. Es la
      respuesta idempotente real, y decidir por `committed` la daría por
      fallida.
    - `ok:true committed:false idempotente:false` → **no colgado**. Es el
      dry-run: no se ha escrito nada y no se puede dar por adjuntado.
    """
    respuesta = _respuesta(ok=ok, committed=committed, idempotente=idempotente)

    assert esta_colgado(respuesta) is colgado


def test_f012_r26_el_dry_run_correcto_no_cuenta_como_colgado():
    """El caso que más veces se ejecuta: mirar qué pasaría no adjunta nada."""
    assert (
        esta_colgado(
            _respuesta(
                committed=False, idempotente=False, dry_run=True, filas_afectadas=0
            )
        )
        is False
    )


def test_f012_las_filas_esperadas_de_un_commit_real_son_tres():
    """R27 · documental + negocio + enlace. Tres filas, dos bases."""
    assert FILAS_ESPERADAS_GRAFICO == 3


# --------------------------------------------------------------------------
# R31–R34 · `clasificar_codigo`, los doce códigos y uno inventado
# --------------------------------------------------------------------------


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_REINTENTABLES)
def test_f012_r31_los_codigos_reintentables_se_clasifican_como_tales(codigo):
    """R31 · el ERP quedó sin cambios y el reintento es seguro → 502."""
    assert clasificar_codigo(codigo) == "reintentable"


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_PRECONDICION)
def test_f012_r32_los_codigos_de_precondicion_se_clasifican_como_tales(codigo):
    """R32 · falta una precondición del dueño de `sigrid-api` → 503."""
    assert clasificar_codigo(codigo) == "precondicion"


@pytest.mark.parametrize("codigo", CODIGOS_PASARELA_RECHAZO)
def test_f012_r33_los_codigos_de_rechazo_se_clasifican_como_tales(codigo):
    """R33 · la pasarela rechaza la petición, sin escribir nada → 409."""
    assert clasificar_codigo(codigo) == "rechazo"


def test_f012_r34_un_codigo_que_no_esta_en_la_lista_es_desconocido():
    """R34 · lista cerrada: lo que no está no se trata «como si fuera» nada.

    Tratarlo como rechazo daría un 409 que promete que el ERP está intacto, y
    eso no se sabe.
    """
    assert clasificar_codigo("codigo_que_nadie_ha_declarado") == "desconocido"


def test_f012_r34_la_ausencia_de_codigo_tambien_es_desconocido():
    assert clasificar_codigo(None) == "desconocido"
    assert clasificar_codigo("") == "desconocido"


def test_f012_las_tres_familias_de_codigos_no_se_solapan():
    """Un código en dos familias daría dos códigos HTTP según el orden.

    Es el tipo de error que solo se ve el día que la pasarela lo devuelve.
    """
    todas = (
        set(CODIGOS_PASARELA_REINTENTABLES)
        | set(CODIGOS_PASARELA_PRECONDICION)
        | set(CODIGOS_PASARELA_RECHAZO)
    )

    assert len(todas) == (
        len(CODIGOS_PASARELA_REINTENTABLES)
        + len(CODIGOS_PASARELA_PRECONDICION)
        + len(CODIGOS_PASARELA_RECHAZO)
    )
    assert len(todas) == 12


def test_f012_las_tres_familias_son_las_doce_de_la_pasarela():
    """La lista cerrada de `azure-apps/sigrid_api.md` §8.8, sin inventar nada.

    Si la pasarela añadiera un código, este test se cae y obliga a decidir qué
    se hace con él en vez de dejarlo caer en «desconocido» sin que nadie mire.
    """
    todas = set(CODIGOS_PASARELA_REINTENTABLES) | set(
        CODIGOS_PASARELA_PRECONDICION
    ) | set(CODIGOS_PASARELA_RECHAZO)

    assert todas == {
        "escritura_documental_deshabilitada",
        "base_de_datos_no_permitida",
        "concepto_no_encontrado",
        "tipo_de_concepto_no_coincide",
        "clase_de_grafico_no_permitida",
        "usuario_no_valido",
        "fichero_vacio",
        "tipo_de_fichero_no_permitido",
        "tamano_excedido",
        "sha256_no_coincide",
        "colision_de_clave",
        "filas_afectadas_inesperadas",
    }


# --------------------------------------------------------------------------
# R53 · control negativo: el contenido del PDF no sale por ningún texto
# --------------------------------------------------------------------------


def test_f012_r53_el_repr_de_la_peticion_no_lleva_ni_un_byte_del_pdf():
    """R53 · `contenido` con `repr=False`, y esto es lo que lo comprueba.

    Dentro de ese PDF va el DNI manuscrito del cliente. Un `repr` que lo
    volcara acabaría en un log, en la traza de una excepción o en un mensaje
    de error — tres sitios que sobreviven al parte.
    """
    peticion = _peticion()

    assert "sintetico para el test" not in repr(peticion)
    assert "%PDF" not in repr(peticion)
    assert "sintetico para el test" not in str(peticion)
    assert "%PDF" not in str(peticion)


def test_f012_r53_el_repr_si_dice_lo_que_hace_falta_para_operar():
    """La otra mitad del control: un `repr` mudo no vale.

    Sin esto, un `repr` vacío pasaría el test de arriba y dejaría sin poder
    depurar la única petición que escribe en el ERP.
    """
    texto = repr(_peticion())

    assert "PARTE FIRMADO" in texto
    assert hashlib.sha256(PDF).hexdigest() in texto


def test_f012_r53_el_contenido_sigue_estando_para_quien_lo_necesita():
    """`repr=False` esconde el campo del texto, **no lo borra**.

    El adaptador tiene que poder codificarlo en base64: si esto fallara, el
    gráfico viajaría vacío.
    """
    assert _peticion().contenido == PDF
