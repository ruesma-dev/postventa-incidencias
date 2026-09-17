# services/postventa-api/domain/models/extraccion.py
"""Entidades de la extracción del parte (F-003).

Qué campos tiene un parte, cuáles se escriben a mano y cómo viaja lo que el
modelo lee: primero **en bruto**, tal y como lo devuelve el proveedor, y luego
**saneado**, con la confianza ya dentro de rango. Quien sanea es la aplicación
(R4), y por eso el dominio guarda las dos formas sin mezclarlas.

> **Añadido por F-032 el 2026-09-17.** Lo que el dominio sí sabe, y aquí vive,
> es **qué es cada campo**: `CAMPOS_DE_CODIGO` y `sanear_valor_leido` dicen
> cuáles de los nueve son un código y cómo se sanea uno. Aplicarlo sigue siendo
> de la aplicación y del borde HTTP —los dos llamantes—, así que «quien sanea es
> la aplicación» no cambia: lo que cambia es que el **criterio** deja de estar
> repartido. `sanear_valor_leido` no tiene reloj, ni red, ni configuración.

Aquí no hay proveedor, ni SDK, ni prompt: el dominio no sabe **quién** leyó el
parte. Eso es lo que permite cambiar de modelo por configuración sin tocar
nada de este fichero (R11, R13).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from domain.models.nombrado import normalizar_codigo

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

#: Los dos campos que son un **código** y no un texto (F-032 R14).
#:
#: Escritos literales y no derivados de nada: son exactamente los dos que
#: identifican algo fuera de este sistema —el `codigo_obra` decide la carpeta
#: de SharePoint donde acaba el PDF, y el `numero_incidencia`, qué reclamación
#: se cierra en el ERP—. Los otros siete llevan texto de una persona.
CAMPOS_DE_CODIGO: tuple[str, ...] = ("codigo_obra", "numero_incidencia")


def sanear_valor_leido(nombre: str, valor: str | None) -> str | None:
    """El valor de un campo listo para viajar y para guardarse (F-032, R11–R16).

    Un **código** sale sin blancos: es lo que identifica una reclamación en el
    ERP —que busca por **igualdad exacta**— y la carpeta del archivo. Cualquier
    otro campo sale **tal cual**: quitarle los espacios a una observación
    manuscrita la convertiría en otra cosa, y esa transcripción es justo lo que
    lee una persona para decidir si el parte vale.

    Se apoya en `normalizar_codigo` y **no en una copia**. Es la misma regla que
    nombra el fichero y que busca en el ERP, así que el día que cambie, cambia
    para las tres. Dos criterios del mismo concepto divergen siempre, y a este
    proyecto ya le pasó: F-028 dejó dos ideas distintas de «espacio sobrante» y
    el **2026-09-17** la IA leyó `RS 26.09/0178`, el cierre murió en
    `ReclamacionNoLocalizada` y hubo que editar el parte a mano.

    Dos cosas que no hace, y las dos importan:

    - **`None` se devuelve sin tocar** (R16): un campo que el modelo no leyó no
      se convierte en uno leído. Devolver `""` sería afirmar que el papel estaba
      en blanco, que es otra cosa;
    - **un código que se queda vacío sale `None`** y no `""`: un valor de solo
      blancos no dice nada que un `NULL` no diga, F-004 ya trata «solo espacios»
      como vacío y la huella del veredicto normaliza los dos al mismo sitio, así
      que esto **no mueve ninguna huella**.

    Un `import` de `domain/models/nombrado.py` es una dependencia **dentro** del
    dominio, y `nombrado` no importa a nadie salvo `errores`: no hay ciclo.
    """
    if valor is None or nombre not in CAMPOS_DE_CODIGO:
        return valor
    return normalizar_codigo(valor) or None


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
