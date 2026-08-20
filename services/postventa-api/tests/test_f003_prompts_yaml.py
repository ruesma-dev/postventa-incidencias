# services/postventa-api/tests/test_f003_prompts_yaml.py
"""Tests del repositorio de prompts en YAML (R8, R9, R10).

El prompt es lo único de esta feature que **ningún test unitario puede
juzgar**: que esté bien redactado solo se sabe llamando a un modelo de verdad
(T18, y de forma sistemática F-015). Lo que sí se puede exigir, y es lo que se
exige aquí, es que **se cargue de fuera del código**, que falle ruidosamente
si el fichero no sirve —antes de gastar una llamada— y que un cambio de
redacción deje huella aunque nadie suba la versión.

Los YAML de prueba los escribe cada test en su `tmp_path`: nada que mantener
en el repositorio y ningún test acoplado a la redacción de producción.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from domain.models.errores import PromptNoEncontrado
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml

#: Ruta del prompt de producción, relativa al directorio del servicio.
RUTA_DE_PRODUCCION = "config/prompts.yaml"

_YAML_MINIMO = """\
parte_posventa_es:
  version: "1"
  schema: parte_posventa
  system: |
    Eres un extractor de partes de prueba.
  task: |
    Extrae los campos del parte de prueba.
otro_prompt:
  version: "3"
  schema: otro_schema
  system: otro system
  task: otra task
