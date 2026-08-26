# services/postventa-api/infrastructure/persistencia/mapeo.py
"""De los modelos del dominio a columnas, y de las filas de vuelta al dominio.

Módulo **puro**: no importa `psycopg`, no abre nada y no sabe cuándo se
guarda. Aquí vive toda la lógica del adaptador que se puede probar sin base de
datos, que es casi toda: el adaptador (`repositorio_pg.py`) queda delgado a
propósito.

## La idea que sostiene R18

Las dieciocho columnas de campos y confianzas **se derivan de
`CAMPOS_DEL_PARTE`**, iterándolo. No hay ninguna lista escrita a mano que
alguien tenga que acordarse de mantener sincronizada: si mañana F-015 añade un
décimo campo al contrato, el mapeo se entera solo y el DDL que no lo tenga
rompe la suite.

## Dato personal

Por aquí pasan el DNI y las observaciones manuscritas del cliente. Este módulo
**no registra nada**: no tiene logger, a propósito. Lo que no se escribe no se
puede filtrar (R29, R37).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from domain.models.cierre import CorrespondenciaSigrid
from domain.models.extraccion import CAMPOS_DEL_PARTE, ExtraccionParte
from domain.models.persistencia import EntradaCola, PreferenciasUsuario
from domain.models.validacion import Motivo, ResultadoValidacion

__all__ = [
    "COLUMNAS_DE_CAMPOS",
    "columnas_de_campos",
    "fila_a_correspondencia",
    "fila_a_entrada_cola",
    "fila_a_preferencias",
    "json_de_avisos",
    "json_de_motivos",
    "valores_de_campos",
    "valores_de_traza_ia",
    "valores_de_validacion",
]

#: Sufijo de la columna de confianza de cada campo.
_SUFIJO_CONFIANZA = "_confianza_pct"

#: Cuántos caracteres de un aviso entran en la columna `avisos`.
#:
#: Un aviso es un **diagnóstico**, no un almacén: el de etiqueta desconocida
#: (`application/pipelines/paso_firma.py`) incrusta el valor crudo que devolvió
#: el modelo, y sin cota ese texto libre entraría verbatim en una base
#: compartida — justo en la tabla cuyo DDL declara que ahí no se copia texto
#: del cliente (R21, R39) —, sobre un servidor con el disco compartido con
#: otros tres proyectos (`design.md`, «sin JSON crudo gigante»).
#:
#: El número, razonado: el aviso legítimo más largo que emite hoy el pipeline
#: son 111 caracteres de texto fijo, antes de su parte variable; el resto de
#: avisos llevan como parte variable el nombre del documento, que dentro de un
#: ZIP es una ruta y puede pasar de los cien caracteres. 240 es algo más del
#: doble de ese esqueleto y deja ~130 libres para la parte variable, de modo
#: que ningún aviso legítimo se mutila; y por arriba acota la columna a unos
#: pocos KB por parte, porque un parte emite del orden de una decena de
#: avisos. El 80 de `ddl.py` no vale aquí: cortaría ese aviso legítimo.
_RECORTE_AVISO = 240


def columnas_de_campos() -> tuple[str, ...]:
    """Las 18 columnas de valor y confianza, en el orden del contrato (R18).

    Nueve campos, cada uno con su confianza justo detrás. El orden importa
    porque es el mismo que sigue `valores_de_campos`: las dos funciones
    recorren `CAMPOS_DEL_PARTE`, así que no pueden desincronizarse.
    """
    columnas: list[str] = []
    for campo in CAMPOS_DEL_PARTE:
        columnas.append(campo)
        columnas.append(f"{campo}{_SUFIJO_CONFIANZA}")
    return tuple(columnas)


#: Las 18 columnas, calculadas una vez.
COLUMNAS_DE_CAMPOS: tuple[str, ...] = columnas_de_campos()


def valores_de_campos(extraccion: ExtraccionParte) -> tuple[Any, ...]:
    """Los 18 valores, en el mismo orden que `columnas_de_campos`.

    Un campo que faltara en la extracción rompería aquí con `KeyError`, y eso
    es lo que se quiere: F-003 promete devolver siempre las nueve claves, y
    guardar un parte al que le falta una sería guardar algo que nadie sabe qué
    es.
    """
    valores: list[Any] = []
    for campo in CAMPOS_DEL_PARTE:
        extraido = extraccion.campo(campo)
        valores.append(extraido.valor)
        valores.append(extraido.confianza_pct)
    return tuple(valores)


def valores_de_traza_ia(extraccion: ExtraccionParte) -> tuple[Any, ...]:
    """Quién leyó el parte y con qué prompt (R19).

    Sin esto, revisar meses después por qué un parte se leyó mal es imposible:
    no se sabría ni qué modelo lo leyó ni con qué texto.
    """
    traza = extraccion.traza
    return (
        traza.proveedor,
        traza.modelo,
        traza.prompt_key,
        traza.version_prompt,
        traza.huella_prompt,
    )


def valores_de_validacion(
    resultado: ResultadoValidacion, ahora: datetime
) -> tuple[Any, ...]:
    """Los valores de una fila de `validaciones` (R20).

    **No incluye las observaciones**, aunque `ResultadoValidacion` las
    transporte: ya viven en la fila del parte y una segunda copia de texto
    manuscrito de un cliente dobla la exposición y diverge (R21, R39).
    """
    return (
        resultado.hash_parte,
        resultado.veredicto.value,
        resultado.destino.value,
        resultado.clasificacion_firma.value,
        json_de_motivos(resultado.motivos),
        json_de_avisos(resultado.avisos),
        ahora,
    )


def json_de_motivos(motivos: Iterable[Motivo]) -> str:
    """Los motivos como JSON, **en el orden en que los emitió F-004** (R20).

    El orden no es estético: F-004 los reúne todos y en un orden declarado
    para que quien revise el parte a mano lea primero lo que le falta al
    documento y después lo que hay que decidir.
    """
    return json.dumps(
        [{"codigo": motivo.codigo.value, "texto": motivo.texto} for motivo in motivos],
        ensure_ascii=False,
    )


def json_de_avisos(avisos: Iterable[str]) -> str:
    """Los avisos como JSON, **cada uno acotado a `_RECORTE_AVISO`** (R20).

    El recorte es por aviso y no sobre el JSON entero: si se aplicara al
    conjunto, un aviso largo se llevaría por delante a los cortos que van
    detrás, que suelen ser los que explican qué le falta al parte.

    Cuando hay recorte se deja la señal `…`, igual que hace `ddl.py`: sin ella
    quien lea la cola creería estar viendo el aviso completo.
    """
    return json.dumps(
        [_recortar_aviso(aviso) for aviso in avisos], ensure_ascii=False
    )


def _recortar_aviso(aviso: str) -> str:
    """El aviso, acotado, con `…` si se ha quedado algo fuera."""
    if len(aviso) <= _RECORTE_AVISO:
        return aviso
    return f"{aviso[:_RECORTE_AVISO]}…"


def fila_a_entrada_cola(fila: Sequence[Any]) -> EntradaCola:
    """Una fila de la consulta de la cola, de vuelta al dominio (R22).

    El orden de las columnas es el de `sentencias.select_cola`. Trae la
    transcripción de las observaciones **desde `partes`**, con un `JOIN`: no
    es una copia guardada aparte.
    """
    (
        hash_parte,
        codigo_obra,
        numero_incidencia,
        observaciones,
        confianza_observaciones,
        clasificacion_firma,
        motivos,
        validado_at_utc,
    ) = fila

    return EntradaCola(
        hash_parte=hash_parte,
        codigo_obra=codigo_obra,
        numero_incidencia=numero_incidencia,
        observaciones=observaciones,
        confianza_observaciones=confianza_observaciones,
        clasificacion_firma=clasificacion_firma,
        motivos=_motivos_desde_json(motivos),
        validado_at_utc=validado_at_utc,
    )


def fila_a_preferencias(fila: Sequence[Any]) -> PreferenciasUsuario:
    """Una fila de `preferencias_usuario`, de vuelta al dominio."""
    usuario_oid, auto_cierre, actualizado_at_utc = fila
    return PreferenciasUsuario(
        usuario_oid=usuario_oid,
        auto_cierre=bool(auto_cierre),
        actualizado_at_utc=actualizado_at_utc,
    )


def fila_a_correspondencia(fila: Sequence[Any]) -> CorrespondenciaSigrid:
    """Una fila de `usuarios_sigrid`, de vuelta al dominio (F-009).

    El orden de las columnas es el de `sentencias.select_login_sigrid`.
    `verificado_at_utc` puede llegar a `None`, y eso **significa algo**: es un
    alta manual que todavía no se ha comprobado contra el ERP, y por tanto no
    exime de comprobarla antes de firmar (R32).
    """
    usuario_oid, login_sigrid, alta_at_utc, verificado_at_utc = fila
    return CorrespondenciaSigrid(
        usuario_oid=usuario_oid,
        login_sigrid=login_sigrid,
        alta_at_utc=alta_at_utc,
        verificado_at_utc=verificado_at_utc,
    )


def _motivos_desde_json(motivos: Any) -> tuple[tuple[str, str], ...]:
    """Los motivos guardados, como pares `(codigo, texto)`.

    El driver puede devolver un `jsonb` ya deserializado o como texto, según
    cómo se haya declarado la columna en la consulta. Se admiten los dos: que
    la cola humana se quede sin motivos por un detalle de adaptación sería un
    fallo caro y silencioso.
    """
    if motivos is None:
        return ()
    if isinstance(motivos, str):
        motivos = json.loads(motivos)
    return tuple(
        (motivo["codigo"], motivo["texto"])
        for motivo in motivos
    )
