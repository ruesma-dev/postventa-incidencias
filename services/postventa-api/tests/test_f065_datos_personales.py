# services/postventa-api/tests/test_f065_datos_personales.py
"""Los datos personales de las reclamaciones de Sigrid (F-065, T7; R37, R38, R39).

`specs/F-065-revision-sigrid-backend/design.md` §8 (Q-6, N-3): los datos de la
lista cerrada de R33 **sí** se sirven a la página, y **nunca** se guardan en la
base ni en un fichero (R37), **nunca** van a un log ni a una traza (R38) y
**nunca** hay uno real en el repositorio (R39).

| Caso | Requisito |
|---|---|
| la ruta no escribe nada en la base: el doble de `RevisionPort` no recibe ninguna escritura | R37 |
| la ruta no abre ningún fichero; las piezas nuevas no escriben ficheros ni guardan nada entre peticiones | R37 |
| con fichas inventadas, **ningún** registro de la ruta ni del adaptador lleva uno de sus valores, ni con 200 ni con error | R38 |
| los tests, `specs/` y `progress/` de F-065 solo traen correos `@ejemplo.invalid` (con su control no ciego) | R39 |

Datos inventados (R39): obra `9901`, «Ejemplo …», `000 000 00n`,
`@ejemplo.invalid`.
"""

from __future__ import annotations

import ast
import builtins
import logging
import re
import traceback
from pathlib import Path

import pytest
from domain.models.errores import CatalogoNoDisponible, PersistenciaNoDisponible

from tests.test_f065_adaptador import SECRETOS as SECRETOS_DEL_ADAPTADOR
from tests.test_f065_adaptador import _adaptador, _fila, _lectura
from tests.test_f065_aplicacion import (
    OBRA_REF,
    OTRA_OBRA_REF,
    BandejaSoloLectura,
    fila,
    obra_de_ejemplo,
    valores_de_la_ficha,
)
from tests.test_f065_dominio import sit
from tests.test_f065_http import Mundo, _componer, _get, _leer
from tests.utiles_revision import RevisionEnMemoria

SERVICIO = Path(__file__).resolve().parents[1]
RAIZ = SERVICIO.parents[1]

#: Las piezas de producción nuevas de F-065 que la ruta compone.
PIEZAS_DE_LA_RUTA = (
    SERVICIO / "application" / "pipelines" / "sigrid_bandeja.py",
    SERVICIO / "interface_adapters" / "api" / "sigrid_bandeja.py",
    SERVICIO / "domain" / "models" / "sigrid_bandeja.py",
    SERVICIO / "domain" / "ports" / "reclamaciones_obra.py",
    SERVICIO / "infrastructure" / "sigrid" / "consultas_reclamaciones_obra.py",
    SERVICIO / "infrastructure" / "sigrid" / "reclamaciones_obra.py",
)


def _registros(caplog) -> str:
    """Todo lo registrado por cualquier logger, con las trazas de las excepciones."""
    partes = []
    for registro in caplog.records:
        partes.append(f"{registro.name} {registro.getMessage()}")
        if registro.exc_info:
            partes.append("".join(traceback.format_exception(*registro.exc_info)))
    return "\n".join(partes)


def _secretos_de(filas) -> set[str]:
    """Los valores de R6 y R33 de unas filas del puerto: ninguno va a un log."""
    secretos = {OBRA_REF, OTRA_OBRA_REF}
    for f in filas:
        secretos.update(
            v
            for v in (f.cod, f.unidad_codigo, f.ubicacion, f.descripcion, f.referencia, f.oficio_nombre, f.tipo_nombre)
            if v
        )
        secretos.update(valores_de_la_ficha(f.ficha))
    return secretos


# ==========================================================================
# R37 · nada se guarda: ni en la base ni en un fichero
# ==========================================================================


def test_f065_r37_la_ruta_no_escribe_nada_en_la_base(monkeypatch) -> None:
    situaciones, filas = obra_de_ejemplo()
    mundo = Mundo(situaciones, filas)
    _componer(monkeypatch, mundo)

    estado, _ = _leer(_get())

    assert estado == 200
    # `BandejaSoloLectura`: cualquier operación que no sea `listar` o `contar` falla.
    assert mundo.llamadas == ["revision.listar", "sigrid.leer"]


def test_f065_r37_con_el_repositorio_en_memoria_entero_no_queda_ninguna_escritura(monkeypatch) -> None:
    """Con el doble completo de F-056 (que sí sabe registrar): ni una revisión ni un lote."""
    mundo = Mundo()
    memoria = RevisionEnMemoria(mundo.llamadas)
    memoria.listar_devuelve = obra_de_ejemplo()[0]
    mundo.con_la_bandeja(memoria)
    mundo.lector.filas = obra_de_ejemplo()[1]
    _componer(monkeypatch, mundo)

    estado, _ = _leer(_get())

    assert estado == 200
    assert memoria.registros == []
    assert memoria.guardadas == []
    assert mundo.llamadas == ["revision.listar", "sigrid.leer"]


