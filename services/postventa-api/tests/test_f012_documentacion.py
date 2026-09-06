# services/postventa-api/tests/test_f012_documentacion.py
"""La documentación que F-012 deja al día (R68, R69, y T19/T20 de `tasks.md`).

Al modo de `test_f009_documentacion.py`. Un documento desactualizado que parece
vigente hace más daño que no tenerlo, y aquí vale doble por dos motivos: lo que
estos documentos describen es **una escritura en un ERP de producción**, y una
de las cosas que declaran —las App Settings de la pasarela— es **configuración
de otro proyecto**, que su dueño solo puede respetar si sabe que dependemos de
ella.

Lo que fija:

- **R68** · `docs/INTEGRACION.md` dice que consumimos el endpoint, qué escribe,
  qué precondiciones exige y qué se rompe si su dueño las cambia. Con los
  nombres de las variables y **ningún valor**.
- **R69** · `docs/ARCHITECTURE.md` deja de describir el riesgo aceptado de
  F-009 como vigente: el paso 7 pasa a 7a/7b y el riesgo consta **cerrado**,
  con fecha y feature.
- **`docs/DESPLIEGUE.md`** explica que la ventana de escritura cubre las dos
  escrituras y que **no hay un interruptor nuevo**.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"

#: Las dos variables que F-012 añade. Se nombran; sus valores, jamás.
VARIABLES_DE_F012 = ("SIGRID_GRATIPIDE_PARTE", "GRAFICO_MAX_BYTES")

#: Las App Settings **de la pasarela** de las que dependemos y que **no
#: controlamos**. Declararlas es lo que convierte una dependencia invisible en
#: una precondición que su dueño puede respetar.
PRECONDICIONES_DE_LA_PASARELA = (
    "SIGRID_DOCUMENT_WRITE_ENABLED",
    "SIGRID_DOCUMENT_WRITE_DATABASE",
    "SIGRID_DOCUMENT_ALLOWED_CONTIP",
    "SIGRID_DOCUMENT_ALLOWED_GRATIPIDE",
    "SIGRID_DOCUMENT_MAX_BYTES",
)

#: Un nombre de host real de la pasarela o del servidor de base de datos.
PATRON_HOST_AZURE = re.compile(
    r"[\w-]+\.(?:azurewebsites\.net|postgres\.database\.azure\.com)",
    re.IGNORECASE,
)

#: Una clave de función: una cadena larga en base64url pegada a la variable.
PATRON_VALOR_DE_SECRETO = re.compile(
    r"SIGRID_API_KEY\s*[=:]\s*[\"']?[A-Za-z0-9+/=_-]{20,}",
)

DOCUMENTOS = (ARQUITECTURA, INTEGRACION, DESPLIEGUE)


# --------------------------------------------------------------------------
# R68 · INTEGRACION.md: el endpoint, lo que escribe y sus precondiciones
# --------------------------------------------------------------------------


def test_f012_r68_integracion_declara_el_endpoint_que_consumimos():
    """R68 · con su ruta exacta.

    Quien administre la pasarela tiene que poder buscar el nombre del endpoint
    y encontrar quién lo usa. «El endpoint de gráficos» no se puede buscar.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "/api/sigrid/concepto-grafico" in texto


def test_f012_r68_integracion_dice_que_son_tres_filas_en_dos_bases():
    """R68 · es lo que distingue esta escritura de todas las anteriores.

    Quien lea «adjuntamos un documento» no sabe que se toca la base documental;
    quien lea «tres filas en dos bases» sí, y esa es justo la parte que a su
    dueño le importa.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "tres filas en dos bases" in texto
    assert "base documental" in texto


def test_f012_r68_integracion_dice_que_el_grafico_va_antes_del_cierre():
    """R68 · el orden **es** la garantía, y no un detalle de implementación."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "orden más idempotencia" in texto
    assert "exige" in texto and "adjuntado" in texto