"""


def _escribir(carpeta: Path, contenido: str, nombre: str = "prompts.yaml") -> Path:
    ruta = carpeta / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_f003_r8_el_prompt_se_carga_del_yaml(tmp_path):
    """R8 · del fichero salen `system`, `task`, `schema` y `version`."""
    repositorio = RepositorioPromptsYaml(_escribir(tmp_path, _YAML_MINIMO))

    prompt = repositorio.obtener("parte_posventa_es")

    assert prompt.clave == "parte_posventa_es"
    assert prompt.version == "1"
    assert prompt.schema == "parte_posventa"
    assert "extractor de partes de prueba" in prompt.system
    assert "Extrae los campos" in prompt.task
    assert prompt.huella


def test_f003_r8_el_prompt_de_produccion_se_carga_con_la_ruta_por_defecto():
    """R8 · el YAML que se despliega existe, es válido y trae la clave.

    La ruta se resuelve **relativa al directorio del servicio**, no al `cwd`:
    la Function App arranca desde otro sitio y un prompt que solo carga si
    ejecutas desde la carpeta correcta es un prompt que no carga.
    """
    prompt = RepositorioPromptsYaml(RUTA_DE_PRODUCCION).obtener("parte_posventa_es")

    assert prompt.schema == "parte_posventa"
    assert prompt.version
    assert prompt.system.strip()
    assert prompt.task.strip()


def test_f003_r9_yaml_inexistente_falla_nombrando_el_fichero(tmp_path):
    """R9 · sin fichero no hay prompt, y el error dice **cuál** falta.

    Falla al construir, no en mitad de una remesa: un `PromptSpec` vacío
    produciría veintidós llamadas caras y silenciosamente inútiles.
    """
    ruta = tmp_path / "no_existe.yaml"

    with pytest.raises(PromptNoEncontrado) as fallo:
        RepositorioPromptsYaml(ruta)

    assert "no_existe.yaml" in fallo.value.motivo


def test_f003_r9_una_raiz_que_no_es_mapping_falla(tmp_path):
    """R9 · una lista en la raíz no es un catálogo de prompts."""
    ruta = _escribir(tmp_path, "- esto es una lista\n- y no un mapping\n")

    with pytest.raises(PromptNoEncontrado) as fallo:
        RepositorioPromptsYaml(ruta)

    assert "prompts.yaml" in fallo.value.motivo


def test_f003_r9_clave_desconocida_falla_listando_las_disponibles(tmp_path):
    """R9 · pedir una clave que no está dice qué claves sí están.

    Sin la lista, corregir un `PROMPT_KEY` mal escrito obliga a abrir el
    fichero desplegado, que es justo lo que no se puede hacer en Azure.
    """
    repositorio = RepositorioPromptsYaml(_escribir(tmp_path, _YAML_MINIMO))

    with pytest.raises(PromptNoEncontrado) as fallo:
        repositorio.obtener("clave_que_no_existe")

    assert "clave_que_no_existe" in fallo.value.motivo
    assert "parte_posventa_es" in fallo.value.motivo
    assert "otro_prompt" in fallo.value.motivo


@pytest.mark.parametrize("ausente", ["system", "task", "schema", "version"])
def test_f003_r9_una_entrada_incompleta_falla_al_cargar(tmp_path, ausente):
    """R9 · o el prompt está entero, o no hay prompt.

    Se valida **al cargar** y no al pedirlo: si el YAML desplegado está roto,
    el servicio tiene que decirlo al arrancar, no la primera vez que alguien
    sube una remesa.
    """
    lineas = {
        "version": '  version: "1"',
        "schema": "  schema: parte_posventa",
        "system": "  system: un system cualquiera",
        "task": "  task: una task cualquiera",
    }
    del lineas[ausente]
    ruta = _escribir(tmp_path, "parte_posventa_es:\n" + "\n".join(lineas.values()))

    with pytest.raises(PromptNoEncontrado) as fallo:
        RepositorioPromptsYaml(ruta)

    assert ausente in fallo.value.motivo
    assert "parte_posventa_es" in fallo.value.motivo


def test_f003_r9_una_entrada_con_texto_en_blanco_tampoco_vale(tmp_path):
    """R9 · un `system` de espacios es un prompt vacío con buena presencia."""
    ruta = _escribir(
        tmp_path,
        'parte_posventa_es:\n  version: "1"\n  schema: s\n  system: "   "\n  task: t\n',
    )

    with pytest.raises(PromptNoEncontrado) as fallo:
        RepositorioPromptsYaml(ruta)

    assert "system" in fallo.value.motivo


def test_f003_r9_una_entrada_que_no_es_mapping_falla(tmp_path):
    """R9 · una clave cuyo valor es texto suelto no es un prompt.

    Es el YAML mal indentado de toda la vida: la entrada queda como cadena y
    no como bloque. Sin este control, el fallo saldría por un `AttributeError`
    ilegible en vez de por el error de dominio que dice qué clave está mal.
    """
    ruta = _escribir(tmp_path, "parte_posventa_es: esto no es un bloque\n")

    with pytest.raises(PromptNoEncontrado) as fallo:
        RepositorioPromptsYaml(ruta)

    assert "parte_posventa_es" in fallo.value.motivo


def test_f003_r10_la_huella_del_prompt_cambia_si_cambia_el_texto(tmp_path):
    """R10 · tocar una coma cambia la huella, aunque la versión no se toque.

    Es la mitad que no se olvida del versionado: la `version` declarada dice
    *qué querías*, la huella dice *qué había*. Sin ella, un cambio de
    redacción viajaría en la traza disfrazado de la versión anterior.
    """
    original = RepositorioPromptsYaml(_escribir(tmp_path, _YAML_MINIMO, "uno.yaml"))
    retocado = RepositorioPromptsYaml(
        _escribir(
            tmp_path,
            _YAML_MINIMO.replace("Extrae los campos", "Extrae los campos,"),
            "dos.yaml",
        )
    )

    primero = original.obtener("parte_posventa_es")
    segundo = retocado.obtener("parte_posventa_es")

    assert primero.version == segundo.version
    assert primero.huella != segundo.huella


def test_f003_r10_la_huella_no_cambia_si_el_texto_no_cambia(tmp_path):
    """R10 · y es estable: dos cargas del mismo texto dan la misma huella.

    Una huella que cambiara sola —con la fecha, con el orden del fichero—
    convertiría la traza en ruido y nadie volvería a mirarla.
    """
    uno = RepositorioPromptsYaml(_escribir(tmp_path, _YAML_MINIMO, "uno.yaml"))
    dos = RepositorioPromptsYaml(_escribir(tmp_path, _YAML_MINIMO, "dos.yaml"))

    assert uno.obtener("parte_posventa_es").huella == (
        dos.obtener("parte_posventa_es").huella
    )