def test_f065_r37_la_ruta_no_abre_ningun_fichero(monkeypatch) -> None:
    situaciones, filas = obra_de_ejemplo()
    mundo = Mundo(situaciones, filas)
    _componer(monkeypatch, mundo)
    assert _get().status_code == 200  # lo que se importe la primera vez, ya importado

    def sin_ficheros(*_args, **_kwargs):
        raise AssertionError("la ruta ha intentado abrir un fichero")

    monkeypatch.setattr(builtins, "open", sin_ficheros)
    monkeypatch.setattr(Path, "write_text", sin_ficheros)
    monkeypatch.setattr(Path, "write_bytes", sin_ficheros)
    monkeypatch.setattr(Path, "open", sin_ficheros)

    estado, cuerpo = _leer(_get())

    assert estado == 200
    assert len(cuerpo["reclamaciones"]) == len(filas)


#: Lo que en una pieza de la ruta sería guardar algo: un fichero, una caché o
#: un estado de módulo con datos.
_GUARDAR = re.compile(
    r"\bopen\(|write_text|write_bytes|\.write\(|tempfile|shelve|pickle|sqlite|lru_cache|\bcache\b|functools"
)


@pytest.mark.parametrize("ruta", PIEZAS_DE_LA_RUTA, ids=lambda r: r.name + "@" + r.parent.name)
def test_f065_r37_ninguna_pieza_de_la_ruta_escribe_ficheros_ni_guarda_entre_peticiones(ruta: Path) -> None:
    """Sobre lo que se **ejecuta**: sin docstrings ni comentarios."""
    assert _GUARDAR.findall(_codigo_que_se_ejecuta(ruta.read_text(encoding="utf-8"))) == []


def _codigo_que_se_ejecuta(fuente: str) -> str:
    arbol = ast.parse(fuente)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(cuerpo[0].value, ast.Constant):
                nodo.body = cuerpo[1:] or [ast.Pass()]
    return ast.unparse(arbol)


def test_f065_r37_el_detector_de_guardar_no_es_ciego() -> None:
    assert _GUARDAR.findall("with open('x', 'w') as f:")
    assert _GUARDAR.findall("Path('x').write_text(datos)")
    assert _GUARDAR.findall("@functools.lru_cache")
    assert not _GUARDAR.findall("cuerpo = {'reclamaciones': []}")
    # Lo que se explica no cuenta; lo que se ejecuta, sí.
    assert _GUARDAR.findall(_codigo_que_se_ejecuta('"""Sin caché."""\nx = 1\n')) == []
    assert _GUARDAR.findall(_codigo_que_se_ejecuta('"""Doc."""\nf = open("x")\n')) == ["open("]


def test_f065_r37_las_piezas_de_la_ruta_no_importan_la_persistencia_salvo_su_fabrica() -> None:
    """Solo `construir_revision` (la lectura de la bandeja): ni sentencias ni repositorios."""
    culpables = {}
    for ruta in PIEZAS_DE_LA_RUTA:
        importados = set()
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.ImportFrom) and nodo.module and "persistencia" in nodo.module:
                importados.update(f"{nodo.module}.{a.name}" for a in nodo.names)
            elif isinstance(nodo, ast.Import):
                importados.update(a.name for a in nodo.names if "persistencia" in a.name)
        if importados - {"infrastructure.persistencia.fabrica.construir_revision"}:
            culpables[ruta.name] = sorted(importados)

    assert culpables == {}


# ==========================================================================
# R38 · ningún dato de una reclamación en un log, tampoco con error
# ==========================================================================


