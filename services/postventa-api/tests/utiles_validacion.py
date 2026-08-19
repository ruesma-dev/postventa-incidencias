# services/postventa-api/tests/utiles_validacion.py
"""Dobles y material de prueba de la validación y de la firma (F-004).

Entregable de la feature, igual que `tests/utiles_ia.py` en F-003
(`design.md` §6): aquí vive **todo** lo que los tests de F-004 necesitan
construir, y por eso ninguno lee un PDF real, ni un JSON capturado de una
llamada de verdad, ni nada de `muestras/`.

**Ni un dato personal.** El parte real lleva DNI de clientes y no se versiona
(`CLAUDE.md`, reglas duras): lo de aquí sale de `CAMPOS_DE_EJEMPLO` de
`utiles_ia.py`, inventado de cabo a rabo —el DNI `00000000T` no es válido—, o
son textos escritos a mano para el test.

Tres builders, y cada uno tiene su motivo:

- `lectura_de_firma(...)` construye la `LecturaFirma` ya saneada que consume
  `validar_parte`: es la entrada de las reglas puras.
- `respuesta_de_firma(...)` construye lo que devolvería un `ExtractorPort`
  **sin sanear**, para probar el paso del pipeline con etiquetas y confianzas
  imposibles.
- `extraccion_de_ejemplo(...)` construye la `ExtraccionParte` de F-003 con los
  nueve campos, para no repetir nueve líneas en cada test de reglas.
"""

from __future__ import annotations

from typing import Any

from domain.models.extraccion import CampoBruto, RespuestaModelo, TrazaExtraccion
from domain.models.firma import CAMPO_CLASIFICACION, ClasificacionFirma, LecturaFirma

from tests.utiles_ia import MODELO_DE_PRUEBA, PROVEEDOR_DE_PRUEBA

#: Clave del prompt de firma, la misma que declara `config/prompts.yaml`.
CLAVE_PROMPT_FIRMA = "firma_parte_es"

#: Hash de parte de mentira: es un identificador, no un dato del papel.
HASH_DE_PRUEBA = "9f2b0011aabb"


def traza_de_prueba(prompt_key: str = CLAVE_PROMPT_FIRMA) -> TrazaExtraccion:
    """La traza que acompañaría a una lectura, con valores inventados."""
    return TrazaExtraccion(
        proveedor=PROVEEDOR_DE_PRUEBA,
        modelo=MODELO_DE_PRUEBA,
        prompt_key=prompt_key,
        version_prompt="1",
        huella_prompt="0a1b2c3d4e5f",
    )


def lectura_de_firma(
    clasificacion: str | ClasificacionFirma = "humana",
    confianza: int = 93,
    *,
    hash_parte: str = HASH_DE_PRUEBA,
    avisos: tuple[str, ...] = (),
) -> LecturaFirma:
    """Una `LecturaFirma` ya saneada, la que consume `validar_parte`.

    La clasificación se acepta como texto para que los tests se lean solos
    (`lectura_de_firma("marca_simple")`), pero se convierte a la enumeración
    **de forma estricta**: si el test escribe una etiqueta que no existe, se
    entera aquí y no dentro de la regla que estaba probando.
    """
    return LecturaFirma(
        hash_parte=hash_parte,
        clasificacion=ClasificacionFirma(clasificacion),
        confianza_pct=confianza,
        traza=traza_de_prueba(),
        avisos=avisos,
    )


def respuesta_de_firma(
    etiqueta: Any = "humana",
    confianza: Any = 93,
    *,
    proveedor: str = PROVEEDOR_DE_PRUEBA,
    modelo: str = MODELO_DE_PRUEBA,
    campos: dict[str, CampoBruto] | None = None,
) -> RespuestaModelo:
    """Lo que devolvería el `ExtractorPort` leyendo la casilla de la firma.

    **Sin sanear**: `etiqueta` y `confianza` son `Any` a propósito, porque los
    tests de R2 y R3 meten aquí una etiqueta inventada, un `None` o una
    confianza que no es un entero. Quien lo arregle es el paso, no el doble.
    """
    return RespuestaModelo(
        proveedor=proveedor,
        modelo=modelo,
        campos=campos
        if campos is not None
        else {
            CAMPO_CLASIFICACION: CampoBruto(valor=etiqueta, confianza_pct=confianza)
        },
    )
