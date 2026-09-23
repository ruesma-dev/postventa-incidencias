# services/postventa-api/application/pipelines/codigos_del_parte.py
"""Los dos códigos que deciden dónde se escribe, en un solo sitio (F-031, F-034).

El `codigo_obra` y el `numero_incidencia` de un parte deciden tres cosas, y las
tres son escrituras:

- la **carpeta y el nombre** con los que se archiva en SharePoint
  (`paso_archivo`, F-031);
- **a qué reclamación** del ERP se adjunta el parte y **con qué nombre**
  (`paso_grafico`, F-034);
- **qué reclamación se cierra** en el ERP de producción (`paso_cierre`, F-034).

En las tres, la regla es la misma: **deciden los guardados** —los que constan
en `postventa.partes` y viajan en la situación que la puerta de aptitud ya
leyó—, y los que trae el cuerpo de la petición **solo cotejan**: si no son los
guardados, no se escribe nada. Lo declarado puede cerrar la puerta, nunca
abrirla ni moverla (F-034 R19).

## Por qué es un módulo y no una función privada en cada paso

Es literalmente el argumento que `puerta_de_estado.py` tiene escrito en su
cabecera y que F-028 pagó por aprender: dos copias de una regla divergen el día
que alguien la corrija en una sola, y en una campaña de mutación **cada copia
se cuenta aparte**, con lo que la segunda y la tercera se quedan sin tests que
las maten. Aquí la aplican tres pasos, y la copia que se aflojara sería la que
dejara escribir en la reclamación equivocada, que en el ERP no se deshace desde
este circuito.

Hasta F-034 estas piezas vivían, privadas, en `paso_archivo.py`
(`_codigos_guardados`, `_exigir_codigos_declarados`). Se mueven aquí **sin
cambiar ni una regla** (F-034 R26, decisión D-2 aprobada por el humano el
2026-09-22): el mensaje que ve quien archiva es, byte a byte, el de antes, y lo
vigila `tests/test_f034_codigos_en_el_erp.py`.

## Tres hechos que no se confunden

- lo declarado **no es** lo guardado → `CodigosNoCoinciden`
  (`exigir_codigos_declarados`);
- lo guardado **está incompleto** → `CodigoNoConsta`
  (`exigir_codigos_completos`);
- el nombre compuesto no vale para SharePoint → `NombradoImposible`, que no
  vive aquí sino en el dominio del nombrado.

Cada uno se arregla de una forma distinta (F-034 R28), y los tres son 409 en el
borde.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.models.errores import CodigoNoConsta, CodigosNoCoinciden
from domain.models.nombrado import es_el_mismo_codigo, normalizar_codigo

from application.pipelines.contexto_parte import ContextoParte

__all__ = [
    "CodigosDelParte",
    "codigos_guardados",
    "exigir_codigos_completos",
    "exigir_codigos_declarados",
]

#: Cómo se nombra cada código en los mensajes, y **en qué orden** se miran: la
#: obra primero, como hacía F-031.
_ETIQUETA_OBRA = "el código de obra"
_ETIQUETA_INCIDENCIA = "el nº de incidencia"


@dataclass(frozen=True)
class CodigosDelParte:
    """Los dos códigos que deciden en qué reclamación —y en qué carpeta— se escribe.

    Una pieza y no dos cadenas sueltas por lo mismo que `DestinoArchivo` es
    una pieza: van siempre juntos y siempre en el mismo orden, y dos
    parámetros posicionales del mismo tipo se invierten un día sin que ningún
    test de tipos lo vea — y ese día el parte se archiva con el nombre del
    revés, o se adjunta a otra reclamación.

    Se usa para las **dos** cosas, y conviene no confundirlas: los guardados
    (`codigos_guardados`), que son los que deciden (F-031 R1, F-034 R8, R9), y
    los declarados en el cuerpo de la petición, que **solo** sirven para
    cotejar y no pueden decidir nada (F-031 R11, F-034 R19).
    """

    codigo_obra: str
    numero_incidencia: str


def codigos_guardados(ctx: ContextoParte) -> CodigosDelParte:
    """Los dos códigos que constan **guardados** de este parte (F-031 R1, F-034 R8).

    Se leen de `ctx.situacion.validacion`, que la puerta de aptitud acaba de
    dejar puesta, y por tanto de la misma consulta que ya se hacía: **ni una
    sentencia más** (F-031 R2, F-034 R10). Los dos campos viajan ahí desde
    F-030, que los necesitaba para recomponer la huella del veredicto, y salen
    de `postventa.partes`, no de `validaciones`.

    Que se lean de **ese** objeto y no de un campo propio de `SituacionParte`
    es la decisión D-1 de F-031, aprobada por el humano el 2026-09-22, y da una
    propiedad que ningún otro camino da gratis: se escribe, byte por byte, con
    los dos valores que la puerta **acaba de aprobar**.

    Sin `validacion` devuelve dos cadenas vacías y **no levanta nada**: quien
    decide que eso es un error es quien los va a usar —el nombrado en archivo
    (F-031 R7), `exigir_codigos_completos` en el gráfico y el cierre (F-034
    R15)—, y lo dice nombrando cuál falta.

    Un único punto de lectura, con nombre, es además lo que hace que F-013 no
    tenga que volver a decidir de dónde salen.
    """
    validacion = ctx.situacion.validacion if ctx.situacion is not None else None
    if validacion is None:
        return CodigosDelParte(codigo_obra="", numero_incidencia="")
    return CodigosDelParte(
        codigo_obra=validacion.codigo_obra,
        numero_incidencia=validacion.numero_incidencia,
    )


def _a_mirar(
    codigos: CodigosDelParte, *, solo_incidencia: bool
) -> tuple[tuple[str, str], ...]:
    """(etiqueta, valor) de cada código que toca mirar, **en orden**: obra primero.

    Un solo sitio decide qué se mira con y sin `solo_incidencia`, para que el
    cotejo y la exigencia de completos no puedan discrepar en eso.
    """
    incidencia = (_ETIQUETA_INCIDENCIA, codigos.numero_incidencia)
    if solo_incidencia:
        return (incidencia,)
    return ((_ETIQUETA_OBRA, codigos.codigo_obra), incidencia)


def exigir_codigos_declarados(
    declarados: CodigosDelParte | None,
    guardados: CodigosDelParte,
    *,
    solo_incidencia: bool = False,
    y_por_eso: str,
) -> None:
    """Lo declarado tiene que ser lo guardado, o no se escribe (F-031 R3, F-034 R11).

    Compara campo a campo con `es_el_mismo_codigo`, que normaliza los dos
    lados con el criterio de F-032: `RS 26.09/0178` y `RS26.09/0178`, o `06 26`
    y `0626`, son **el mismo** código y no pueden dar un error (F-031 R4,
    F-034 R12). El front manda lo que devuelve `valorDeCampo`, que solo hace
    `trim()`, mientras que la base guarda lo que F-032 saneó al leerlo; con un
    cotejo literal, el caso que costó un cierre a mano el 2026-09-17 sería un
    error diario.

    Levanta `CodigosNoCoinciden` nombrando **el primero que falla** —la obra
    antes que la incidencia— con los dos valores. El mensaje tiene una parte
    fija, «<cuál> de la petición («…») no es el que consta guardado para este
    parte («…»), así que », y **todo lo demás lo pone quien llama** en
    `y_por_eso`: qué no se ha hecho y qué hay que hacer, incluida la acción de
    guardar la corrección (F-034 R11). Así el mensaje de archivar es, byte a
    byte, el de F-031 (R26), y el gráfico y el cierre dicen lo suyo (decisión
    del humano del 2026-09-23 sobre el §2.5 de `progress/impl_F-034.md`). Los
    dos códigos identifican una obra y una reclamación, no a una persona, así
    que pueden ir en el mensaje; nada más del papel puede (F-031 R25, F-034
    R34).

    `solo_incidencia=True` es lo que necesita el cierre, cuyo cuerpo no trae
    `codigo_obra` (F-034 R16): entonces solo se coteja el número de
    incidencia. Por defecto se cotejan **los dos**, que es lo que protege
    archivar y adjuntar: un cuerpo sin obra no pasa.

    Sin `declarados` no hay nada que cotejar y se sigue adelante. Eso **no**
    abre ninguna puerta: quien llama escribe con lo guardado igual, así que el
    camino sin cotejo tampoco puede escribir con otros códigos (F-031 R11,
    F-034 R19).

    Dónde se llama es la mitad del requisito: en el punto **1 bis** de cada
    paso, **después** de la puerta de aptitud —que es la que deja la situación
    con la que se coteja— y **antes** de cualquier traza, de cualquier llamada
    al puerto y de cualquier conversación con el ERP (F-031 R5, F-034 R13).
    """
    if declarados is None:
        return
    for (etiqueta, declarado), (_, guardado) in zip(
        _a_mirar(declarados, solo_incidencia=solo_incidencia),
        _a_mirar(guardados, solo_incidencia=solo_incidencia),
        strict=True,
    ):
        if not es_el_mismo_codigo(declarado, guardado):
            raise CodigosNoCoinciden(
                f"{etiqueta} de la petición («{declarado}») no es el que consta "
                f"guardado para este parte («{guardado}»), así que {y_por_eso}"
            )


def exigir_codigos_completos(
    guardados: CodigosDelParte, *, solo_incidencia: bool = False, y_por_eso: str
) -> None:
    """Lo guardado tiene que traer el código con el que se escribe (F-034 R15).

    «Falta» es lo que `normalizar_codigo` deja vacío —ausente, vacío o de solo
    blancos—, el mismo criterio con el que el nombrado decide que falta un
    código: dos criterios del mismo concepto divergen siempre.

    Levanta `CodigoNoConsta` nombrando **cuál** falta —la obra antes que la
    incidencia— y **no** lo sustituye por el que traiga el cuerpo: eso volvería
    a dejar que el cuerpo decidiera (F-034 R19). El mensaje lleva `y_por_eso`
    —qué no se ha hecho— y termina **siempre** con la acción, que es la misma
    en cualquier endpoint: teclear el código en el parte y guardarlo. No es un
    400: la petición está bien formada y lo incompleto es lo guardado.

    `solo_incidencia=True`, en el cierre: la obra no decide nada allí y no se
    exige (F-034 R16).

    Archivar **no** la llama: allí el código vacío lo sigue diciendo el
    nombrado con `NombradoImposible`, como desde F-006 (F-034 R26).
    """
    for etiqueta, codigo in _a_mirar(guardados, solo_incidencia=solo_incidencia):
        if not normalizar_codigo(codigo):
            raise CodigoNoConsta(
                f"no consta guardado {etiqueta} de este parte, así que "
                f"{y_por_eso}: hay que teclearlo en el parte y guardarlo "
                f"(POST /api/parte) antes de volver a intentarlo"
            )