def test_f012_r68_integracion_dice_que_nunca_nombramos_la_base_documental():
    """R68 · la elige la pasarela, y decirlo evita que su dueño crea que le
    estamos pasando el nombre de una base por parámetro."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "Nunca nombramos la documental" in texto


@pytest.mark.parametrize("variable", VARIABLES_DE_F012)
def test_f012_r68_integracion_nombra_las_dos_variables_nuevas(variable):
    """R68 · sin esto, la lista de variables solo vive en el código."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert variable in texto, f"INTEGRACION.md no nombra {variable}"


@pytest.mark.parametrize("variable", PRECONDICIONES_DE_LA_PASARELA)
def test_f012_r68_integracion_declara_las_precondiciones_de_la_pasarela(variable):
    """R68 · **lo más importante de esta sección.**

    Son App Settings de **otro proyecto**. Si su dueño no sabe que dependemos
    de ellas, las cambiará un día por un motivo razonable y este servicio
    dejará de poder cerrar incidencias sin que nadie relacione las dos cosas.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert variable in texto, f"INTEGRACION.md no declara {variable}"


def test_f012_r68_integracion_dice_que_esas_precondiciones_no_se_tocan_desde_aqui():
    """R68 · declararlas sin decir de quién son invita a «arreglarlas»."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "no se tocan desde aquí" in texto or "no se toca desde aquí" in texto
    assert "dueño de `sigrid-api`" in texto


def test_f012_r68_integracion_dice_que_se_rompe_si_apagan_la_documental():
    """R68 · §6, y con el código HTTP que verá quien lo sufra.

    Un «dejaría de funcionar» no sirve para diagnosticar: un **503 nombrando la
    precondición** sí.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "SIGRID_DOCUMENT_WRITE_ENABLED" in texto
    assert "503" in texto
    assert "El ERP queda intacto" in texto


def test_f012_r68_la_nota_de_que_f012_no_tiene_por_donde_hacerse_esta_resuelta():
    """R68 · la nota decía que subir el PDF **no tenía por dónde hacerse**.

    Se conserva como historia —explica de dónde viene la precondición— pero
    tiene que constar resuelta, o quien la lea abandonará antes de empezar.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "RESUELTO el 2026-09-06" in texto
    # Sin el salto de línea del documento: lo que se fija es la afirmación,
    # no dónde decidió cortar el párrafo quien lo escribió.
    plano = " ".join(texto.split())
    assert "F-012 no cruza ninguna frontera" in plano


def test_f012_r68_integracion_declara_el_endpoint_nuevo_que_exponemos():
    """R68 · `/api/adjuntar` en la tabla de §8, con lo que escribe."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "`POST /api/adjuntar`" in texto
    assert "Los once quedan en nivel" in texto


# --------------------------------------------------------------------------
# R69 · ARCHITECTURE.md: el paso 7a/7b y el riesgo cerrado
# --------------------------------------------------------------------------


def test_f012_r69_arquitectura_declara_el_paso_7a_del_grafico():
    """R69 · el pipeline tiene un paso más, y va **delante** del cierre."""
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "7a. **Gráfico** (F-012)" in texto
    assert "7b. **Cierre** (F-009)" in texto
    assert texto.index("7a. **Gráfico**") < texto.index("7b. **Cierre**")


def test_f012_r69_el_riesgo_aceptado_consta_cerrado_con_fecha_y_feature():
    """R69 · **lo que pedía la tarea**: cerrado, con fecha y con feature.

    Un riesgo que sigue leyéndose como vigente manda a quien lo lea a tomar
    precauciones que ya no hacen falta — y, peor, le hace desconfiar de un
    circuito que sí está completo.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "RIESGO ACEPTADO · CERRADO el 2026-09-06 por F-012" in texto
    assert "ya no está vigente" in texto


