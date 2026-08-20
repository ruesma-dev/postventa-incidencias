# services/postventa-api/application/pipelines/confianza.py
"""El saneo de la confianza declarada por el modelo, en un solo sitio.

Nació dentro de `paso_extraccion.py` (F-003, R4) y se saca aquí en F-004
porque la lectura de la firma necesita **exactamente la misma** regla. Dos
copias de una regla numérica divergen el día que alguien decida, por ejemplo,
que un decimal se redondea; y en una campaña de mutación cada copia se cuenta
aparte, con lo que la segunda queda sin tests que la maten.

El comportamiento no cambia ni un caso respecto a F-003: la prueba de que el
refactor está bien hecho es que los tests de aquella feature pasan **sin
tocarlos**.
"""

from __future__ import annotations

#: Extremos de la confianza declarada (F-003, R3).
CONFIANZA_MINIMA = 0
CONFIANZA_MAXIMA = 100


def sanear_confianza(declarada: object) -> tuple[int, str | None]:
    """La confianza dentro de `0–100`, y el aviso si hubo que tocarla.

    Nunca se descarta el valor leído por culpa de la confianza: una confianza
    mal formada no invalida lo leído, lo hace **sospechoso**. Quien decide qué
    hacer con esa sospecha es la validación (F-004), no este saneo.
    """
    entero = _a_entero(declarada)
    if entero is None:
        return CONFIANZA_MINIMA, "la confianza declarada no es un entero, se deja en 0"
    if entero < CONFIANZA_MINIMA:
        return CONFIANZA_MINIMA, f"confianza {entero} fuera de rango, se ajusta a 0"
    if entero > CONFIANZA_MAXIMA:
        return CONFIANZA_MAXIMA, f"confianza {entero} fuera de rango, se ajusta a 100"
    return entero, None


def _a_entero(valor: object) -> int | None:
    """El entero que declara ese valor, o `None` si no declara ninguno.

    Un `bool` **no** cuenta: en Python es un `int`, y `True` colaría como
    confianza 1. Un entero escrito como texto (`"85"`) sí, porque los modelos
    lo devuelven así más a menudo de lo que reconocen y tirar por eso una
    lectura buena sería absurdo. Un decimal (`"85.0"`, `85.5`) no: redondearlo
    sería inventarse una regla que el schema no declara, y el schema dice
    `integer`.
    """
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().lstrip("-").isdigit():
        return int(valor.strip())
    return None
