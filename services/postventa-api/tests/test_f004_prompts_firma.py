# services/postventa-api/tests/test_f004_prompts_firma.py
"""Tests del prompt de la firma y del registro de schemas (R4, R5).

Dos cosas se vigilan aquí, y ninguna la caza ningún otro test:

- **Que F-004 no ha rozado el prompt de extracción.** Su calidad se midió a
  mano sobre 22 partes reales el 2026-08-19, y la suite no puede volver a
  medirla: el modelo está simulado. La única red disponible es clavar su
  huella (decisión D3 de `design.md` §7). El efecto lateral es buscado: quien
  lo cambie legítimamente en F-015 tendrá que actualizar la constante a
  conciencia y volver a medir.
- **Que cada prompt pide el schema que le corresponde.** Mandarle a la lectura
  de la firma el schema de los nueve campos —lo que pasaba antes de F-004,
  porque el adaptador lo tenía incrustado— produciría basura cara y silenciosa.

La huella y las listas de campos están escritas **a mano** en este fichero, no
importadas de lo que vigilan: un test parametrizado con su propia constante se
mueve con ella y aplaude el cambio en vez de cazarlo.
"""

from __future__ import annotations

import pytest
from domain.models.errores import SchemaDesconocido
from domain.models.schemas import CAMPOS_POR_SCHEMA, campos_del_schema
from infrastructure.llm.gemini import AdaptadorGeminiVision, schema_para
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml

from tests.utiles_ia import ClienteGenaiFalso, json_del_modelo, prompt_de_prueba

#: El fichero de prompts de verdad: aquí se prueba el que se despliega.
RUTA_DE_PROMPTS = "config/prompts.yaml"

#: La huella de `parte_posventa_es` medida en F-003 sobre 22 partes reales.
#: **Escrita a mano.** Si este test se cae, alguien ha tocado ese prompt y hay
#: que volver a medirlo, no actualizar la constante y seguir.
HUELLA_DEL_PROMPT_MEDIDO = "2306ac1d07f1"

#: Los nueve campos del parte, **escritos a mano** (contrato de F-003).
CAMPOS_DEL_PARTE_A_MANO = (
    "promocion",
    "codigo_obra",
    "unidad",
    "numero_incidencia",
    "fecha_servicio",
    "descripcion",
    "dni_cliente",
    "observaciones",
    "numero_pagina",
)


def _repositorio() -> RepositorioPromptsYaml:
    return RepositorioPromptsYaml(RUTA_DE_PROMPTS)


def test_f004_r4_el_prompt_de_firma_existe_y_es_otro():
    """R4 · `firma_parte_es` se carga entero y **no** es el de extracción.

    Es la vía B del diseño: un prompt propio sobre el mismo puerto, en vez de
    un décimo campo dentro del prompt medido. Si las dos huellas coincidieran,
    alguien habría copiado uno en el otro.
    """
    firma = _repositorio().obtener("firma_parte_es")
    extraccion = _repositorio().obtener("parte_posventa_es")

    assert firma.clave == "firma_parte_es"
    assert firma.version
    assert firma.schema == "firma_cliente"
    assert firma.system.strip()
    assert firma.task.strip()
    assert firma.huella != extraccion.huella


def test_f004_r4_el_prompt_de_extraccion_conserva_su_huella():
    """R4 · el prompt medido sobre 22 partes reales no se ha tocado.

    Ningún test unitario detecta que un cambio de redacción empeore la
    extracción: el modelo está simulado. Esta huella es la única prueba de que
    el barrido manual del 2026-08-19 sigue siendo válido.
    """
    extraccion = _repositorio().obtener("parte_posventa_es")

    assert extraccion.huella == HUELLA_DEL_PROMPT_MEDIDO
    assert extraccion.schema == "parte_posventa"
    assert extraccion.version == "1"


def test_f004_r5_cada_prompt_declara_un_schema_conocido():
    """R5 · ningún prompt del YAML pide un schema que el dominio no registre.

    El adaptador ya no sabe de memoria qué campos mandar: los resuelve por el
    nombre que declara el prompt. Un nombre mal escrito en el YAML tiene que
    verse aquí, y no en producción con un modelo devolviendo cualquier cosa.
    """
    prompts = _repositorio()._prompts

    assert prompts, "el fichero de prompts no declara ninguna clave"

    desconocidos = {
        clave: prompt.schema
        for clave, prompt in prompts.items()
        if prompt.schema not in CAMPOS_POR_SCHEMA
    }

    assert desconocidos == {}


