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
from domain.models.estado import DecisionEstado, EstadoParte
from domain.models.extraccion import CAMPOS_DEL_PARTE, ExtraccionParte
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import (
    EntradaCola,
    EstadoGrafico,
    PreferenciasUsuario,
    TrazaGrafico,
)
from domain.models.validacion import (
    CodigoMotivo,
    Destino,
    Motivo,
    ResultadoValidacion,
    Veredicto,
)

__all__ = [
    "COLUMNAS_DE_CAMPOS",
    "columnas_de_campos",
    "fila_a_correspondencia",
    "fila_a_decision_estado",
    "fila_a_entrada_cola",
    "fila_a_preferencias",
    "fila_a_traza_grafico",
    "fila_a_validacion_y_cierre",
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


def fila_a_traza_grafico(fila: Sequence[Any]) -> TrazaGrafico:
    """Una fila de `graficos`, de vuelta al dominio (F-012).

    El orden de las columnas es el de `sentencias.select_grafico`, y por eso
    las dos cosas viven juntas: una fila leída por posición se rompe en
    silencio el día que alguien añade una columna al `SELECT`.

    `EstadoGrafico(estado)` **revienta** si la base trae un estado que el
    dominio no conoce, y eso es lo correcto: pasaría si alguien ampliara el
    `CHECK` del `.sql` sin ampliar el `Enum`, y traducirlo «como si fuera»
    otro haría que `paso_cierre` leyera «no adjuntado» de una fila que sí lo
    está — y con eso se cierra una reclamación sin su parte, que es justo lo
    que esta feature viene a impedir.

    Los tres `ide` y el `gra_cod` pueden llegar a `None`: son las trazas de
    dry-run y de error. `gra_ide_documental` puede ser `None` **incluso en una
    traza adjuntada**, porque la respuesta idempotente de la pasarela no lo
    trae **[MEDIDO]**.
    """
    (
        hash_parte,
        numero_incidencia,
        reclamacion_ide,
        estado,
        sha256,
        bytes_,
        nombre_fichero,
        gratipide,
        gra_cod,
        gra_ide_negocio,
        gra_ide_documental,
        rcg_ide,
        idempotente,
        confirmado_por,
        motivo,
        dry_run_at_utc,
        adjuntado_at_utc,
    ) = fila
    return TrazaGrafico(
        hash_parte=hash_parte,
        numero_incidencia=numero_incidencia,
        estado=EstadoGrafico(estado),
        reclamacion_ide=reclamacion_ide,
        sha256=sha256,
        bytes=bytes_,
        nombre_fichero=nombre_fichero,
        gratipide=gratipide,
        gra_cod=gra_cod,
        gra_ide_negocio=gra_ide_negocio,
        gra_ide_documental=gra_ide_documental,
        rcg_ide=rcg_ide,
        idempotente=bool(idempotente),
        confirmado_por=confirmado_por,
        motivo=motivo,
        dry_run_at_utc=dry_run_at_utc,
        adjuntado_at_utc=adjuntado_at_utc,
    )


def fila_a_decision_estado(fila: Sequence[Any]) -> DecisionEstado:
    """Una fila de `historico_estado`, de vuelta al dominio (F-028, R22).

    El orden de las columnas es el de `sentencias._COLUMNAS_HISTORICO`, y por
    eso las dos cosas viven pegadas: una fila leída por posición se rompe **en
    silencio** el día que alguien añade una columna al `SELECT`, y aquí eso
    sería reconstruir la decisión de una persona con la huella en el sitio del
    `oid`.

    La fila que llega **no trae el marcador de origen** del `UNION ALL`: lo
    quita quien lee, porque es de la consulta y no de la decisión. Tampoco trae
    `cambio_id`: lo pone la base y nadie lo lee, solo desempata el orden.

    `EstadoParte(...)` **revienta** si la base trae un estado que el dominio no
    conoce, y eso es lo correcto: pasaría si alguien ampliara el `CHECK` del
    `.sql` sin ampliar el `Enum`, y traducirlo «como si fuera» otro haría que
    un estado desconocido se leyera como `aprobado` y abriera la puerta del
    circuito que escribe en el ERP de producción.

    `estado_anterior` a `None` es «no había estado registrado antes» y se
    conserva como `None`: es la primera fila de ese parte. `decidido_por` a
    `None` es **lo decidió la máquina** (R24), y aquí no se traduce a nada:
    inventar un autor al leer sería tan falso como inventarlo al escribir.
    """
    (
        hash_parte,
        estado,
        decidido_at_utc,
        estado_anterior,
        decidido_por,
        motivo,
        huella_veredicto,
    ) = fila

    return DecisionEstado(
        hash_parte=hash_parte,
        estado=EstadoParte(estado),
        decidido_at_utc=decidido_at_utc,
        estado_anterior=(
            None if estado_anterior is None else EstadoParte(estado_anterior)
        ),
        decidido_por=decidido_por,
        motivo=motivo,
        huella_veredicto=huella_veredicto,
    )


def fila_a_validacion_y_cierre(
    fila: Sequence[Any], *, hash_parte: str
) -> tuple[ResultadoValidacion | None, str | None]:
    """El veredicto **guardado** y el estado de cierre, de vuelta al dominio (F-030).

    El orden de las columnas es el de `sentencias.select_veredicto_y_cierre`, y
    por eso las dos cosas viven pegadas: una fila leída por posición se rompe
    **en silencio** el día que alguien añade una columna al `SELECT`, y aquí eso
    sería recomponer el veredicto con el destino en el sitio del veredicto.

    **Las dos cosas vuelven juntas porque vienen de la misma fila** — la misma
    regla que ya siguen `fila_a_traza_grafico` y `fila_a_decision_estado`—, y
    eso es lo que hace que leer el veredicto no cueste ni un viaje más contra
    un PostgreSQL que se comparte con otros tres proyectos (R18).

    Tres columnas salen de `postventa.partes` y no de `validaciones`: las
    **observaciones**, el **código de obra** y el **número de incidencia**. No
    es una comodidad: el DDL de `validaciones` prohíbe copiar ahí el texto
    manuscrito del cliente (R21, R39), así que la única forma de recomponer los
    seis campos de la cadena canónica de la huella es el `JOIN`.

    `veredicto` a `None` **es «no hay fila de validación»**, y se distingue por
    ahí y no por el `hash_parte`: la consulta se ancla en `partes`, así que el
    `hash` viene siempre aunque no haya veredicto. En ese caso vuelve `None`, y
    de ahí sale el error propio de «no consta que este parte haya pasado la
    validación» (R8, R9) — que se arregla revalidando, no decidiendo.

    Los cuatro enumerados **revientan** si la base trae un valor que el dominio
    no conoce, igual que `EstadoGrafico` y `EstadoParte`: pasaría si alguien
    ampliara un `CHECK` del `.sql` sin ampliar el `Enum`, y traducirlo «como si
    fuera» otro haría que un destino desconocido se leyera como
    `archivo_y_cierre` y abriera la puerta que escribe en el ERP de producción.

    Las observaciones se pasan **tal cual vienen**, y pueden ser `None` o solo
    espacios: normalizarlas aquí sería una segunda copia del criterio de
    `_normalizar`, que es de `huella_de_veredicto` y no se toca (R13). Los dos
    campos decisivos sí se traducen de `NULL` a `""`, porque eso no es criterio
    sino el valor por defecto que ya declara `ResultadoValidacion`.

    El `hash_parte` entra **por palabra clave y no de la fila**: es el que se
    pidió, y `ResultadoValidacion.hash_parte` es identificador, no dato leído.
    """
    (
        veredicto,
        destino,
        clasificacion_firma,
        motivos,
        avisos,
        observaciones,
        confianza_observaciones,
        codigo_obra,
        numero_incidencia,
        estado_cierre,
    ) = fila

    if veredicto is None:
        return None, estado_cierre

    validacion = ResultadoValidacion(
        hash_parte=hash_parte,
        veredicto=Veredicto(veredicto),
        destino=Destino(destino),
        motivos=tuple(
            Motivo(codigo=CodigoMotivo(codigo), texto=texto)
            for codigo, texto in _motivos_desde_json(motivos)
        ),
        clasificacion_firma=ClasificacionFirma(clasificacion_firma),
        observaciones=observaciones,
        confianza_observaciones=confianza_observaciones,
        avisos=_avisos_desde_json(avisos),
        codigo_obra=codigo_obra or "",
        numero_incidencia=numero_incidencia or "",
    )
    return validacion, estado_cierre


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


def _avisos_desde_json(avisos: Any) -> tuple[str, ...]:
    """Los avisos guardados, como tupla de textos.

    El gemelo de `_motivos_desde_json`, con la misma tolerancia y por el mismo
    motivo: el driver puede devolver un `jsonb` ya deserializado o como texto,
    según cómo se haya declarado la columna en la consulta.

    Los avisos **no entran en la cadena canónica de la huella**, así que el
    recorte a `_RECORTE_AVISO` con el que se guardaron no caduca ninguna
    aprobación: vuelven acotados y eso es lo que había que devolver. Que la
    columna venga a `NULL` tampoco es un error — es un veredicto que no emitió
    ningún diagnóstico— y da la tupla vacía, que es el valor por defecto del
    dominio.
    """
    if avisos is None:
        return ()
    if isinstance(avisos, str):
        avisos = json.loads(avisos)
    return tuple(avisos)