def test_f012_r69_el_texto_historico_del_riesgo_se_conserva_en_pasado():
    """R69 · conservarlo es lo que explica por qué el orden es el que es.

    Los literales que `test_f009_documentacion.py` fija siguen ahí —«RIESGO
    ACEPTADO», «sin ninguna fila en `rcg`», «2.365», «fecha de caducidad»,
    «F-012»—, y esos dos tests conviven a propósito: uno exige que el texto
    esté, este exige que ya no se lea como presente.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "iba a producir" in texto
    assert "Aquellos cierres habrían sido" in texto
    # Y la afirmación en presente, la que mandaba a preocuparse, no puede estar.
    assert "este servicio va a producir reclamaciones en" not in texto


def test_f012_r69_arquitectura_dice_que_la_decision_del_dueno_ya_esta_tomada():
    """R69 · la nota decía que hacía falta una decisión ajena. Ya está tomada,
    y el documento tiene que decirlo o seguirá pareciendo un bloqueo."""
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "La tomó él, y está desplegada" in texto
    assert "/api/sigrid/concepto-grafico" in texto


@pytest.mark.parametrize("variable", VARIABLES_DE_F012)
def test_f012_r69_la_tabla_de_sistemas_externos_nombra_las_variables_nuevas(
    variable,
):
    """R69 · la tabla es donde se mira «qué configura este sistema»."""
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert variable in texto


def test_f012_r69_la_tabla_distingue_los_dos_reintentos():
    """R69 · **la diferencia que más caro sale confundir.**

    El cierre no se reintenta solo; el gráfico sí es seguro reintentarlo. Quien
    lea que «la escritura no se reintenta jamás» y lo aplique al gráfico dejará
    partes sin adjuntar por prudencia mal entendida.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "idempotente por tamaño y `sha256`" in texto


# --------------------------------------------------------------------------
# DESPLIEGUE.md · una sola ventana, y las dos App Settings
# --------------------------------------------------------------------------


def test_f012_despliegue_dice_que_la_ventana_cubre_las_dos_escrituras():
    """La ventana es **una**, y quien la abra tiene que saber qué abre."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "`/api/adjuntar` y `/api/cerrar`" in texto
    assert "Una sola variable para las dos escrituras" in texto


def test_f012_despliegue_dice_que_no_hay_un_interruptor_nuevo_y_por_que():
    """Un «no hay» sin porqué es un «no hay» que el siguiente cambia."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "No hay `GRAFICO_HABILITADO`" in texto
    assert "primera mitad del cierre" in texto


def test_f012_despliegue_avisa_de_que_abrir_para_el_grafico_abre_el_cierre():
    """Es la consecuencia de compartir ventana, y hay que saberla **antes**."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "abre también el cierre" in texto


def test_f012_despliegue_declara_la_secuencia_de_un_cierre_real_con_grafico():
    """La secuencia es el procedimiento, y ahora tiene dos llamadas más."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "leer los dos dry-run" in texto.replace("**", "").replace("\n", " ")
    assert "solo si responde" in texto.replace("**", "")


@pytest.mark.parametrize("variable", VARIABLES_DE_F012)
def test_f012_despliegue_declara_las_dos_app_settings_nuevas(variable):
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert variable in texto


# --------------------------------------------------------------------------
# Ningún valor, en ninguno de los tres
# --------------------------------------------------------------------------


@pytest.mark.parametrize("documento", DOCUMENTOS, ids=lambda ruta: ruta.name)
def test_f012_r68_ningun_documento_trae_el_valor_de_un_secreto(documento):
    """R68 · se nombran las variables y **jamás** sus valores.

    Es la misma regla que F-009 puso sobre `INTEGRACION.md`, extendida a los
    tres documentos que F-012 toca: el historial de git no suelta lo que entra.
    """
    texto = documento.read_text(encoding="utf-8")

    assert PATRON_VALOR_DE_SECRETO.search(texto) is None
    assert PATRON_HOST_AZURE.search(texto) is None