def test_f065_r38_con_200_ningun_registro_lleva_un_valor_de_las_fichas(monkeypatch, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    situaciones, filas = obra_de_ejemplo()
    mundo = Mundo(situaciones, filas)
    _componer(monkeypatch, mundo)

    respuesta = _get()

    assert respuesta.status_code == 200
    texto = respuesta.get_body().decode("utf-8")
    secretos = _secretos_de(filas) - {OBRA_REF, OTRA_OBRA_REF}
    assert all(s in texto for s in secretos), "los valores tienen que estar en la respuesta (Q-6)"
    registros = _registros(caplog)
    assert registros
    assert sorted(s for s in _secretos_de(filas) if s in registros) == []


@pytest.mark.parametrize("caso", ["techo", "ambigua", "sigrid", "base"])
def test_f065_r38_con_error_ningun_registro_lleva_un_valor_de_las_fichas(monkeypatch, caplog, caso) -> None:
    caplog.set_level(logging.DEBUG)
    situaciones, filas = obra_de_ejemplo()
    if caso == "ambigua":
        filas = (*filas, fila("RS26.09/0999", obra_ref=OTRA_OBRA_REF, n=11))
    mundo = Mundo(
        situaciones,
        filas,
        al_techo=caso == "techo",
        fallo=CatalogoNoDisponible("sin red") if caso == "sigrid" else None,
    )
    if caso == "base":
        mundo.con_la_bandeja(BandejaSoloLectura(mundo.llamadas, fallo=PersistenciaNoDisponible("sin base")))
    _componer(monkeypatch, mundo)

    respuesta = _get()

    assert respuesta.status_code in {409, 503}
    registros = _registros(caplog)
    assert sorted(s for s in _secretos_de(filas) if s in registros) == []
    cuerpo = respuesta.get_body().decode("utf-8")
    assert sorted(s for s in _secretos_de(filas) if s in cuerpo) == []


@pytest.mark.parametrize(
    "respuesta_de_sigrid",
    ["entera", "truncated", "dos-obras", "sin-truncated"],
)
def test_f065_r38_ni_la_ruta_ni_el_adaptador_de_verdad_registran_nada_de_una_fila(
    monkeypatch, caplog, respuesta_de_sigrid
) -> None:
    """Con el adaptador real y el `ClienteFalso`: lo que registra el adaptador, también."""
    caplog.set_level(logging.DEBUG)
    filas = [_fila("RS26.09/0123"), _fila("RS26.09/0124")]
    if respuesta_de_sigrid == "dos-obras":
        filas.append(_fila("RS26.09/0125", obride=7002))
    lectura = _lectura(filas, truncada=respuesta_de_sigrid == "truncated")
    if respuesta_de_sigrid == "sin-truncated":
        lectura._cuerpo.pop("truncated")
    mundo = Mundo((sit(1),))
    mundo.lector, _ = _adaptador(lectura)
    _componer(monkeypatch, mundo)

    respuesta = _get()

    esperado = {"entera": 200, "truncated": 409, "dos-obras": 409, "sin-truncated": 503}
    assert respuesta.status_code == esperado[respuesta_de_sigrid]
    registros = _registros(caplog)
    assert "F-065 reclamaciones de la obra" in registros or respuesta_de_sigrid == "sin-truncated"
    assert "F-065 sigrid de la bandeja" in registros
    assert [s for s in SECRETOS_DEL_ADAPTADOR if s in registros] == []
    assert "7002" not in registros


# ==========================================================================
# R39 · solo datos inventados en los ficheros de F-065
# ==========================================================================

#: Un correo, en cualquier texto.
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
DOMINIO_FICTICIO = "@ejemplo.invalid"


def _ficheros_de_f065() -> list[Path]:
    ficheros = sorted((SERVICIO / "tests").glob("test_f065_*.py"))
    ficheros += sorted(p for p in (RAIZ / "specs" / "F-065-revision-sigrid-backend").rglob("*") if p.is_file())
    ficheros += sorted(p for p in (RAIZ / "progress").glob("*F-065*") if p.is_file())
    return ficheros


def _correos_reales(texto: str) -> list[str]:
    return [c for c in CORREO.findall(texto) if not c.lower().endswith(DOMINIO_FICTICIO)]


def test_f065_r39_los_ficheros_de_f065_solo_traen_correos_inventados() -> None:
    ficheros = _ficheros_de_f065()
    culpables = {
        str(f.relative_to(RAIZ)): _correos_reales(f.read_text(encoding="utf-8"))
        for f in ficheros
        if _correos_reales(f.read_text(encoding="utf-8"))
    }

    assert culpables == {}


def test_f065_r39_el_barrido_mira_los_ficheros_que_tiene_que_mirar() -> None:
    nombres = {f.name for f in _ficheros_de_f065()}

    assert {
        "test_f065_aplicacion.py",
        "test_f065_http.py",
        "test_f065_datos_personales.py",
        "test_f065_dominio.py",
        "requirements.md",
        "design.md",
        "tasks.md",
        "impl_F-065.md",
        "review_F-065.md",
    } <= nombres


def test_f065_r39_el_detector_de_correos_no_es_ciego() -> None:
    # Compuestos en tiempo de ejecución: escritos enteros, el propio barrido los vería aquí.
    arroba = "@"
    real, otro, casi = (
        f"persona.real{arroba}empresa.es",
        f"otra{arroba}dominio.com",
        f"alguien{arroba}ejemplo.invalido",
    )

    assert _correos_reales(f"escribe a {real} o a {otro}") == [real, otro]
    assert _correos_reales("avisos@ejemplo.invalid, Reclama@Ejemplo.Invalid") == []
    assert _correos_reales("@app.route y @dataclass(frozen=True)") == []
    assert _correos_reales(casi) == [casi]
