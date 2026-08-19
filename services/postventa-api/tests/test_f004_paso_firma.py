# services/postventa-api/tests/test_f004_paso_firma.py
"""Tests del paso que lee la firma del parte (R2, R3, y la mitad de R23).

Todo contra `ExtractorFalso`: aquí no hay proveedor, ni SDK, ni red. Este paso
es el gemelo pequeño de `paso_extraccion` —mismo puerto, mismo tope de tamaño,
mismo saneo de confianza—, y lo único propio que hace es traducir **un** campo
de texto a la enumeración del dominio.

Esa traducción es donde vive el fallo caro de la feature: dar por `humana` lo
que el modelo no supo decir. Por eso casi todos los tests de aquí empujan en la
misma dirección: cualquier cosa rara acaba en `ilegible` **y con aviso**, para
que quien revise el parte sepa que hubo algo raro.
"""

from __future__ import annotations

import pytest
from application.pipelines import paso_extraccion as modulo_extraccion
from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_firma import MIME_PDF, paso_firma
from domain.models.errores import ParteDemasiadoGrande
from domain.models.extraccion import CampoBruto
from domain.models.firma import ClasificacionFirma
from domain.models.remesa import ModoDeteccion, ParteTroceado

from tests.utiles_ia import ExtractorFalso, prompt_de_prueba
from tests.utiles_validacion import respuesta_de_firma

#: La clave del prompt de firma que se le pide al repositorio.
CLAVE = "firma_parte_es"


class PromptsFalsos:
    """Doble de `RepositorioPromptsPort`: registra qué clave le piden."""

    def __init__(self) -> None:
        self.prompt = prompt_de_prueba(clave=CLAVE, schema="firma_cliente")
        self.claves_pedidas: list[str] = []

    def obtener(self, clave: str):
        self.claves_pedidas.append(clave)
        return self.prompt


