# services/postventa-api/tests/test_f019_documentacion.py
"""La documentación normativa dice lo que el código hace (F-019, R32, R33).

Dos documentos, y ninguno es decorativo:

- **`docs/ARCHITECTURE.md`** es normativo: el reviewer valida contra él y el
  próximo que toque el paso de archivo lo lee antes que el código. Si no
  cuenta la garantía de orden, alguien la quitará por «simplificar» y volverá
  el defecto 15 con el fichero subido y sin constancia.
- **`docs/INTEGRACION.md`** §8 es el documento que **viaja a `azure-apps/`**,
  el que se lee antes de una demostración a negocio. Una tabla que anuncia
  como pendiente algo que ya está desplegado gasta la credibilidad del resto.

Se lee el Markdown como texto, igual que `test_f010_integracion_expuesto.py`:
lo que se fija es lo que **está escrito**, porque es lo único que alguien va a
leer dentro de seis meses.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"


@pytest.fixture
def arquitectura() -> str:
    return ARQUITECTURA.read_text(encoding="utf-8")


@pytest.fixture
def paso_de_archivo(arquitectura: str) -> str:
    """El punto 6 del pipeline, hasta el 7."""
    hallado = re.search(
        r"^6\. \*\*Archivo\*\*(.*?)^7\. ", arquitectura, re.DOTALL | re.MULTILINE
    )
    assert hallado is not None, "no se encuentra el paso 6 del pipeline"
    return hallado.group(1)


@pytest.fixture
def seccion_ocho() -> str:
    """De «Qué exponemos nosotros» hasta la sección siguiente."""
    documento = INTEGRACION.read_text(encoding="utf-8")
    hallado = re.search(
        r"^## 8 · Qué exponemos nosotros$(.*?)^## ",
        documento,
        re.DOTALL | re.MULTILINE,
    )
    assert hallado is not None, "no se encuentra la sección 8"
    return hallado.group(1)


# --------------------------------------------------------------------------
# R33 · La arquitectura cuenta la garantía de orden
# --------------------------------------------------------------------------


def test_f019_r33_el_paso_de_archivo_dice_que_solo_se_archiva_lo_guardado(
    paso_de_archivo,
):
    """R33 · el requisito, escrito donde se lee antes de tocar el código."""
    assert "consta guardado" in paso_de_archivo


def test_f019_r33_el_paso_de_archivo_dice_con_que_mecanismo_se_garantiza(
    paso_de_archivo,
):
    """R33 · «solo se archiva lo guardado» sin decir **cómo** no sirve.

    Quien lea sólo la promesa la implementará con una consulta previa, que es
    justo lo que el diseño descarta: entre la consulta y la escritura cabe
    otro proceso, y una comprobación paralela puede divergir de la restricción
    real. Lo que hay que poder leer aquí son las tres piezas: la traza previa
    en `pendiente`, la clave ajena, y que se aborta **sin subir nada**.
    """
    assert "pendiente" in paso_de_archivo
    assert "clave ajena" in paso_de_archivo
    assert "409" in paso_de_archivo
    assert "sin llamar a nadie" in paso_de_archivo


def test_f019_r33_el_paso_de_archivo_dice_por_que_la_idempotencia_va_antes(
    paso_de_archivo,
):
    """R33 · el orden **entre** las dos capas también es requisito.

    Escribir la traza previa antes de la comprobación de idempotencia
    degradaría a `pendiente` un parte ya archivado, y `pendiente` no corta el
    reintento: el intento siguiente volvería a subir el fichero. Es el fallo
    exacto que alguien introduciría reordenando «para que quede más limpio».
    """
    assert "no corta el reintento" in paso_de_archivo


# --------------------------------------------------------------------------
# R32 · La sección 8 lista los endpoints nuevos con su efecto
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint", ("/api/remesa", "/api/parte", "/api/cola")
)
def test_f019_r32_la_seccion_ocho_lista_los_tres_endpoints_nuevos(
    seccion_ocho, endpoint
):
    """R32 · los tres, por su ruta."""
    assert endpoint in seccion_ocho


def test_f019_r32_la_seccion_ocho_dice_el_efecto_de_cada_uno(seccion_ocho):
    """R32 · «existe» no es un efecto. Qué escribe y qué devuelve, sí.

    La tabla existe para que alguien del ecosistema sepa **qué pasa** si llama
    a esto: dos escriben en el esquema propio y uno devuelve dato personal
    acumulado. Un listado de rutas sin efecto invita a probarlas.
    """
    assert "postventa.remesas" in seccion_ocho
    assert "postventa.partes" in seccion_ocho
    assert "dato personal acumulado" in seccion_ocho


def test_f019_r32_la_seccion_ocho_dice_que_no_dependen_de_la_ventana(
    seccion_ocho,
):
    """R32 + R34 · con la ventana cerrada **se guarda igual**, y hay que decirlo.

    Es la pregunta que hará la primera persona que mire el entorno desplegado,
    porque la ventana está cerrada casi siempre. Sin esta frase, la respuesta
    razonable es la equivocada: «entonces no se guarda nada».
    """
    assert "ARCHIVO_HABILITADO" in seccion_ocho
    assert "se guarda" in seccion_ocho


def test_f019_r32_la_seccion_ocho_dice_que_archivar_exige_el_parte_guardado(
    seccion_ocho,
):
    """R32 · el cambio de comportamiento de `/api/archivar`, dicho.

    Quien llame al endpoint sin guardar antes va a recibir un 409 donde antes
    recibía un 200 a medias. Es exactamente el tipo de cambio que hay que
    encontrar leyendo, no depurando.
    """
    assert "409" in seccion_ocho
    assert "conste guardado" in seccion_ocho


def test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints(seccion_ocho):
    """R32 · la cuenta también cambia, y decía «los seis».

    Un número que se queda atrás es la señal más barata de que el documento ya
    no se mantiene, y este es el que se copia a `azure-apps/`. Iba por seis
    antes de F-019, por nueve después, y por **diez** desde que F-009 añadió
    `POST /api/cerrar`. Cada vez ha habido que venir aquí, que es el punto.
    """
    assert "Los seis quedan en nivel" not in seccion_ocho
    assert "Los nueve quedan en nivel" not in seccion_ocho
    assert "Los diez quedan en nivel" in seccion_ocho
