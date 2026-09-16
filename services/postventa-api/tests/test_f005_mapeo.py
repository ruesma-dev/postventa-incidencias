# services/postventa-api/tests/test_f005_mapeo.py
"""Del dominio a las columnas y de vuelta (F-005, T15): R18, R19, R20, R21.

Lo que se prueba aquí es que **no se pierde ni se inventa nada** entre lo que
leyó F-003, lo que decidió F-004 y lo que acaba en la base.

Todo el material es inventado: sale de `tests/utiles_validacion.py`, que a su
vez lo saca de `tests/utiles_ia.py`. Ni un dato de un parte real.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from domain.models.extraccion import CAMPOS_DEL_PARTE
from domain.models.firma import ClasificacionFirma
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    Motivo,
    Veredicto,
    validar_parte,
)

from infrastructure.persistencia import mapeo
from infrastructure.persistencia.mapeo import (
    columnas_de_campos,
    fila_a_entrada_cola,
    fila_a_preferencias,
    json_de_avisos,
    json_de_motivos,
    valores_de_campos,
    valores_de_traza_ia,
    valores_de_validacion,
)
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

#: Instante inventado, con zona.
AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

#: Las 18 columnas, **escritas a mano**. Es el contrato que tiene que existir
#: en el DDL: si el mapeo dejara de producirlas, no habría dónde guardar el
#: parte, y un test que las leyera de `columnas_de_campos()` no lo notaría.
COLUMNAS_ESPERADAS = (
    "promocion",
    "promocion_confianza_pct",
    "codigo_obra",
    "codigo_obra_confianza_pct",
    "unidad",
    "unidad_confianza_pct",
    "numero_incidencia",
    "numero_incidencia_confianza_pct",
    "fecha_servicio",
    "fecha_servicio_confianza_pct",
    "descripcion",
    "descripcion_confianza_pct",
    "dni_cliente",
    "dni_cliente_confianza_pct",
    "observaciones",
    "observaciones_confianza_pct",
    "numero_pagina",
    "numero_pagina_confianza_pct",
)


def test_f005_r18_las_dieciocho_columnas_son_las_del_contrato():
    """R18 · nueve campos, cada uno con su confianza justo detrás."""
    assert columnas_de_campos() == COLUMNAS_ESPERADAS
    assert len(COLUMNAS_ESPERADAS) == 2 * len(CAMPOS_DEL_PARTE)


def test_f005_r18_las_columnas_se_derivan_del_contrato_y_no_de_una_lista(
    monkeypatch,
):
    """R18 · un décimo campo en el contrato aparece solo en el mapeo.

    Es lo que hace que «añadir un campo» rompa **la suite** —el DDL no tendrá
    esa columna— en vez de romper producción en silencio. Si
    `columnas_de_campos` fuera una lista escrita a mano, este test la cazaría.
    """
    monkeypatch.setattr(
        mapeo, "CAMPOS_DEL_PARTE", (*CAMPOS_DEL_PARTE, "campo_inventado")
    )

    columnas = columnas_de_campos()

    assert len(columnas) == 20
    assert columnas[-2:] == ("campo_inventado", "campo_inventado_confianza_pct")


def test_f005_r18_los_valores_van_en_el_orden_de_las_columnas():
    """R18 · valor y confianza de cada campo, emparejados sin desplazarse.

    Un desplazamiento de una posición guardaría la confianza de la promoción
    en el código de obra: pasa desapercibido y corrompe todo lo guardado.
    """
    extraccion = extraccion_de_ejemplo()

    valores = valores_de_campos(extraccion)

    assert len(valores) == len(COLUMNAS_ESPERADAS)
    for indice, columna in enumerate(COLUMNAS_ESPERADAS):
        if columna.endswith("_confianza_pct"):
            campo = columna.removesuffix("_confianza_pct")
            assert valores[indice] == extraccion.campo(campo).confianza_pct, columna
        else:
            assert valores[indice] == extraccion.campo(columna).valor, columna


def test_f005_r18_un_campo_vacio_se_guarda_como_vacio_y_no_se_pierde():
    """Un campo en blanco es un dato, no un hueco: se guarda tal cual.

    El papel real deja en blanco fecha, horas, nombre y DNI en casi toda la
    remesa. Convertir eso en «no lo sé» sería inventar.
    """
    extraccion = extraccion_de_ejemplo(fecha_servicio=None)

    valores = valores_de_campos(extraccion)
    posicion = COLUMNAS_ESPERADAS.index("fecha_servicio")

    assert valores[posicion] is None
    assert valores[posicion + 1] == 0


def test_f005_r19_la_traza_de_ia_va_entera():
    """R19 · proveedor, modelo, clave del prompt, versión y huella."""
    extraccion = extraccion_de_ejemplo()

    traza = valores_de_traza_ia(extraccion)

    assert traza == (
        extraccion.traza.proveedor,
        extraccion.traza.modelo,
        extraccion.traza.prompt_key,
        extraccion.traza.version_prompt,
        extraccion.traza.huella_prompt,
    )
    assert len(traza) == 5


def test_f005_r20_la_validacion_se_mapea_con_sus_motivos_en_orden():
    """R20 · veredicto, destino, firma y **todos** los motivos, en su orden."""
    extraccion = extraccion_de_ejemplo()
    resultado = validar_parte(
        extraccion, lectura_de_firma(ClasificacionFirma.CASILLA_VACIA)
    )

    valores = valores_de_validacion(resultado, AHORA_INVENTADO)

    assert valores[0] == resultado.hash_parte
    assert valores[1] == resultado.veredicto.value
    assert valores[2] == resultado.destino.value
    assert valores[3] == resultado.clasificacion_firma.value
    assert valores[6] == AHORA_INVENTADO

    guardados = json.loads(valores[4])
    assert [motivo["codigo"] for motivo in guardados] == [
        motivo.codigo.value for motivo in resultado.motivos
    ]
    assert [motivo["texto"] for motivo in guardados] == [
        motivo.texto for motivo in resultado.motivos
    ]


def test_f005_r21_la_validacion_no_copia_las_observaciones():
    """R21, R39 · la transcripción del cliente vive **solo** en `partes`.

    `ResultadoValidacion` la transporta, y esta es exactamente la línea donde
    podría colarse una segunda copia de texto manuscrito de un cliente en una
    base compartida. No se cuela.
    """
    extraccion = extraccion_de_ejemplo(
        observaciones="texto manuscrito inventado del cliente"
    )
    resultado = validar_parte(extraccion, lectura_de_firma(ClasificacionFirma.HUMANA))

    valores = valores_de_validacion(resultado, AHORA_INVENTADO)

    assert resultado.observaciones == "texto manuscrito inventado del cliente"
    assert not any(
        "texto manuscrito inventado del cliente" in str(valor) for valor in valores
    )


def test_f005_r20_los_avisos_viajan_como_json():
    """Los avisos se guardan como lista JSON, no como un texto pegado."""
    assert json.loads(json_de_avisos(("uno inventado", "otro inventado"))) == [
        "uno inventado",
        "otro inventado",
    ]
    assert json.loads(json_de_avisos(())) == []


def test_f005_r20_los_avisos_tambien_conservan_los_acentos():
    """Lo mismo que los motivos, y por la misma razón: los lee una persona.

    `json.loads` devuelve el mismo texto se escapen los acentos o no, así que
    el test de arriba —que compara la lista deserializada— no distingue un
    `ensure_ascii=False` de un `ensure_ascii=True`. Hay que mirar el **texto**
    que se guarda: lo que acaba en la columna `jsonb` y lo que ve quien
    consulta la base a mano.
    """
    texto = json_de_avisos(("firma sin resolución suficiente", "página añadida"))

    assert "\\u" not in texto
    assert "resolución" in texto
    assert "página añadida" in texto


# --- La cota de los avisos (O1, decidida por el humano el 2026-08-19) --------
#
# Un aviso es un **diagnóstico**, no un almacén. El de etiqueta desconocida
# (`paso_firma.py`) mete dentro el valor crudo que devolvió el modelo, y sin
# cota ese texto libre entraba verbatim en la columna `avisos` de una base
# compartida. Se recorta, con el mismo patrón que `ddl.py`.
#
# El 240 va escrito aquí a mano y NO importado de `mapeo.py`: un test que
# leyera la constante se movería con ella y dejaría de vigilar el borde. Es la
# misma razón por la que `test_f005_ddl_seguro.py` escribe su 80.

#: Un aviso de **240 caracteres exactos**, contados a mano: el último que se
#: guarda entero.
AVISO_DE_240 = "aviso inventado: " + "x" * 223

#: El mismo, con un carácter más: el primero que **sí** se recorta.
AVISO_DE_241 = "aviso inventado: " + "x" * 224

#: El aviso legítimo más largo que hoy emite el pipeline, copiado literalmente
#: de `application/pipelines/paso_firma.py` con el valor del modelo vacío. Es
#: la razón del número: la cota tiene que dejarlo pasar entero, y con margen
#: de sobra para la parte variable (el valor, o la ruta de un PDF dentro de un
#: ZIP). Por eso no vale el 80 de `ddl.py`: mutilaría este mismo aviso.
AVISO_LEGITIMO_MAS_LARGO = (
    "clasificacion_firma: el modelo devolvió '', que no es una de las cuatro "
    "etiquetas, y se ha tomado como ilegible"
)


def test_f005_r20_un_aviso_de_240_caracteres_se_guarda_entero():
    """En el borde, el aviso entra completo y sin marca de recorte.

    La cota existe para que el modelo no vuelque texto libre en la base, no
    para esconder el diagnóstico: lo que cabe, se guarda.
    """
    assert len(AVISO_DE_240) == 240

    guardado = json.loads(json_de_avisos((AVISO_DE_240,)))

    assert guardado == [AVISO_DE_240]
    assert "…" not in guardado[0]


def test_f005_r20_un_aviso_mas_largo_se_recorta_a_240_y_lo_dice():
    """Pasado el borde se recorta, y los puntos suspensivos avisan de que hay más.

    Sin la señal, quien lea la cola creería estar viendo el aviso entero y
    buscaría la causa donde no está.
    """
    assert len(AVISO_DE_241) == 241

    guardado = json.loads(json_de_avisos((AVISO_DE_241,)))

    assert guardado == [AVISO_DE_241[:240] + "…"]
    assert AVISO_DE_241 not in guardado[0]


def test_f005_r20_el_aviso_legitimo_mas_largo_del_pipeline_no_se_mutila():
    """La cota está elegida para no cortar un aviso que el pipeline sí emite.

    Este es el texto fijo más largo de todos los avisos del proceso, y aún le
    quedan más de cien caracteres libres para su parte variable. Si alguien
    bajara la cota hasta rozarlo, este test lo dice.
    """
    assert len(AVISO_LEGITIMO_MAS_LARGO) < 240

    guardado = json.loads(json_de_avisos((AVISO_LEGITIMO_MAS_LARGO,)))

    assert guardado == [AVISO_LEGITIMO_MAS_LARGO]


def test_f005_r20_la_cota_se_aplica_a_cada_aviso_y_no_al_conjunto():
    """El recorte es por aviso.

    Si la cota se aplicara al JSON entero, dos avisos cortos y legítimos se
    perderían por culpa de un tercero largo. Se recorta el que se pasa, y solo
    ese.
    """
    guardado = json.loads(
        json_de_avisos(("corto inventado", AVISO_DE_241, "otro corto inventado"))
    )

    assert guardado[0] == "corto inventado"
    assert guardado[1] == AVISO_DE_241[:240] + "…"
    assert guardado[2] == "otro corto inventado"


def test_f005_r20_los_motivos_vacios_son_una_lista_vacia():
    """Un parte apto no tiene motivos, y eso es `[]`, no `null`."""
    assert json.loads(json_de_motivos(())) == []


def test_f005_r20_el_json_conserva_los_acentos():
    """Los textos de los motivos son para personas: no se escapan a `\\uXXXX`."""
    extraccion = extraccion_de_ejemplo(codigo_obra=None)
    resultado = validar_parte(extraccion, lectura_de_firma(ClasificacionFirma.HUMANA))

    texto = json_de_motivos(resultado.motivos)

    assert "\\u" not in texto
    assert "código" in texto


def test_f005_r22_una_fila_de_la_cola_vuelve_al_dominio():
    """R22 · ida y vuelta: la fila que devuelve la consulta es una `EntradaCola`."""
    fila = (
        "hash-inventado",
        "0000",
        "XX00.00 - 0000",
        "texto de ejemplo inventado",
        82,
        "humana",
        [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}],
        AHORA_INVENTADO,
    )

    entrada = fila_a_entrada_cola(fila)

    assert entrada.hash_parte == "hash-inventado"
    assert entrada.codigo_obra == "0000"
    assert entrada.numero_incidencia == "XX00.00 - 0000"
    assert entrada.observaciones == "texto de ejemplo inventado"
    assert entrada.confianza_observaciones == 82
    assert entrada.clasificacion_firma == "humana"
    assert entrada.motivos == (("observaciones_manuscritas", "texto inventado"),)
    assert entrada.validado_at_utc == AHORA_INVENTADO


def test_f005_r22_los_motivos_valen_ya_vengan_como_json_o_como_texto():
    """El driver puede devolver el `jsonb` deserializado o en texto.

    Que la cola humana se quedara sin motivos por un detalle de adaptación
    sería un fallo caro y silencioso: quien decide se quedaría sin saber por
    qué está mirando ese parte.
    """
    crudo = json.dumps(
        [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}]
    )
    fila = (
        "hash-inventado",
        None,
        None,
        None,
        0,
        "humana",
        crudo,
        AHORA_INVENTADO,
    )

    assert fila_a_entrada_cola(fila).motivos == (
        ("observaciones_manuscritas", "texto inventado"),
    )


def test_f005_r22_una_cola_sin_motivos_no_revienta():
    """Un `NULL` en la columna de motivos se lee como «ninguno»."""
    fila = ("hash-inventado", None, None, None, 0, "humana", None, AHORA_INVENTADO)

    assert fila_a_entrada_cola(fila).motivos == ()


def test_f005_r27_una_fila_de_preferencias_vuelve_al_dominio():
    """La preferencia guardada se lee como `PreferenciasUsuario`."""
    preferencias = fila_a_preferencias(("oid-inventado-0000", True, AHORA_INVENTADO))

    assert preferencias.usuario_oid == "oid-inventado-0000"
    assert preferencias.auto_cierre is True
    assert preferencias.actualizado_at_utc == AHORA_INVENTADO


# --------------------------------------------------------------------------
# F-030 · el veredicto guardado, de vuelta al dominio
# --------------------------------------------------------------------------

#: Una fila de `select_veredicto_y_cierre` con veredicto y sin traza de cierre.
#:
#: Las diez columnas en el orden de `design.md` §3 de F-030: cinco de
#: `validaciones`, cuatro de `partes` y el estado de `cierres`.
FILA_CON_VEREDICTO = (
    "no_apto",
    "cola_validacion_humana",
    "humana",
    [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}],
    ["un aviso inventado"],
    "texto de ejemplo inventado",
    82,
    "0000",
    "XX00.00 - 0000",
    None,
)


def test_f030_r9_sin_fila_de_validacion_el_veredicto_vuelve_a_none():
    """R8, R9 · «no hay veredicto» se distingue por el **veredicto**, no por el hash.

    La consulta se ancla en `postventa.partes`, así que un parte que exista
    pero al que nadie haya validado devuelve fila con las cinco columnas de
    `validaciones` a `NULL`. Recomponer ahí un `ResultadoValidacion` con huecos
    sería inventarse un veredicto que nadie emitió —que es exactamente el
    defecto que F-030 viene a quitar— y además taparía el error propio de «no
    consta que este parte haya pasado la validación», que se arregla
    revalidando y no decidiendo.

    El estado de cierre **sí vuelve**, y eso importa: un parte cerrado sin
    fila de validación tiene que seguir dando `cerrado`, porque ese hecho es
    del ERP y gana a todo.
    """
    fila = (None, None, None, None, None, None, 0, None, None, "cerrado")

    validacion, estado_cierre = mapeo.fila_a_validacion_y_cierre(
        fila, hash_parte="hash-inventado"
    )

    assert validacion is None
    assert estado_cierre == "cerrado"


def test_f030_r9_sin_ninguna_fila_no_hay_ni_veredicto_ni_cierre():
    """R9 · un parte del que no consta ni la ficha se lee como los dos huecos.

    Lo que no puede pasar es que el camino de «no consta nada» sea distinto del
    de «no consta la validación»: los dos acaban en el mismo error y ninguno es
    un fallo de base de datos.
    """
    fila = (None,) * 10

    assert mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado") == (
        None,
        None,
    )


def test_f030_r10_el_veredicto_guardado_vuelve_entero():
    """Las diez columnas se leen cada una en su sitio, y el `hash` no sale de la fila.

    El orden es lo único que sostiene esta lectura: si alguien añadiera una
    columna al `SELECT` sin tocar aquí, el destino se leería en el sitio del
    veredicto. Por eso este caso afirma **campo a campo** y no solo la huella.
    """
    validacion, estado_cierre = mapeo.fila_a_validacion_y_cierre(
        FILA_CON_VEREDICTO, hash_parte="hash-inventado"
    )

    assert validacion.hash_parte == "hash-inventado"
    assert validacion.veredicto is Veredicto.NO_APTO
    assert validacion.destino is Destino.COLA_VALIDACION_HUMANA
    assert validacion.clasificacion_firma is ClasificacionFirma.HUMANA
    assert validacion.motivos == (
        Motivo(codigo=CodigoMotivo.OBSERVACIONES_MANUSCRITAS, texto="texto inventado"),
    )
    assert validacion.avisos == ("un aviso inventado",)
    assert validacion.observaciones == "texto de ejemplo inventado"
    assert validacion.confianza_observaciones == 82
    assert validacion.codigo_obra == "0000"
    assert validacion.numero_incidencia == "XX00.00 - 0000"
    assert estado_cierre is None


def test_f030_r10_los_motivos_y_los_avisos_valen_como_json_o_como_texto():
    """El gemelo de R22: el driver puede deserializar el `jsonb` o no.

    Si los motivos se perdieran por un detalle de adaptación, la huella
    recompuesta dejaría de ser la del veredicto guardado y **caducaría la
    aprobación de una persona** sin que nadie lo notara: el mismo síntoma que
    la regresión que F-030 arregla, por otro camino.
    """
    fila = (
        FILA_CON_VEREDICTO[:3]
        + (
            json.dumps(
                [{"codigo": "observaciones_manuscritas", "texto": "texto inventado"}]
            ),
            json.dumps(["un aviso inventado"]),
        )
        + FILA_CON_VEREDICTO[5:]
    )

    validacion, _ = mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado")

    assert validacion.motivos == (
        Motivo(codigo=CodigoMotivo.OBSERVACIONES_MANUSCRITAS, texto="texto inventado"),
    )
    assert validacion.avisos == ("un aviso inventado",)


def test_f030_r10_un_veredicto_sin_motivos_ni_avisos_no_revienta():
    """Un `NULL` en las dos columnas `jsonb` es «ninguno», no un fallo.

    Es el caso del parte apto: ni motivos que explicar ni diagnósticos que
    emitir. Y las dos tuplas vacías son justo lo que necesita la cadena
    canónica de la huella para dar el mismo valor que el veredicto en memoria.
    """
    fila = FILA_CON_VEREDICTO[:3] + (None, None) + FILA_CON_VEREDICTO[5:]

    validacion, _ = mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado")

    assert validacion.motivos == ()
    assert validacion.avisos == ()


def test_f030_r10_los_dos_campos_decisivos_a_null_se_leen_como_vacios():
    """`NULL` en `codigo_obra` o en `numero_incidencia` es la cadena vacía.

    No es criterio: es el valor por defecto que ya declara
    `ResultadoValidacion`, y es lo que hace que la huella de un parte al que el
    modelo no le pudo leer el número coincida con la del veredicto que se
    emitió con `""`. Las **observaciones**, en cambio, se pasan tal cual
    vienen: normalizarlas aquí sería una segunda copia del criterio de
    `_normalizar`, que es de la huella y no se toca.
    """
    fila = FILA_CON_VEREDICTO[:5] + ("   ", 0, None, None, None)

    validacion, _ = mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado")

    assert validacion.codigo_obra == ""
    assert validacion.numero_incidencia == ""
    assert validacion.observaciones == "   "


@pytest.mark.parametrize(
    "posicion",
    [
        pytest.param(0, id="veredicto"),
        pytest.param(1, id="destino"),
        pytest.param(2, id="clasificacion_firma"),
    ],
)
def test_f030_r1_un_literal_que_el_dominio_no_conoce_revienta(posicion):
    """Un valor desconocido **rompe**, y no se degrada a nada.

    Pasaría si alguien ampliara un `CHECK` de `sql/04_validaciones.sql` sin
    ampliar el `Enum`. Traducirlo «como si fuera» otro haría que un destino
    desconocido se leyera como `archivo_y_cierre`, y con eso se abre la puerta
    que archiva un PDF con el DNI de un cliente y cierra una reclamación en el
    ERP de producción. Es el mismo trato que ya reciben `EstadoGrafico` y
    `EstadoParte`.
    """
    fila = (
        FILA_CON_VEREDICTO[:posicion]
        + ("valor_que_nadie_declaro",)
        + FILA_CON_VEREDICTO[posicion + 1 :]
    )

    with pytest.raises(ValueError, match="valor_que_nadie_declaro"):
        mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado")


def test_f030_r1_un_codigo_de_motivo_desconocido_tambien_revienta():
    """Y lo mismo con el código de un motivo, que viene dentro del `jsonb`.

    El `jsonb` **no tiene `CHECK`**, así que este es el sitio por donde podría
    entrar un código que el dominio no declara. Que reviente es lo correcto: un
    motivo que nadie sabe leer no puede acabar contando como uno que sí, porque
    los códigos de los motivos entran en la cadena canónica de la huella.
    """
    fila = (
        FILA_CON_VEREDICTO[:3]
        + ([{"codigo": "motivo_que_nadie_declaro", "texto": "texto inventado"}],)
        + FILA_CON_VEREDICTO[4:]
    )

    with pytest.raises(ValueError, match="motivo_que_nadie_declaro"):
        mapeo.fila_a_validacion_y_cierre(fila, hash_parte="hash-inventado")