def _parte(contenido: bytes = b"%PDF-1.4 parte de prueba") -> ParteTroceado:
    return ParteTroceado(
        hash="hash-del-parte",
        origen="remesa-de-prueba.pdf",
        paginas_origen=(7,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=contenido,
    )


def _ejecutar(respuesta=None, parte: ParteTroceado | None = None):
    """Ejecuta el paso con dobles y devuelve el contexto y los dobles."""
    extractor = ExtractorFalso(
        respuesta if respuesta is not None else respuesta_de_firma()
    )
    prompts = PromptsFalsos()
    contexto = paso_firma(
        ContextoParte(parte=parte if parte is not None else _parte()),
        extractor,
        prompts,
        CLAVE,
    )
    return contexto, extractor, prompts


@pytest.mark.parametrize(
    "etiqueta", ["humana", "marca_simple", "casilla_vacia", "ilegible"]
)
def test_f004_r2_el_paso_traduce_la_etiqueta_a_la_enumeracion(etiqueta):
    """R2 · lo que el modelo dice bien llega al dominio tal cual, y sin avisos."""
    contexto, _, _ = _ejecutar(respuesta_de_firma(etiqueta, 88))

    assert contexto.lectura_firma.clasificacion == ClasificacionFirma(etiqueta)
    assert contexto.lectura_firma.confianza_pct == 88
    assert contexto.lectura_firma.hash_parte == "hash-del-parte"
    assert contexto.lectura_firma.avisos == ()


@pytest.mark.parametrize("desconocida", ["garabato", "firma", "aspa", "válida"])
def test_f004_r2_una_etiqueta_desconocida_sale_ilegible_con_aviso(desconocida):
    """R2 · el paso no se cree lo que no entiende, y lo deja dicho.

    Sin el aviso, un modelo que empezara a devolver `"firma"` mandaría toda la
    remesa a revisión manual sin que nadie supiera por qué.
    """
    contexto, _, _ = _ejecutar(respuesta_de_firma(desconocida, 90))

    lectura = contexto.lectura_firma

    assert lectura.clasificacion == ClasificacionFirma.ILEGIBLE
    assert lectura.clasificacion != ClasificacionFirma.HUMANA
    assert len(lectura.avisos) == 1
    assert desconocida in lectura.avisos[0]
    assert lectura.avisos[0] in contexto.avisos


def test_f004_r2_si_el_modelo_no_devuelve_el_campo_sale_ilegible_con_aviso():
    """R2 · un campo que no llega es tan sospechoso como uno mal escrito."""
    contexto, _, _ = _ejecutar(respuesta_de_firma(campos={}))

    lectura = contexto.lectura_firma

    assert lectura.clasificacion == ClasificacionFirma.ILEGIBLE
    assert lectura.confianza_pct == 0
    assert len(lectura.avisos) == 1
    assert "clasificacion_firma" in lectura.avisos[0]


def test_f004_r2_un_campo_sobrante_se_descarta_con_aviso():
    """R2 · a la casilla se le pregunta una cosa; lo demás no se guarda.

    Si el modelo empieza a devolver el nombre del firmante —que el prompt no
    pide, y por una razón de datos personales—, se descarta y se avisa.
    """
    contexto, _, _ = _ejecutar(
        respuesta_de_firma(
            campos={
                "clasificacion_firma": CampoBruto(valor="humana", confianza_pct=90),
                "nombre_firmante": CampoBruto(valor="lo que sea", confianza_pct=90),
            }
        )
    )

    assert contexto.lectura_firma.clasificacion == ClasificacionFirma.HUMANA
    assert any("nombre_firmante" in aviso for aviso in contexto.lectura_firma.avisos)


@pytest.mark.parametrize(
    ("declarada", "saneada"),
    [
        (120, 100),
        (101, 100),
        (-5, 0),
        (-1, 0),
        ("no sé", 0),
        (None, 0),
        (True, 0),
        ("85.5", 0),
    ],
)
def test_f004_r3_la_confianza_de_la_firma_se_sanea_igual_que_la_extraccion(
    declarada, saneada
):
    """R3 · **la misma** regla que la extracción, y en la misma función.

    Dos copias de una regla numérica divergen: el día que alguien decida que
    un decimal se redondea, tiene que cambiar en un solo sitio.
    """
    contexto, _, _ = _ejecutar(respuesta_de_firma("humana", declarada))

    assert contexto.lectura_firma.confianza_pct == saneada
    assert len(contexto.lectura_firma.avisos) == 1


@pytest.mark.parametrize("buena", [0, 1, 50, 93, 100])
def test_f004_r3_una_confianza_correcta_no_deja_aviso(buena):
    """R3 · lo que ya viene bien no se toca ni se comenta."""
    contexto, _, _ = _ejecutar(respuesta_de_firma("humana", buena))

    assert contexto.lectura_firma.confianza_pct == buena
    assert contexto.lectura_firma.avisos == ()


def test_f004_r3_la_traza_dice_quien_leyo_la_casilla_y_con_que():
    """R3 · sin traza, revisar meses después por qué se leyó mal es imposible.

    Se reutiliza la traza de F-003 porque es exactamente el mismo dato; lo que
    cambia es la clave del prompt, y por eso está en la aserción.
    """
    contexto, _, prompts = _ejecutar()

    traza = contexto.lectura_firma.traza

    assert traza.proveedor == "gemini"
    assert traza.modelo == "gemini-3.7-flash"
    assert traza.prompt_key == CLAVE
    assert traza.version_prompt == prompts.prompt.version
    assert traza.huella_prompt == prompts.prompt.huella
    assert prompts.claves_pedidas == [CLAVE]


def test_f004_r3_al_modelo_se_le_manda_el_pdf_del_parte():
    """R3 · el mismo PDF que se extrae, sin rasterizar y sin recortar."""
    contexto, extractor, prompts = _ejecutar()

    llamada = extractor.llamadas[0]

    assert len(extractor.llamadas) == 1
    assert llamada["documento"] == contexto.parte.contenido
    assert llamada["mime"] == MIME_PDF
    assert llamada["prompt"] is prompts.prompt


def test_f004_r23_un_parte_demasiado_grande_no_llega_al_modelo(monkeypatch):
    """R23 · el tope es el de la extracción, **importado** y no duplicado.

    Y se comprueba antes de llamar: pagar una llamada para descubrir que el
    parte no cabía sería pagar por nada. El doble tiene que quedarse a cero.
    """
    monkeypatch.setattr(modulo_extraccion, "MAX_BYTES_PARTE", 10)
    extractor = ExtractorFalso(respuesta_de_firma())

    with pytest.raises(ParteDemasiadoGrande) as fallo:
        paso_firma(
            ContextoParte(parte=_parte(b"%PDF-1.4 esto ocupa mas de diez bytes")),
            extractor,
            PromptsFalsos(),
            CLAVE,
        )

    assert extractor.llamadas == []
    assert "%PDF" not in fallo.value.motivo


def test_f004_r23_el_tope_de_tamano_no_se_duplica_en_el_paso_de_firma():
    """R23 · una segunda constante con el mismo número se desincroniza sola.

    No se comprueba el valor —eso lo hace el test de arriba, que mueve el tope
    de la extracción y ve reaccionar a este paso—, sino que aquí no vive una
    copia con ese nombre.
    """
    from application.pipelines import paso_firma as modulo_firma

    assert "MAX_BYTES_PARTE" not in vars(modulo_firma)
