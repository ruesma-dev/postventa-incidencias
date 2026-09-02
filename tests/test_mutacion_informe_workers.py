# tests/test_mutacion_informe_workers.py
"""Un informe de mutación sin el número de workers no se puede interpretar.

Pasó de verdad el 2026-09-02: reconstruyendo la campaña de F-009 del 2026-08-27
no se pudo determinar con cuántos workers se había lanzado, y sin ese dato el
«Tiempo total» no dice nada —3.623 s son 3,7 veces el techo teórico de una
campaña de 16 workers y encajan al 0,4 % con una campaña en serie—. La línea
`Campaña paralela: hasta N workers` la imprime el comando y se la lleva el
scrollback; el informe, que es lo que queda, no la guardaba.

Y desde que la campaña repasa en serie los mutantes en `timeout`, el informe
tiene que decir además cuántos se repasaron y a cuántos les sacó el repaso un
veredicto de verdad: sin eso, «0 timeouts» no distingue una campaña sin
incidencias de una que las tuvo y las resolvió.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import (
    MUERTO,
    InformeMutacion,
    Mutante,
    escribir_informe,
)
from harness.mutacion_paralela import ejecutar_campania_paralela, fusionar

ALCANCE = Alcance(
    feature="F-000", origen="rama", ref_diff=("dev", "rama"), lineas={"codigo.py": {2}}
)


def mutante(linea: int) -> Mutante:
    return Mutante(
        fichero="codigo.py",
        linea=linea,
        col=0,
        original="==",
        mutado="!=",
        operador="comparacion",
    )


def informe(**campos: object) -> InformeMutacion:
    base: dict[str, object] = {
        "feature": "F-000",
        "alcance": ALCANCE,
        "generados": 3,
        "muertos": 3,
        "mutantes_evaluados": [mutante(2), mutante(3), mutante(4)],
        "segundos": 120.0,
    }
    base.update(campos)
    return InformeMutacion(**base)  # type: ignore[arg-type]


def escrito(informe_: InformeMutacion, tmp_path: Path) -> str:
    destino = tmp_path / "mutacion_F-000.md"
    escribir_informe(informe_, destino)
    return destino.read_text(encoding="utf-8")


# --- Con cuántos workers se midió -------------------------------------------


def test_la_cabecera_cita_el_comando_con_sus_workers(tmp_path: Path) -> None:
    """Reproducir la campaña exige el comando entero, no medio comando."""
    texto = escrito(informe(workers=8), tmp_path)

    assert "--feature F-000 --workers 8" in texto


def test_los_totales_traen_la_fila_de_workers(tmp_path: Path) -> None:
    texto = escrito(informe(workers=8), tmp_path)

    assert "| Workers | 8 |" in texto


def test_sin_saber_los_workers_la_fila_lo_dice_en_vez_de_faltar(
    tmp_path: Path,
) -> None:
    """Una fila ausente se lee como descuido; un `n/d` se lee como lo que es."""
    texto = escrito(informe(), tmp_path)

    assert "| Workers | n/d |" in texto


def test_fusionar_registra_los_workers_de_la_campania() -> None:
    fusionado = fusionar(ALCANCE, [], generados=0, segundos=1.0, workers=4)

    assert fusionado.workers == 4


# --- Qué pasó con los timeouts ----------------------------------------------


def test_el_informe_dice_cuantos_timeouts_se_repasaron_y_cuantos_cambiaron(
    tmp_path: Path,
) -> None:
    texto = escrito(
        informe(muertos=2, timeouts=[mutante(4)], timeouts_repasados=3), tmp_path
    )

    assert "Timeouts repasados en serie" in texto
    assert "3" in texto and "2" in texto
    fila = next(
        linea for linea in texto.splitlines() if "Timeouts repasados" in linea
    )
    assert "3" in fila, f"no se ve cuántos se repasaron: {fila}"
    assert "2" in fila, f"no se ve a cuántos les sacó veredicto: {fila}"


def test_sin_un_solo_timeout_la_fila_del_repaso_lo_dice(tmp_path: Path) -> None:
    """«0 repasados» sin más se confunde con un arnés que no repasa."""
    texto = escrito(informe(), tmp_path)

    fila = next(
        linea for linea in texto.splitlines() if "Timeouts repasados" in linea
    )
    assert "ningún mutante agotó el reloj" in fila


def test_una_campania_en_serie_explica_por_que_no_repasa(tmp_path: Path) -> None:
    """En serie el reloj ya midió al mutante a solas: repasar no aportaría nada."""
    texto = escrito(
        informe(muertos=2, timeouts=[mutante(4)], timeouts_repasados=0, workers=1),
        tmp_path,
    )

    fila = next(
        linea for linea in texto.splitlines() if "Timeouts repasados" in linea
    )
    assert "serie" in fila


def test_la_seccion_de_timeouts_avisa_de_que_sobrevivieron_al_repaso(
    tmp_path: Path,
) -> None:
    """Tras el repaso, un timeout ya no tiene la contención como excusa."""
    texto = escrito(
        informe(muertos=2, timeouts=[mutante(4)], timeouts_repasados=3), tmp_path
    )

    cuerpo = texto.split("## Timeouts", 1)[1].lower()
    assert "repas" in cuerpo, "no se dice que estos ya pasaron por el repaso"
    assert "serie" in cuerpo, "no se dice que el repaso fue sin concurrencia"


# --- Lo que se registra es lo que se corrió, no lo que se pidió -------------

FUENTE = "def clasifica(a, b):\n    if a == b:\n        return a > b\n    return None\n"


class EjecutorQueMata:
    def ejecutar(self, _timeout_s: int) -> str:
        return MUERTO


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Alcance, str]:
    def _git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(tmp_path), *args], capture_output=True, check=True
        )

    (tmp_path / "codigo.py").write_text(FUENTE, encoding="utf-8")
    _git("init", "-q")
    _git("config", "user.email", "arnes@ejemplo.invalid")
    _git("config", "user.name", "Arnes")
    _git("add", "codigo.py")
    _git("commit", "-q", "-m", "base")
    alcance = Alcance(
        feature="F-000",
        origen="rama",
        ref_diff=("dev", "feature/x"),
        lineas={"codigo.py": {2, 3}},
    )
    return (alcance, str(tmp_path))


def test_la_campania_registra_los_workers_que_de_verdad_corrieron(
    repo: tuple[Alcance, str],
) -> None:
    """Pedir 99 workers con 4 mutantes no arranca 99: el informe dice los reales."""
    alcance, raiz = repo

    resultado = ejecutar_campania_paralela(
        alcance,
        servicios=[],
        timeout_s=5,
        raiz=raiz,
        workers=99,
        fabrica=lambda _fichero, _raiz: EjecutorQueMata(),
    )

    assert resultado.workers == resultado.evaluados
    assert resultado.workers is not None and resultado.workers < 99
