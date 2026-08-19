# services/postventa-api/tests/test_f003_paso_extraccion.py
"""Tests del paso de extracción del pipeline (R2, R2 bis, R4, R6, R7, R13, R16).

Todo contra `ExtractorFalso`: aquí no hay proveedor, ni SDK, ni red. Es el
sitio donde se prueba lo que de verdad decide el contrato —que el resultado
trae siempre las nueve claves, ni una menos ni una de más, y con la confianza
saneada—, y se prueba **sin depender de qué modelo esté de moda**.
"""

from __future__ import annotations

from dataclasses import fields

import pytest
from application.pipelines import paso_extraccion as modulo_paso
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_extraccion import MIME_PDF, paso_extraccion
from domain.models.errores import ParteDemasiadoGrande
from domain.models.extraccion import CAMPOS_DEL_PARTE, ExtraccionParte
from domain.models.remesa import ModoDeteccion, ParteTroceado

from tests.utiles_ia import ExtractorFalso, prompt_de_prueba, respuesta_simulada


class PromptsFalsos:
    """Doble de `RepositorioPromptsPort`: siempre el mismo prompt de mentira."""

    def __init__(self, prompt=None) -> None:
        self.prompt = prompt if prompt is not None else prompt_de_prueba()
        self.claves_pedidas: list[str] = []

    def obtener(self, clave: str):
        self.claves_pedidas.append(clave)
        return self.prompt


def _parte(
    contenido: bytes = b"%PDF-1.4 parte de prueba",
    paginas_origen: tuple[int, ...] = (7,),
    modo: ModoDeteccion = ModoDeteccion.UNA_PAGINA_POR_PARTE,
) -> ParteTroceado:
    """Un parte troceado de mentira, con la forma que produce F-002."""
    return ParteTroceado(
        hash="hash-del-parte",
        origen="remesa-de-prueba.pdf",
        paginas_origen=paginas_origen,
        modo_deteccion=modo,
        contenido=contenido,
    )


def _ejecutar(
    respuesta=None,
    parte: ParteTroceado | None = None,
    prompt_key: str = "parte_posventa_es",
) -> tuple[ContextoParte, ExtractorFalso, PromptsFalsos]:
    """Ejecuta el paso con dobles y devuelve el contexto y los dobles."""
    extractor = ExtractorFalso(
        respuesta if respuesta is not None else respuesta_simulada()
    )
    prompts = PromptsFalsos()
    contexto = paso_extraccion(
        ContextoParte(parte=parte if parte is not None else _parte()),
        extractor,
        prompts,
        prompt_key,
    )
    return contexto, extractor, prompts


def test_f003_r2_el_resultado_siempre_trae_las_nueve_claves():
    """R2 · las nueve claves declaradas, ni una menos, pase lo que pase.

    Se recorre `CAMPOS_DEL_PARTE` y **no** las claves que devolvió el modelo:
    por eso R2 (no puede faltar ninguna) y R7 (no puede sobrar ninguna) son la
    misma línea de código.
    """
    contexto, _, _ = _ejecutar(
        respuesta_simulada(omitir=["dni_cliente", "descripcion"])
    )

    assert tuple(contexto.extraccion.campos) == CAMPOS_DEL_PARTE
    assert len(CAMPOS_DEL_PARTE) == 9


def test_f003_r2_un_campo_ausente_sale_vacio_con_confianza_cero_y_aviso():
    """R2 · lo que el modelo no devuelve sale vacío, no desaparece.

    Un campo que faltara como clave rompería a F-004, y el papel real deja en
    blanco fecha, horas, nombre y DNI en casi toda la remesa.
    """
    contexto, _, _ = _ejecutar(respuesta_simulada(omitir=["fecha_servicio"]))

    campo = contexto.extraccion.campo("fecha_servicio")

    assert campo.valor is None
    assert campo.confianza_pct == 0
    assert campo.esta_vacio is True
    assert any("fecha_servicio" in aviso for aviso in contexto.extraccion.avisos)
    assert contexto.avisos == list(contexto.extraccion.avisos)


def test_f003_r1_una_clave_inventada_por_el_modelo_se_descarta_con_aviso():
    """R1 · lo que el modelo se invente no entra en el contrato.

    Y no se tira en silencio: deja aviso, porque un modelo que empieza a
    inventar campos es un modelo que hay que mirar.
    """
    contexto, _, _ = _ejecutar(respuesta_simulada(color_del_boligrafo=("azul", 99)))

    assert "color_del_boligrafo" not in contexto.extraccion.campos
    assert any("color_del_boligrafo" in aviso for aviso in contexto.extraccion.avisos)


