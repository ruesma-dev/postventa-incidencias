# services/postventa-api/infrastructure/documentos/plantilla_yaml.py
"""Carga y valida `config/plantilla_incidencias.yaml` (F-036, `design.md` §3.4).

El YAML trae lo que la plantilla no lee de Sigrid: las urgencias, los
listados y los textos que lee la propiedad. Se valida **entero al cargar**: un
fichero roto tiene que tumbar el arranque del handler, no generar una
plantilla cuyo desplegable ofrezca un valor que luego el importador rechace.

Las ubicaciones **ya no** están aquí (F-071, R21): salen de Sigrid, por
unidad, al descargar la plantilla. Un YAML que todavía traiga la clave
`ubicaciones` no carga, para que nadie crea que esa lista sigue mandando.

La ruta es fija (R49: F-036 no añade variables de entorno) y se resuelve
**relativa al servicio**, nunca al `cwd`, como la de los prompts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import yaml
from domain.models.errores import ConfiguracionPlantillaInvalida
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    MAX_DESCRIPCION,
    Listado,
    ListasCerradas,
    MensajeColumna,
    Opcion,
    TextosPlantilla,
    Urgencia,
)

#: Raíz del servicio: este fichero vive en `<servicio>/infrastructure/documentos/`.
SERVICIO = Path(__file__).resolve().parents[2]

RUTA_POR_DEFECTO = "config/plantilla_incidencias.yaml"

#: Columnas con validación de datos y, por tanto, con mensajes (R3, R4).
COLUMNAS_CON_MENSAJE: tuple[str, ...] = tuple(
    c for c in CABECERA if c != COLUMNA_ERRORES
)

#: Topes de Excel para los mensajes de una validación de datos.
MAX_TITULO_MENSAJE = 32
MAX_MENSAJE = 255

#: Filas de ejemplo en «Instrucciones» (R5: «dos o tres»).
MIN_EJEMPLOS = 2
MAX_EJEMPLOS = 3

_CAMPOS_MENSAJE = (
    ("titulo_entrada", MAX_TITULO_MENSAJE),
    ("entrada", MAX_MENSAJE),
    ("titulo_error", MAX_TITULO_MENSAJE),
    ("error", MAX_MENSAJE),
)


@dataclass(frozen=True)
class ConfiguracionPlantilla:
    listas: ListasCerradas
    textos: TextosPlantilla


def _falla(motivo: str) -> ConfiguracionPlantillaInvalida:
    return ConfiguracionPlantillaInvalida(f"{RUTA_POR_DEFECTO}: {motivo}")


def _texto(valor: object, donde: str) -> str:
    """Un texto no vacío, tal cual (sin recortar: lo que se escribe se compara exacto)."""
    if not isinstance(valor, str) or not valor.strip():
        raise _falla(f"{donde}: falta el texto")
    return valor


def _lista_de_mappings(valor: object, donde: str) -> list[Mapping]:
    if not isinstance(valor, list) or not all(isinstance(e, Mapping) for e in valor):
        raise _falla(f"{donde}: tiene que ser una lista de entradas con sus campos")
    return valor


def _opciones(
    crudo: object, seccion: str, codigos: tuple[str, ...]
) -> tuple[Opcion, ...]:
    """Una lista `{codigo, etiqueta}` con **exactamente** los códigos del `Enum`."""
    entradas = _lista_de_mappings(crudo, seccion)
    opciones = tuple(
        Opcion(
            etiqueta=_texto(e.get("etiqueta"), seccion),
            codigo=str(e.get("codigo")),
        )
        for e in entradas
    )
    leidos = [o.codigo for o in opciones]
    if sorted(leidos) != sorted(codigos):
        raise _falla(f"{seccion}: los códigos tienen que ser {', '.join(codigos)}")
    etiquetas = [o.etiqueta for o in opciones]
    if len(set(etiquetas)) != len(etiquetas):
        raise _falla(f"{seccion}: hay una etiqueta repetida")
    return opciones


def _ejemplos(crudo: object, listas: ListasCerradas) -> tuple[Mapping[str, str], ...]:
    if not isinstance(crudo, list) or not MIN_EJEMPLOS <= len(crudo) <= MAX_EJEMPLOS:
        raise _falla(
            f"textos.ejemplos: tienen que ser de {MIN_EJEMPLOS} a {MAX_EJEMPLOS}"
        )
    # `Ubicación`, `Oficio` y `Proveedor` salen de Sigrid (F-071): sus
    # ejemplos son textos indicativos (R19) y no se comprueban contra lista.
    permitidas = {
        "Urgencia": tuple(o.etiqueta for o in listas.urgencias),
        "Listado": tuple(o.etiqueta for o in listas.listados),
    }
    ejemplos: list[Mapping[str, str]] = []
    for numero, ejemplo in enumerate(crudo, start=1):
        donde = f"textos.ejemplos, ejemplo {numero}"
        if not isinstance(ejemplo, Mapping):
            raise _falla(f"{donde}: tiene que ser una fila con sus columnas")
        sobran = set(ejemplo) - set(COLUMNAS_CON_MENSAJE)
        if sobran:
            raise _falla(
                f"{donde}: columnas que no son de la plantilla: {sorted(sobran)}"
            )
        fila = {
            c: _texto(ejemplo[c], f"{donde}, {c}")
            for c in COLUMNAS_CON_MENSAJE
            if c in ejemplo
        }
        for obligatoria in ("Unidad", "Descripción corta"):
            if obligatoria not in fila:
                raise _falla(f"{donde}: falta «{obligatoria}»")
        if len(fila["Descripción corta"]) > MAX_DESCRIPCION:
            raise _falla(f"{donde}: la descripción corta pasa de {MAX_DESCRIPCION}")
        for columna, valores in permitidas.items():
            if columna in fila and fila[columna] not in valores:
                raise _falla(f"{donde}: «{columna}» no está en su lista")
        ejemplos.append(MappingProxyType(fila))
    return tuple(ejemplos)


def _mensajes(crudo: object) -> Mapping[str, MensajeColumna]:
    if not isinstance(crudo, Mapping):
        raise _falla("textos.mensajes: tiene que ser un mensaje por columna")
    sobran = sorted(set(crudo) - set(COLUMNAS_CON_MENSAJE))
    faltan = [c for c in COLUMNAS_CON_MENSAJE if c not in crudo]
    if sobran or faltan:
        raise _falla(f"textos.mensajes: faltan {faltan} y sobran {sobran}")
    mensajes: dict[str, MensajeColumna] = {}
    for columna in COLUMNAS_CON_MENSAJE:
        entrada = crudo[columna]
        if not isinstance(entrada, Mapping):
            raise _falla(f"textos.mensajes.{columna}: faltan sus campos")
        campos: dict[str, str] = {}
        for campo, tope in _CAMPOS_MENSAJE:
            texto = _texto(entrada.get(campo), f"textos.mensajes.{columna}.{campo}")
            if len(texto) > tope:
                raise _falla(
                    f"textos.mensajes.{columna}.{campo}: pasa de {tope} caracteres, "
                    "que es lo que admite Excel"
                )
            campos[campo] = texto
        mensajes[columna] = MensajeColumna(**campos)
    return MappingProxyType(mensajes)


def _textos(crudo: object, listas: ListasCerradas) -> TextosPlantilla:
    if not isinstance(crudo, Mapping):
        raise _falla("textos: tiene que ser un mapping")
    instrucciones = crudo.get("instrucciones")
    if not isinstance(instrucciones, list) or not instrucciones:
        raise _falla("textos.instrucciones: tiene que ser una lista de párrafos")
    return TextosPlantilla(
        titulo=_texto(crudo.get("titulo"), "textos.titulo"),
        instrucciones=tuple(_texto(p, "textos.instrucciones") for p in instrucciones),
        sin_oficios=_texto(crudo.get("sin_oficios"), "textos.sin_oficios"),
        excel_errores=_texto(crudo.get("excel_errores"), "textos.excel_errores"),
        ejemplos=_ejemplos(crudo.get("ejemplos"), listas),
        mensajes=_mensajes(crudo.get("mensajes")),
    )


def cargar_plantilla_yaml(
    ruta: str | Path = RUTA_POR_DEFECTO,
) -> ConfiguracionPlantilla:
    """Lee y valida el YAML; levanta `ConfiguracionPlantillaInvalida` si algo falla."""
    camino = Path(ruta)
    camino = camino if camino.is_absolute() else SERVICIO / camino
    if not camino.is_file():
        raise _falla(f"no existe el fichero {camino.name}")
    crudo = yaml.safe_load(camino.read_text(encoding="utf-8"))
    if not isinstance(crudo, Mapping):
        raise _falla("la raíz tiene que ser un mapping")
    if "ubicaciones" in crudo:
        raise _falla(
            "`ubicaciones`: la lista de ubicaciones ya no se configura aquí; "
            "sale de Sigrid, por unidad (F-071)"
        )
    listas = ListasCerradas(
        urgencias=_opciones(
            crudo.get("urgencias"), "urgencias", tuple(u.value for u in Urgencia)
        ),
        listados=_opciones(
            crudo.get("listados"), "listados", tuple(x.value for x in Listado)
        ),
    )
    return ConfiguracionPlantilla(
        listas=listas,
        textos=_textos(crudo.get("textos"), listas),
    )
