# services/postventa-api/tests/test_f010_prompt_keys_infra.py
"""Toda clave de prompt que fijen los scripts de `infra/` existe en el YAML.

**Por qué existe este fichero, con nombre y fecha.** El 2026-08-21, el
despliegue real de F-010 salió con `PROMPT_KEY_FIRMA=firma_cliente_es` en
`desplegar_backend.ps1`. El prompt real es `firma_parte_es`. Fue el más grave
de los doce defectos de esa jornada precisamente porque **no impedía
desplegar ni entrar**: la aplicación quedaba en pie, el usuario iniciaba
sesión, soltaba su remesa y **todas las lecturas fallaban con un 500** sin
explicación. En los registros, y solo ahí, aparecía el motivo:
`PromptNoEncontrado: el prompt 'firma_cliente_es' no está en ...`.

El valor ya está corregido. Lo que este fichero añade es que **no pueda
volver**: es un descuido de una sola letra en un fichero que ningún test
tocaba, en un valor que solo se usa en el entorno desplegado. Nadie lo ve
leyendo el diff, y el sistema no se cae al arrancar: se cae al usarlo.

El planteamiento es el de `test_f010_scripts_infra.py` —los `.ps1` no entran
ni en la cobertura ni en la campaña de mutación, así que lo que sobrevive a la
siguiente edición es un test que los lee como texto—, con una diferencia que
importa: aquí no se compara contra una lista escrita a mano, sino contra el
**fichero de prompts de verdad**, cargado por el **mismo repositorio** que usa
el servicio en producción. Si el YAML cambia, el test cambia con él sin que
nadie lo mantenga.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.errores import PromptNoEncontrado
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables.
INFRA = RAIZ / "infra"

#: El fichero de prompts que se despliega, relativo al servicio. Se resuelve
#: dentro de `RepositorioPromptsYaml`, igual que en producción.
RUTA_DE_PRODUCCION = "config/prompts.yaml"

#: Cualquier App Setting cuyo nombre empiece por `PROMPT_KEY` y su valor.
#: Cubre `PROMPT_KEY`, `PROMPT_KEY_FIRMA` y las que vengan después sin tener
#: que volver aquí a añadirlas: el día que F-015 traiga un tercer prompt, su
#: clave queda vigilada sola.
PATRON_PROMPT_KEY = re.compile(r"\b(PROMPT_KEY[A-Z0-9_]*)\s*=\s*([^\s\"',]+)")


def claves_fijadas_en(texto: str) -> tuple[tuple[str, str], ...]:
    """Los pares (variable, valor) que ese texto fija, ya sin las de PowerShell.

    Un valor que empieza por `$` es una variable de PowerShell, no una clave:
    lo que llegue ahí lo decide otro sitio y este barrido no puede juzgarlo.
    """
    return tuple(
        (variable, valor)
        for variable, valor in PATRON_PROMPT_KEY.findall(texto)
        if not valor.startswith("$")
    )


def claves_de_infra() -> tuple[tuple[str, str, str], ...]:
    """Los tríos (script, variable, valor) de todos los `.ps1` de `infra/`.

    Se compone leyendo el directorio y no a mano, por el mismo motivo que en
    `test_f010_scripts_infra.py`: una lista fija dejaría fuera del barrido al
    siguiente script sin que se note, que es exactamente como se coló el valor
    que originó este fichero.
    """
    return tuple(
        (script.name, variable, valor)
        for script in sorted(INFRA.glob("*.ps1"))
        for variable, valor in claves_fijadas_en(script.read_text(encoding="ascii"))
    )


@pytest.fixture(scope="module")
def prompts() -> RepositorioPromptsYaml:
    """El repositorio de prompts de producción, cargado como lo carga el servicio."""
    return RepositorioPromptsYaml(RUTA_DE_PRODUCCION)


def test_f010_el_barrido_encuentra_alguna_clave_en_los_scripts():
    """Un barrido que no barre nada pasa siempre y no protege nada.

    Si alguien renombra la App Setting, cambia el entrecomillado o mueve los
    scripts de sitio, el test de abajo se quedaría sin casos y seguiría en
    verde. Este lo impide: mientras el despliegue fije una clave de prompt,
    aquí tiene que aparecer.
    """
    encontradas = claves_de_infra()

    assert encontradas != (), (
        "ningún script de infra/ fija un PROMPT_KEY*: o el despliegue dejó de "
        "fijarlos, o el patrón ya no reconoce cómo se escriben"
    )


@pytest.mark.parametrize(
    ("script", "variable", "valor"),
    claves_de_infra(),
    ids=lambda dato: str(dato),
)
def test_f010_cada_prompt_key_de_infra_existe_en_el_yaml(
    prompts, script, variable, valor
):
    """El valor que se despliega tiene que ser una clave real del YAML.

    Se comprueba pidiéndoselo al repositorio de verdad, no mirando una lista:
    así el fallo del test es **el mismo** `PromptNoEncontrado` que vería el
    usuario en el entorno desplegado, con las claves disponibles dentro del
    mensaje. Quien lo lea sabrá en el acto cuál quiso escribir.
    """
    try:
        prompt = prompts.obtener(valor)
    except PromptNoEncontrado as error:
        pytest.fail(
            f"infra/{script} fija {variable}={valor}, que no existe en "
            f"{RUTA_DE_PRODUCCION}. El despliegue quedaría en pie y roto: "
            f"toda lectura que use ese prompt responderá 500. Detalle: {error}"
        )

    assert prompt.clave == valor


def test_f010_el_barrido_de_prompt_keys_caza_un_valor_inventado(prompts):
    """Control negativo: un patrón que nunca se ha visto saltar no protege nada.

    Se reproduce **la línea exacta** que se desplegó el 2026-08-21, con su
    valor inventado, sobre un texto en memoria. Tiene que extraerse y tiene que
    ser rechazada por el repositorio.
    """
    linea = '    "PROMPT_KEY_FIRMA=firma_cliente_es",'

    extraidas = claves_fijadas_en(linea)

    assert extraidas == (("PROMPT_KEY_FIRMA", "firma_cliente_es"),)
    with pytest.raises(PromptNoEncontrado):
        prompts.obtener(extraidas[0][1])


def test_f010_el_barrido_de_prompt_keys_ignora_las_variables_de_powershell():
    """Un guardián que grita con todo se acaba desactivando.

    Un valor tomado de una variable no es una clave escrita a mano: este
    barrido lee texto, no ejecuta PowerShell, y no puede juzgar lo que valga
    esa variable. Decirlo aquí evita que el día que alguien parametrice la
    clave el test empiece a fallar por algo que no es un defecto.
    """
    assert claves_fijadas_en('"PROMPT_KEY=$PostventaPromptExtraccion",') == ()