@pytest.mark.parametrize(
    ("declarada", "saneada"),
    [(120, 100), (101, 100), (-5, 0), (100, 100), (0, 0)],
)
def test_f003_r4_confianza_fuera_de_rango_se_ajusta_con_aviso(declarada, saneada):
    """R4 · la confianza se ajusta al rango; el valor leído **no** se tira.

    Una confianza mal formada no invalida lo leído: lo hace sospechoso. Los
    casos `100` y `0` están aquí para fijar que los extremos son válidos y no
    dejan aviso.
    """
    contexto, _, _ = _ejecutar(respuesta_simulada(codigo_obra=("0677", declarada)))

    campo = contexto.extraccion.campo("codigo_obra")

    assert campo.valor == "0677"
    assert campo.confianza_pct == saneada
    hubo_aviso = any("codigo_obra" in aviso for aviso in contexto.extraccion.avisos)
    assert hubo_aviso is (declarada != saneada)


@pytest.mark.parametrize("basura", ["no sé", None, "", [95], {"pct": 95}, True])
def test_f003_r4_confianza_no_numerica_pasa_a_cero_con_aviso(basura):
    """R4 · lo que no es un entero es confianza cero, y se dice.

    `True` está en la lista a propósito: en Python es un `int` y colaría como
    confianza 1 si el saneo se escribiera con un `isinstance(valor, int)`
    descuidado.
    """
    contexto, _, _ = _ejecutar(
        respuesta_simulada(observaciones=("Falta rematar", basura))
    )

    campo = contexto.extraccion.campo("observaciones")

    assert campo.valor == "Falta rematar"
    assert campo.confianza_pct == 0
    assert any("observaciones" in aviso for aviso in contexto.extraccion.avisos)


@pytest.mark.parametrize(("texto", "esperada"), [("85", 85), (" 85 ", 85), ("85.0", 0)])
def test_f003_r4_una_confianza_escrita_como_texto_se_entiende(texto, esperada):
    """R4 · `"85"` es 85; `"85.0"` no es un entero y se va a cero.

    Los modelos devuelven el número como texto más a menudo de lo que
    reconocen, y tirar por eso una lectura buena sería absurdo. Lo que no se
    hace es adivinar: un decimal no es lo que declara el schema.
    """
    contexto, _, _ = _ejecutar(respuesta_simulada(unidad=("Villa 5", texto)))

    assert contexto.extraccion.campo("unidad").confianza_pct == esperada


def test_f003_r6_el_resultado_trae_traza_y_hash_del_parte():
    """R6 · con qué se leyó y a qué parte corresponde.

    Sin esto, revisar meses después por qué un parte se leyó mal es imposible.
    La huella (R10) va aquí para que un cambio de redacción del prompt sea
    detectable aunque nadie suba la versión.
    """
    prompt = prompt_de_prueba()
    contexto, _, prompts = _ejecutar()

    traza = contexto.extraccion.traza

    assert contexto.extraccion.hash_parte == "hash-del-parte"
    assert traza.proveedor == "gemini"
    assert traza.modelo == "gemini-3.7-flash"
    assert traza.prompt_key == "parte_posventa_es"
    assert traza.version_prompt == prompt.version
    assert traza.huella_prompt == prompt.huella
    assert prompts.claves_pedidas == ["parte_posventa_es"]


def test_f003_r7_el_resultado_no_trae_veredicto_ni_firma_ni_rutas():
    """R7 · el límite de alcance de F-003, con un test que lo vigila.

    Ni veredicto de validación (F-004), ni nombre de fichero o ruta de
    SharePoint (F-006), ni identificador de base de datos (F-005), ni estado
    de Sigrid (F-008/F-009). Si alguien añade aquí una de esas claves, este
    test lo para.
    """
    contexto, _, _ = _ejecutar(
        respuesta_simulada(
            veredicto=("apto", 99),
            firma_valida=("sí", 88),
            nombre_fichero=("0677 - RS26.08 - 0123 PARTE FIRMADO.pdf", 90),
        )
    )

    assert set(contexto.extraccion.campos) == set(CAMPOS_DEL_PARTE)
    assert {campo.name for campo in fields(ExtraccionParte)} == {
        "hash_parte",
        "campos",
        "traza",
        "avisos",
    }
    # El contexto sí crece feature a feature, y eso es lo que se diseñó: F-004
    # le añadió `lectura_firma` y `validacion`, y F-006 le añade `archivo`
    # (`specs/F-006-sharepoint/design.md` §3.2), que es la `TrazaArchivo` de
    # F-005 —una entidad de dominio ya existente—, no una ruta ni un
    # identificador sueltos.
    #
    # Lo que este test sigue impidiendo es exactamente lo de antes: que
    # aparezcan aquí una ruta de SharePoint en crudo, un identificador de base
    # de datos (F-005) o el estado de Sigrid (F-008/F-009). Quien añada uno
    # tiene que pasar por esta línea, y ese es todo el propósito del test.
    assert {campo.name for campo in fields(ContextoParte)} == {
        "parte",
        "extraccion",
        "lectura_firma",
        "validacion",
        "archivo",
        "avisos",
    }


