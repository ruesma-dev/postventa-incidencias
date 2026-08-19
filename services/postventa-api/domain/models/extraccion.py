# services/postventa-api/domain/models/extraccion.py
"""Entidades de la extracción del parte (F-003).

Qué campos tiene un parte, cuáles se escriben a mano y cómo viaja lo que el
modelo lee: primero **en bruto**, tal y como lo devuelve el proveedor, y luego
**saneado**, con la confianza ya dentro de rango. Quien sanea es la aplicación
(R4), y por eso el dominio guarda las dos formas sin mezclarlas.

Aquí no hay proveedor, ni SDK, ni prompt: el dominio no sabe **quién** leyó el
parte. Eso es lo que permite cambiar de modelo por configuración sin tocar
nada de este fichero (R11, R13).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

#: Los campos que se extraen de un parte, en el orden de la tabla de R1.
#:
#: **`unidad` es la unidad de posventa.** El papel la imprime con la etiqueta
#: «Vivienda» y el backlog la llamaba «chalet»: son tres nombres del mismo
#: dato. Se llama `unidad` (decisión del humano del 2026-08-18) porque es como
#: la nombra la estructura de archivo de Posventa
#: (`PARTES INCIDENCIAS / <UNIDAD> / PARTES FIRMADOS`).
#:
#: El noveno, **`numero_pagina`**, es el «Página N» del pie impreso (R2 bis).
#: Está aquí porque el modelo **sí ve ese pie** aunque el escaneo no tenga
#: capa de texto, que es justo lo que F-002 no pudo leer. F-003 lo lee y lo
#: devuelve; **quien reagrupe el parte de dos hojas con él es F-014**.
CAMPOS_DEL_PARTE: tuple[str, ...] = (
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

#: Los campos que van escritos a mano en el papel
#: (`docs/referencia/02_parte_de_trabajo.md`).
#:
#: Quién es manuscrito **lo sabe el dominio**, no el modelo, y esa decisión no
#: puede depender de lo que una IA declare en una respuesta.
#:
#: Ojo con lo que este conjunto **no** es. Tras la decisión del humano del
#: 2026-08-19, el campo que decide la regla «firmado no es conforme» es **solo
#: `observaciones`**: ni la fecha de servicio ni el DNI descalifican un parte,
#: y de hecho vienen en blanco en casi toda la remesa real. Quien lo aplica es
#: `domain/models/validacion.py` (F-004), que no usa este conjunto.
CAMPOS_MANUSCRITOS: frozenset[str] = frozenset(
    {"fecha_servicio", "dni_cliente", "observaciones"}
)


@dataclass(frozen=True)
class CampoBruto:
    """Lo que dice el modelo, sin tocar: valor y confianza tal y como llegan.

    `confianza_pct` es `object` a propósito. Un modelo puede devolver `"85"`,
    `120` o `null`, y quien lo saneé es la aplicación (R4), en un sitio que se
    puede probar sin proveedor.
    """

    valor: str | None
    confianza_pct: object


@dataclass(frozen=True)
class RespuestaModelo:
    """Lo que devuelve un `ExtractorPort`: campos en bruto y quién los leyó."""

    proveedor: str
    modelo: str
    campos: Mapping[str, CampoBruto]


@dataclass(frozen=True)
class CampoExtraido:
    """Un campo ya saneado: su valor literal y su confianza `0–100`."""

    valor: str | None
    confianza_pct: int

    @property
    def esta_vacio(self) -> bool:
        """¿El parte deja este campo en blanco?

        Vacío es no traer nada y traer solo espacios: de un escaneo salen las
        dos cosas y significan lo mismo. Y estar vacío **no es un fallo**: el
        papel real deja en blanco fecha, horas, nombre y DNI en casi toda la
        remesa (`docs/ARCHITECTURE.md`, semántica 4 bis).
        """
        return self.valor is None or self.valor.strip() == ""


@dataclass(frozen=True)
class TrazaExtraccion:
    """Con qué se obtuvo un dato: proveedor, modelo y prompt (R6, R10).

    Sin esto, revisar meses después por qué un parte se leyó mal es
    imposible: no se sabría ni qué modelo lo leyó ni con qué texto.
    """

    proveedor: str
    modelo: str
    prompt_key: str
    version_prompt: str
    huella_prompt: str


@dataclass(frozen=True)
class ExtraccionParte:
    """El resultado de leer **un** parte: sus campos, su traza y sus avisos.

    `campos` trae **siempre todas** las claves de `CAMPOS_DEL_PARTE` cuando lo
    construye el paso del pipeline (R2): un campo que faltara como clave
    rompería a F-004.
    """

    hash_parte: str
    campos: Mapping[str, CampoExtraido]
    traza: TrazaExtraccion
    avisos: tuple[str, ...] = ()

    def campo(self, nombre: str) -> CampoExtraido:
        """El campo pedido, o `KeyError` si no está.

        No devuelve un vacío de consolación: un campo ausente es un hueco del
        contrato y tiene que verse, no taparse.
        """
        return self.campos[nombre]
