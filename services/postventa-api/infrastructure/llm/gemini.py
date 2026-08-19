# services/postventa-api/infrastructure/llm/gemini.py
"""Adaptador de Gemini: el **único** fichero del servicio que conoce el SDK.

Implementa `ExtractorPort`. Todo lo que sabe de `google-genai` está aquí, y
eso es deliberado (riesgo 3 del diseño): el SDK es joven y cambia, así que el
día que cambie una firma se toca este fichero y ni el dominio ni la aplicación
se enteran.

Dos cosas que no son de estilo, sino reglas:

- **El contenido del parte no sale de aquí.** Ni en el log ni en el mensaje de
  un error. Se registran modelo, tamaño en bytes, intento y duración; nunca
  los bytes, nunca la respuesta cruda, nunca un valor leído. El parte lleva
  DNI de clientes (R15, riesgo 4).
- **El schema se genera desde el dominio.** No se escribe a mano una segunda
  lista de campos: el contrato del dominio y el que se le manda al modelo son
  la misma fuente. Desde F-004 **cuál** de esas listas toca lo dice el prompt
  (`PromptSpec.schema`), no este fichero: el adaptador sirve a los dos prompts
  —el del parte y el de la firma— sin saber de ninguno.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Mapping
from typing import Any

from domain.models.errores import ExtraccionFallida
from domain.models.extraccion import CampoBruto, RespuestaModelo
from domain.models.prompt import PromptSpec
from domain.models.schemas import campos_del_schema
from google import genai
from google.genai import types
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

#: Nombre con el que este adaptador se identifica en la traza (R6).
PROVEEDOR = "gemini"

#: Errores de red que merecen otro intento sin mirar ningún código.
ERRORES_TRANSITORIOS = (TimeoutError, ConnectionError)

#: Códigos del proveedor que significan «vuelve a preguntar»: cuota agotada,
#: tiempo agotado y los 5xx. Un 400 o un 401 no mejoran por insistir.
CODIGOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})


def es_transitorio(error: BaseException) -> bool:
    """¿Ese fallo tiene pinta de arreglarse solo en el siguiente intento?"""
    if isinstance(error, ERRORES_TRANSITORIOS):
        return True
    return getattr(error, "code", None) in CODIGOS_TRANSITORIOS


def schema_para(nombre: str) -> dict[str, Any]:
    """El schema estructurado de ese nombre, generado del dominio (F-004, R5).

    Antes de F-004 esta función era `schema_del_parte()` y mandaba **siempre**
    los nueve campos: el adaptador sabía de memoria a qué prompt servía. Ahora
    resuelve el nombre que declara el prompt contra `CAMPOS_POR_SCHEMA`, y por
    eso una feature futura puede añadir un prompt sin tocar infraestructura.

    Todos los campos van como `required` a propósito: es la mitad de R2 que se
    le puede exigir al modelo. La otra mitad —completar lo que aun así falte—
    la hace la aplicación, porque un `required` no es una garantía.

    Levanta `SchemaDesconocido` si el nombre no está registrado, y se llama
    **antes** de entrar en los reintentos: llamar al modelo con el schema
    equivocado cuesta dinero y devuelve campos que nadie sabe leer.
    """
    campos = campos_del_schema(nombre)
    return {
        "type": "object",
        "properties": {
            campo: {
                "type": "object",
                "properties": {
                    "valor": {"type": ["string", "null"]},
                    "confianza_pct": {"type": "integer"},
                },
                "required": ["valor", "confianza_pct"],
            }
            for campo in campos
        },
        "required": list(campos),
    }


class AdaptadorGeminiVision:
    """Lee documentos con un modelo multimodal de Gemini."""

    def __init__(
        self,
        *,
        api_key: str,
        modelo: str,
        timeout_s: int = 120,
        reintentos: int = 3,
        espera_inicial_s: float = 1.0,
        cliente: Any | None = None,
    ) -> None:
        self.modelo = modelo
        self.cliente = cliente
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._reintentos = reintentos
        self._espera_inicial_s = espera_inicial_s

    def _asegurar_cliente(self) -> Any:
        """El cliente del SDK, construido en la primera llamada y reutilizado.

        No se construye en el `__init__` para que el adaptador se pueda crear
        sin SDK vivo y sin abrir nada: `/health` no puede depender de que haya
        credencial de IA.
        """
        if self.cliente is None:
            self.cliente = genai.Client(api_key=self._api_key)
        return self.cliente

    def extraer(
        self, *, documento: bytes, mime: str, prompt: PromptSpec
    ) -> RespuestaModelo:
        """Manda el documento al modelo y devuelve sus campos **en bruto**.

        El schema se resuelve **aquí**, antes de entrar en los reintentos: un
        nombre no registrado tiene que salir como `SchemaDesconocido` —un
        fallo de configuración— y no disfrazado de `ExtraccionFallida` tras
        tres intentos que nunca llegaron a salir (R5).
        """
        esquema = schema_para(prompt.schema)
        texto = self._llamar_con_reintentos(
            documento=documento, mime=mime, prompt=prompt, esquema=esquema
        )
        return RespuestaModelo(
            proveedor=PROVEEDOR,
            modelo=self.modelo,
            campos=_a_campos(_json_del_modelo(texto, self.modelo)),
        )

    def _llamar_con_reintentos(
        self,
        *,
        documento: bytes,
        mime: str,
        prompt: PromptSpec,
        esquema: dict[str, Any],
    ) -> str:
        """Llama al modelo reintentando solo lo que puede mejorar (R14, R15)."""
        reintentador = Retrying(
            retry=retry_if_exception(es_transitorio),
            wait=wait_exponential(multiplier=self._espera_inicial_s),
            stop=stop_after_attempt(self._reintentos),
            reraise=True,
        )
        try:
            return reintentador(
                self._una_llamada,
                documento=documento,
                mime=mime,
                prompt=prompt,
                esquema=esquema,
            )
        except Exception as error:
            raise ExtraccionFallida(
                f"el modelo {self.modelo} no devolvió una respuesta utilizable: "
                f"{type(error).__name__} (código {getattr(error, 'code', 'ninguno')})"
            ) from error

    def _una_llamada(
        self,
        *,
        documento: bytes,
        mime: str,
        prompt: PromptSpec,
        esquema: dict[str, Any],
    ) -> str:
        """Un intento contra el SDK. Registra tamaños y tiempos, nunca datos."""
        arranque = time.monotonic()
        respuesta = self._asegurar_cliente().models.generate_content(
            model=self.modelo,
            contents=[
                prompt.task,
                types.Part.from_bytes(data=documento, mime_type=mime),
            ],
            config=types.GenerateContentConfig(
                system_instruction=prompt.system,
                response_mime_type="application/json",
                response_json_schema=esquema,
                http_options=types.HttpOptions(timeout=self._timeout_s * 1000),
            ),
        )
        log.info(
            "extraccion: modelo=%s prompt=%s huella=%s bytes=%d segundos=%.2f",
            self.modelo,
            prompt.clave,
            prompt.huella,
            len(documento),
            time.monotonic() - arranque,
        )
        return respuesta.text


def _json_del_modelo(texto: str | None, modelo: str) -> Mapping[str, Any]:
    """El JSON de la respuesta, o `ExtraccionFallida` diciendo qué llegó.

    Lo que **no** dice el mensaje es qué ponía la respuesta: sería volcar en
    el log lo que el modelo leyó del parte.
    """
    try:
        datos = json.loads(texto or "")
    except ValueError as error:
        raise ExtraccionFallida(
            f"la respuesta del modelo {modelo} no es JSON válido"
        ) from error
    if not isinstance(datos, Mapping):
        raise ExtraccionFallida(
            f"la respuesta del modelo {modelo} es un {type(datos).__name__} "
            "y se esperaba un objeto con los campos del parte"
        )
    return datos


def _a_campos(datos: Mapping[str, Any]) -> dict[str, CampoBruto]:
    """Los campos tal y como llegan. Aquí no se sanea nada (eso es R4)."""
    return {nombre: _a_campo(crudo) for nombre, crudo in datos.items()}


def _a_campo(crudo: Any) -> CampoBruto:
    """Un campo del JSON, venga bien puesto o venga suelto.

    Un modelo descuidado devuelve `"0677"` en vez de `{"valor": …}`. Tirar el
    parte entero por eso sería peor que quedarse el valor y desconfiar de él:
    sin confianza declarada, la aplicación lo dejará en 0 con su aviso (R4).
    """
    if isinstance(crudo, Mapping):
        return CampoBruto(
            valor=_texto(crudo.get("valor")),
            confianza_pct=crudo.get("confianza_pct"),
        )
    return CampoBruto(valor=_texto(crudo), confianza_pct=None)


def _texto(valor: Any) -> str | None:
    """El valor como texto, sin normalizar nada más (R5).

    Solo convierte el tipo: un modelo puede devolver `2` donde el schema pide
    `"2"`, y eso no cambia lo que pone el papel.
    """
    return None if valor is None else str(valor)