def test_f003_r13_el_paso_funciona_con_un_doble_del_puerto():
    """R13 · el paso habla con `ExtractorPort`, no con un proveedor.

    Se demuestra ejecutándolo entero con un doble: si el paso supiera de
    Gemini, esto no podría existir. Es lo que permite cambiar de proveedor por
    configuración sin tocar el pipeline (criterio `acceptance` 1).
    """
    contexto, extractor, _ = _ejecutar()

    assert len(extractor.llamadas) == 1
    llamada = extractor.llamadas[0]
    assert llamada["documento"] == b"%PDF-1.4 parte de prueba"
    assert llamada["mime"] == MIME_PDF
    assert llamada["prompt"].clave == "parte_posventa_es"
    assert contexto.extraccion.campo("codigo_obra").valor == "0677"


def test_f003_r16_parte_demasiado_grande_no_llama_al_modelo(monkeypatch):
    """R16 · pasarse del tamaño se rechaza **antes** de gastar una llamada.

    Lo que de verdad se comprueba es la segunda mitad: que el doble no recibe
    **ninguna** llamada. Rechazarlo después de llamar costaría dinero y
    tiempo, y sería un 502 en vez del 413 que le corresponde.
    """
    monkeypatch.setattr(modulo_paso, "MAX_BYTES_PARTE", 10)
    extractor = ExtractorFalso()

    with pytest.raises(ParteDemasiadoGrande) as fallo:
        paso_extraccion(
            ContextoParte(parte=_parte(contenido=b"x" * 11)),
            extractor,
            PromptsFalsos(),
            "parte_posventa_es",
        )

    assert extractor.llamadas == []
    assert "10" in fallo.value.motivo


def test_f003_r16_el_tope_declarado_son_quince_megas():
    """R16 · el tope es una decisión, no un número que se pueda mover solo.

    Un parte troceado son 1–2 páginas escaneadas: quince megas es holgado para
    eso y ajustado para que no pase por aquí una remesa entera por error.
    """
    assert modulo_paso.MAX_BYTES_PARTE == 15 * 1024 * 1024


def test_f003_r16_un_parte_que_ocupa_justo_el_tope_si_se_procesa(monkeypatch):
    """R16 · el límite es **hasta** el tope, no antes.

    El caso frontera importa: con `>=` en vez de `>`, un parte que ocupara
    exactamente el máximo se rechazaría con un 413 sin que nadie entendiera
    por qué, y el mensaje diría que se pasa de un límite que no se pasa.
    """
    monkeypatch.setattr(modulo_paso, "MAX_BYTES_PARTE", 10)
    extractor = ExtractorFalso()

    contexto = paso_extraccion(
        ContextoParte(parte=_parte(contenido=b"x" * 10)),
        extractor,
        PromptsFalsos(),
        "parte_posventa_es",
    )

    assert len(extractor.llamadas) == 1
    assert contexto.extraccion is not None


def test_f003_r16_el_mensaje_del_rechazo_no_lleva_el_contenido_del_parte(monkeypatch):
    """R16 · el motivo habla de tamaños, no del parte: lleva DNI (riesgo 4)."""
    monkeypatch.setattr(modulo_paso, "MAX_BYTES_PARTE", 10)

    with pytest.raises(ParteDemasiadoGrande) as fallo:
        paso_extraccion(
            ContextoParte(parte=_parte(contenido=b"DNI 00000000T" * 3)),
            ExtractorFalso(),
            PromptsFalsos(),
            "parte_posventa_es",
        )

    assert "00000000T" not in fallo.value.motivo


def test_f003_r2bis_la_extraccion_no_reagrupa_paginas():
    """R2 bis · F-003 **lee** el número de página; no une hojas.

    Un parte cuya segunda hoja llegó suelta se lee como `numero_pagina = "2"`,
    y eso es todo lo que hace F-003: el parte troceado sale del paso **igual
    que entró** —mismas páginas de origen, mismo modo de detección, mismo
    contenido—. Reagrupar es **F-014**, y este test es el que impide que
    alguien empiece a hacerla aquí «ya que estamos».
    """
    parte = _parte(paginas_origen=(7,), modo=ModoDeteccion.UNA_PAGINA_POR_PARTE)
    extractor = ExtractorFalso(respuesta_simulada(numero_pagina=("2", 98)))

    contexto = paso_extraccion(
        ContextoParte(parte=parte), extractor, PromptsFalsos(), "parte_posventa_es"
    )

    assert contexto.extraccion.campo("numero_pagina").valor == "2"
    assert contexto.parte is parte
    assert contexto.parte.paginas_origen == (7,)
    assert contexto.parte.modo_deteccion is ModoDeteccion.UNA_PAGINA_POR_PARTE
    assert contexto.parte.contenido == b"%PDF-1.4 parte de prueba"
    assert extractor.llamadas[0]["documento"] == parte.contenido
