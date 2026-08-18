# services/postventa-api/tests/utiles_ia.py
"""Dobles y respuestas simuladas de la extracción (F-003).

Entregable de la feature, igual que `tests/utiles_pdf.py` en F-002: aquí vive
**todo** el material de prueba de la IA, y por eso ningún test necesita red
—la guardia de `conftest.py` la hace imposible— ni un JSON capturado de una
llamada real.

**Ni un dato personal.** El parte real lleva DNI de clientes y no se versiona
(`CLAUDE.md`, reglas duras), así que promoción, unidad, observaciones y DNI de
aquí están **inventados**: el DNI `00000000T` no es un DNI válido. Un builder
parametrizable, además, deja legible qué prueba cada test:
`respuesta_simulada(omitir=["fecha_servicio"])` se lee solo; un JSON de
cuarenta líneas, no.

Dos costuras, dos dobles (`design.md` §6.1):

- `ExtractorFalso` sustituye al adaptador entero (cumple `ExtractorPort`) y
  sirve para probar el paso del pipeline y el endpoint.
- `ClienteGenaiFalso` sustituye al cliente del SDK **dentro** del adaptador, y
  sirve para probar el adaptador de verdad: parseo, reintentos y errores.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from domain.models.extraccion import CampoBruto, RespuestaModelo
from domain.models.prompt import PromptSpec, huella_de_prompt
from google.genai import errors as errores_genai

#: Proveedor y modelo con los que se etiquetan las respuestas simuladas.
PROVEEDOR_DE_PRUEBA = "gemini"
MODELO_DE_PRUEBA = "gemini-3.7-flash"

#: Confianza que se le pone a un campo cuando el test no dice otra cosa.
CONFIANZA_POR_DEFECTO = 90

#: Un parte de mentira, campo a campo: `(valor, confianza)`. Reproduce la
#: forma del papel (`docs/referencia/02_parte_de_trabajo.md`) con datos
#: inventados de cabo a rabo.
CAMPOS_DE_EJEMPLO: dict[str, tuple[str | None, Any]] = {
    "promocion": ("15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)", 96),
    "codigo_obra": ("0677", 99),
    "unidad": ("Viviendas Bloque Villa 5", 94),
    "numero_incidencia": ("RS26.08/0123", 97),
    "fecha_servicio": ("05/08/26", 71),
    "descripcion": ("Sellado de encuentro de falsos techos de porches", 92),
    "dni_cliente": ("00000000T", 61),
    "observaciones": ("Se aprecia que se han hecho parcheados", 74),
    "numero_pagina": ("1", 98),
}


def _a_campo_bruto(valor: Any) -> CampoBruto:
    """Traduce lo que escribe el test a un `CampoBruto`.

    Admite tres formas, de la más cómoda a la más explícita: `None` (campo en
    blanco), un valor suelto (con la confianza por defecto) y la pareja
    `(valor, confianza)`, que es la que usan los tests de R4 para meter
    confianzas imposibles.
    """
    if isinstance(valor, CampoBruto):
        return valor
    if isinstance(valor, tuple):
        return CampoBruto(valor=valor[0], confianza_pct=valor[1])
    if valor is None:
        return CampoBruto(valor=None, confianza_pct=0)
    return CampoBruto(valor=valor, confianza_pct=CONFIANZA_POR_DEFECTO)


def _campos_de_ejemplo(
    omitir: Sequence[str], cambios: dict[str, Any]
) -> dict[str, CampoBruto]:
    """Los campos de ejemplo, menos los omitidos, más los que cambie el test.

    Una clave que no esté en `CAMPOS_DE_EJEMPLO` se añade igual: así se simula
    que el modelo se invente un campo, que es lo que vigilan R1 y R7.
    """
    campos = {
        nombre: _a_campo_bruto(valor)
        for nombre, valor in CAMPOS_DE_EJEMPLO.items()
        if nombre not in omitir
    }
    campos.update({nombre: _a_campo_bruto(valor) for nombre, valor in cambios.items()})
    return campos


def respuesta_simulada(
    *,
    proveedor: str = PROVEEDOR_DE_PRUEBA,
    modelo: str = MODELO_DE_PRUEBA,
    omitir: Sequence[str] = (),
    **campos: Any,
) -> RespuestaModelo:
    """Lo que devolvería un `ExtractorPort`, ya parseado y sin normalizar."""
    return RespuestaModelo(
        proveedor=proveedor,
        modelo=modelo,
        campos=_campos_de_ejemplo(omitir, campos),
    )


def json_del_modelo(*, omitir: Sequence[str] = (), **campos: Any) -> str:
    """El texto JSON que devolvería Gemini, para probar el parseo del adaptador."""
    return json.dumps(
        {
            nombre: {"valor": bruto.valor, "confianza_pct": bruto.confianza_pct}
            for nombre, bruto in _campos_de_ejemplo(omitir, campos).items()
        },
        ensure_ascii=False,
    )


def prompt_de_prueba(**cambios: str) -> PromptSpec:
    """Un `PromptSpec` de mentira, con su huella calculada como la de verdad.

    La huella sale de `huella_de_prompt`, la misma función que usa el
    repositorio del YAML: si el test la calculara por su cuenta habría dos
    algoritmos que mantener y R10 dejaría de significar nada.
    """
    datos = {
        "clave": "parte_posventa_es",
        "version": "1",
        "schema": "parte_posventa",
        "system": "Eres un extractor de prueba.",
        "task": "Extrae los campos del parte de prueba.",
    }
    datos.update(cambios)
    return PromptSpec(
        clave=datos["clave"],
        version=datos["version"],
        schema=datos["schema"],
        system=datos["system"],
        task=datos["task"],
        huella=huella_de_prompt(datos["system"], datos["task"]),
    )


def error_del_proveedor(codigo: int, mensaje: str = "error simulado") -> Exception:
    """Un error del SDK con el código HTTP pedido.

    `429` y los `5xx` son transitorios y se reintentan; un `400` o un `401`,
    no. Se construye el error de verdad del SDK —no un `Exception` cualquiera—
    para que el test compruebe la regla que se aplicará en producción.
    """
    return errores_genai.ClientError(
        codigo, {"error": {"code": codigo, "message": mensaje, "status": "SIMULADO"}}
    )


class ExtractorFalso:
    """Doble de `ExtractorPort` que registra lo que le piden.

    O devuelve la respuesta programada, o levanta el error programado. Guardar
    las llamadas es lo que permite comprobar lo más importante de R16: que
    ante un parte demasiado grande **no se le llama**.
    """

    def __init__(
        self,
        respuesta: RespuestaModelo | None = None,
        error: Exception | None = None,
    ) -> None:
        self.respuesta = respuesta if respuesta is not None else respuesta_simulada()
        self.error = error
        self.llamadas: list[dict[str, Any]] = []

    def extraer(
        self, *, documento: bytes, mime: str, prompt: PromptSpec
    ) -> RespuestaModelo:
        self.llamadas.append({"documento": documento, "mime": mime, "prompt": prompt})
        if self.error is not None:
            raise self.error
        return self.respuesta


class RespuestaGenaiFalsa:
    """Lo que devuelve el SDK: un objeto con el texto de la respuesta."""

    def __init__(self, texto: str) -> None:
        self.text = texto


class _ModelosFalsos:
    """El `cliente.models` del SDK, con su `generate_content`."""

    def __init__(self, cliente: ClienteGenaiFalso) -> None:
        self._cliente = cliente

    def generate_content(self, **argumentos: Any) -> RespuestaGenaiFalsa:
        self._cliente.llamadas.append(argumentos)
        if not self._cliente.pendientes:
            raise AssertionError(
                "el doble del SDK ha recibido más llamadas de las programadas"
            )
        siguiente = self._cliente.pendientes.pop(0)
        if isinstance(siguiente, BaseException):
            raise siguiente
        return RespuestaGenaiFalsa(siguiente)


class ClienteGenaiFalso:
    """Doble del cliente del SDK, con una secuencia programable.

    Cada elemento de la secuencia es lo que pasa en la llamada n-ésima: un
    texto se devuelve como respuesta, una excepción se levanta. Con eso se
    prueban los reintentos (R14), su agotamiento (R15) y que un error no
    transitorio sale a la primera.
    """

    def __init__(self, *secuencia: Any) -> None:
        self.pendientes: list[Any] = list(secuencia)
        self.llamadas: list[dict[str, Any]] = []
        self.models = _ModelosFalsos(self)