def test_f004_r5_un_schema_no_registrado_revienta_antes_de_llamar_al_modelo():
    """R5 · con un schema inventado no se gasta ni una llamada.

    Es la mitad cara del requisito: llamar al modelo con el schema equivocado
    cuesta dinero y devuelve campos que nadie sabe leer. El doble del SDK
    tiene que quedarse **sin recibir ninguna llamada**.
    """
    cliente = ClienteGenaiFalso(json_del_modelo())
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo="gemini-3.7-flash",
        espera_inicial_s=0,
        cliente=cliente,
    )

    with pytest.raises(SchemaDesconocido) as fallo:
        adaptador.extraer(
            documento=b"%PDF-1.4 parte de prueba",
            mime="application/pdf",
            prompt=prompt_de_prueba(schema="schema_que_no_existe"),
        )

    assert "schema_que_no_existe" in fallo.value.motivo
    assert cliente.llamadas == []


def test_f004_r5_el_schema_de_la_firma_tiene_su_unico_campo():
    """R5 · a la casilla se le pregunta una cosa; al parte, nueve.

    Escritos a mano los dos: son el contrato del dominio, y un registro que se
    comprobara contra sí mismo no comprobaría nada.
    """
    assert campos_del_schema("firma_cliente") == ("clasificacion_firma",)
    assert campos_del_schema("parte_posventa") == CAMPOS_DEL_PARTE_A_MANO
    assert set(CAMPOS_POR_SCHEMA) == {"parte_posventa", "firma_cliente"}


def test_f004_r5_un_nombre_de_schema_no_registrado_no_devuelve_nada_por_defecto():
    """R5 · el registro no tiene consolación: o el nombre está, o hay error.

    Devolver una tupla vacía dejaría que la llamada saliera con un schema sin
    campos, que es exactamente el fallo silencioso que este requisito evita.
    """
    with pytest.raises(SchemaDesconocido):
        campos_del_schema("parte_posventas")

    with pytest.raises(SchemaDesconocido):
        campos_del_schema("")


def test_f004_r5_el_schema_estructurado_sale_del_nombre_que_pide_el_prompt():
    """R5 · el JSON schema que se le manda al modelo lo decide el prompt.

    Antes de F-004 el adaptador mandaba **siempre** los nueve campos: un
    segundo prompt habría recibido el schema equivocado. Ahora se resuelve por
    nombre, y por eso una feature futura puede añadir prompts sin tocar
    infraestructura.
    """
    del_parte = schema_para("parte_posventa")
    de_la_firma = schema_para("firma_cliente")

    assert tuple(del_parte["properties"]) == CAMPOS_DEL_PARTE_A_MANO
    assert del_parte["required"] == list(CAMPOS_DEL_PARTE_A_MANO)
    assert tuple(de_la_firma["properties"]) == ("clasificacion_firma",)
    assert de_la_firma["required"] == ["clasificacion_firma"]
    assert de_la_firma["properties"]["clasificacion_firma"]["properties"][
        "confianza_pct"
    ] == {"type": "integer"}


def test_f004_r5_la_llamada_al_modelo_usa_el_schema_del_prompt_de_firma():
    """R5 · y llega de verdad al SDK: no se queda en una función suelta.

    Se comprueba sobre la llamada que recibe el doble, que es lo que viajaría
    al proveedor.
    """
    cliente = ClienteGenaiFalso('{"clasificacion_firma": {"valor": "humana", '
                               '"confianza_pct": 93}}')
    adaptador = AdaptadorGeminiVision(
        api_key="no-es-una-credencial",
        modelo="gemini-3.7-flash",
        espera_inicial_s=0,
        cliente=cliente,
    )

    adaptador.extraer(
        documento=b"%PDF-1.4 parte de prueba",
        mime="application/pdf",
        prompt=prompt_de_prueba(clave="firma_parte_es", schema="firma_cliente"),
    )

    esquema = cliente.llamadas[0]["config"].response_json_schema

    assert tuple(esquema["properties"]) == ("clasificacion_firma",)
