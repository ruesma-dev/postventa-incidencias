<!-- progress/impl_postreview_F-002.md -->
# Post-review de F-002 — las tres decisiones abiertas

Rama `chore/postreview-F-002`, salida de `feature/F-002-ingesta-troceado`
(el cambio de código depende del código de F-002, que aún no está en `dev`).
Sin `push` y sin PR. `harness/features.json` no se ha tocado.

**Estado: dos trabajos y medio cerrados y uno bloqueado en su último paso.**
Los trabajos 1, 2 y 3 están hechos y commiteados, incluida la propagación a
`arnes-base`. Lo único que queda en el aire es el **paso 4 del trabajo 3** —
subir `harness/VERSION` de este repositorio a 1.5.1—, porque la premisa del
encargo no se cumple: `arnes-base` **ya estaba en 1.5.1** con otro cambio que
este repositorio no tiene. Detalle y decisión al final.

---

## Trabajo 1 · El PDF válido de 0 páginas ya no se descarta en silencio

Commit `46f9afc`. Ficheros:

| Fichero | Qué cambia |
|---|---|
| `services/postventa-api/tests/utiles_pdf.py` | nueva `pdf_sin_paginas()` |
| `services/postventa-api/tests/test_f002_troceado.py` | el test nuevo |
| `services/postventa-api/application/pipelines/paso_troceado.py` | el aviso |

### La fase RED, con la traza real

El test se escribió antes que el arreglo. Comando exacto:

```
cd services/postventa-api
./.venv/Scripts/python.exe -m pytest \
  tests/test_f002_troceado.py::test_f002_pdf_valido_de_cero_paginas_se_descarta_con_aviso -q
```

Salida (recortada al fallo; los colores del terminal, quitados):

```
_________ test_f002_pdf_valido_de_cero_paginas_se_descarta_con_aviso __________

    def test_f002_pdf_valido_de_cero_paginas_se_descarta_con_aviso():
        """Lo que se descarta, se nombra: también el PDF que no tiene páginas.
        ...
        """
        contexto = _trocear(
            [
                DocumentoEntrada(nombre="vacio.pdf", contenido=pdf_sin_paginas()),
                DocumentoEntrada(nombre="remesa.pdf", contenido=remesa_sintetica([1])),
            ]
        )

        assert [parte.origen for parte in contexto.partes] == ["remesa.pdf"]
>       assert contexto.avisos == ["vacio.pdf: descartado, el PDF no tiene páginas"]
E       AssertionError: assert [] == ['vacio.pdf: ...iene páginas']
E
E         Right contains one more item: 'vacio.pdf: descartado, el PDF no tiene páginas'
E         Use -v to get more diff

tests\test_f002_troceado.py:293: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f002_troceado.py::test_f002_pdf_valido_de_cero_paginas_se_descarta_con_aviso - AssertionError: assert [] == ['vacio.pdf: ...iene páginas']
1 failed in 0.43s
```

El rojo es el que interesa: **la primera aserción ya pasaba** (el fichero
efectivamente no producía ningún parte) y lo que faltaba era exactamente el
aviso — `contexto.avisos == []`. Es el defecto que describía la observación 1
de la review, reproducido.

### El fixture: por qué se arma a mano

`pdf_con_textos([])` **no sirve** para fabricar el caso: PyMuPDF se niega a
escribir un PDF sin páginas.

```
ValueError: cannot save with zero pages
```

Lo mismo con `delete_page(0)` sobre un PDF de una página: se queda en 0
páginas y `tobytes()` corta igual. Por eso `pdf_sin_paginas()` arma la
estructura mínima de un PDF —catálogo y árbol de páginas con `/Count 0`— con
su tabla `xref` calculada. Verificado que PyMuPDF lo abre sin protestar
(`page_count == 0`, `needs_pass == 0`) y que `texto_por_pagina` devuelve `[]`,
que es la entrada al hueco. **No se ha montado otro generador**: la función
vive en `tests/utiles_pdf.py`, con el motivo escrito en su docstring.

### El arreglo

`paso_troceado`, justo detrás del `except PdfIlegible`:

```python
if not textos:
    contexto.avisos.append(
        f"{documento.nombre}: descartado, el PDF no tiene páginas"
    )
    continue
```

La redacción es la de los avisos que ya existían (`paso_ingesta.py:31` y
`paso_troceado.py:46`, ambos `«<nombre>: descartado, <motivo>»`), con el texto
que sugirió el reviewer. El docstring del módulo gana un párrafo diciendo que
lo que no da ningún parte se descarta nombrándolo.

**Lo que NO cambia**: el contrato de `/api/split`, la forma del `ParteTroceado`
y cualquier otro comportamiento. Solo se añade un aviso donde no lo había. El
test nuevo **no** es trazable a ningún requisito y por eso no se llama
`test_f002_rN_...`: F-002 no exige esto, es el patrón de la feature el que lo
pide (los 76 tests trazables siguen siendo 76).

### Verificación real

| Qué | Comando | Resultado |
|---|---|---|
| Test nuevo antes del arreglo | el de arriba | **1 failed** (traza pegada) |
| Suite del servicio | `./.venv/Scripts/python.exe -m pytest -q` | **95 passed in 2.30s** (eran 94; ninguno roto) |
| Portero | `bash harness/init.sh` | exit 0, `ENTORNO LISTO` |

---

## Trabajo 2 · `docs/CONVENTIONS.md`, ReportLab frente a PyMuPDF

Commit `6048c19`. La línea «PDF en servidor: ReportLab (no HTML/CSS print)»
pasa a distinguir los dos casos, con el estilo de lista del resto del fichero:

- **Componer un PDF nuevo** desde cero (informes, etiquetas, acuses):
  ReportLab, no HTML/CSS print.
- **Manipular un PDF de entrada** —abrirlo, leer su texto, extraer páginas—:
  PyMuPDF, porque ReportLab no sabe leer lo que no ha escrito él. Con el
  ejemplo real: `infrastructure/documentos/pdf_pymupdf.py`, donde el PDF de
  cada parte son páginas del original y no una composición nueva.

Sin reglas nuevas: describe lo que el código ya hace y que la spec de F-002 ya
aprobó.

---

## Trabajo 3 · Automejora del arnés

### En este repositorio (commit `c6c63d7`)

- `.claude/agents/reviewer.md`, punto 4 (verificación de la mutación).
- `CHECKPOINTS.md`, bloque **C4 bis**: checkbox nuevo, «Los muertos están
  comprobados, no solo contados».

Lo que dicen ambos: recalcular alcance y número de mutantes **no demuestra que
los muertos lo estén**; si el «Tiempo total» que declara el propio informe de
mutación baja de **5 minutos**, el reviewer **reejecuta la campaña** con
`--salida` a una ruta **fuera de `progress/`** (allí pisaría el informe del
implementer), compara los cuatro totales y comprueba con `git status` que el
árbol queda limpio; si pasa de 5 minutos, se queda en el recálculo puro y **lo
dice explícitamente en su informe**.

### Propagación a `arnes-base` (commit `8b5148d`, local, sin push)

- `arnes-base/arnes-base/.claude/agents/reviewer.md` y
  `arnes-base/arnes-base/CHECKPOINTS.md`: **el mismo texto**. Comprobado antes
  de tocarlos que las dos regiones eran idénticas a las de este repositorio, o
  sea que no había adaptación local que portar por error (el `[ADAPTAR]` de C3
  no se ha tocado).
- `arnes-base/GUIA_INSTALACION.md`: sección al final, «La mutación se
  reejecuta, no solo se recuenta (1.5.1, 2026-08-18)», con el motivo, las dos
  ramas de la regla y el origen (la review de F-002, 29,7 s de campaña).
- `arnes-base/arnes-base/harness/VERSION`: **no ha hecho falta tocarlo**, ya
  estaba en `ARNES_VERSION=1.5.1` / `ARNES_FECHA=2026-08-18`. Ver más abajo.
- `git status` de `arnes-base`: limpio tras el commit.

---

## BLOQUEADO · El paso 4 (subir `harness/VERSION` de este repo a 1.5.1)

**El hecho.** El encargo daba por supuesto que `arnes-base` estaba en 1.5.0.
No lo está: su commit `11f24fb`, de hoy a las 16:44, ya subió a **1.5.1** con
otro cambio, «repetir una campaña de mutación ya no borra el análisis de los
supervivientes», que toca `harness/mutacion.py` (+107 líneas) y añade
`tests/test_mutacion_informe.py` (148 líneas).

**Por qué no he escrito 1.5.1 aquí.** Este repositorio **no tiene** ese
cambio: su `harness/mutacion.py` es byte a byte el de la 1.5.0 (comprobado con
`git show 11f24fb^:arnes-base/harness/mutacion.py | diff -`) y
`tests/test_mutacion_informe.py` no existe. Poner `ARNES_VERSION=1.5.1` sería
declarar una versión que no se tiene, justo en el fichero cuyo trabajo es no
mentir sobre eso —y `harness/ARNES_VERSION.md` de este repositorio documenta,
versión a versión, **qué se copió literal**: la entrada de la 1.5.1 no se
podría escribir sin listar dos ficheros que no están. Es el mismo pecado que
esta automejora viene a cerrar: dar por buena una declaración sin la evidencia
detrás. Por eso paro en vez de improvisar.

**Contexto que acota el riesgo**, ya comprobado:

- La 1.5.1 de `arnes-base` está **sin publicar** (`origin/main..main` la tiene
  pendiente) y **no está instalada en ningún proyecto**: `albaranes` 1.4.0,
  `partes` 1.4.0, `datamart-seg-anual` 1.5.0, este 1.5.0.
- Por eso he metido esta mejora **dentro de la misma 1.5.1** en `arnes-base`
  en vez de abrir una 1.5.2: misma fecha, mismo día, nada que ya se hubiera
  entregado. Si prefieres una versión propia, es un `git commit --amend` de
  distancia.
- Mientras tanto, este repositorio queda **entendiendo de menos, no de más**:
  lleva ya el contenido de la 1.5.1 en `reviewer.md` y `CHECKPOINTS.md` pero
  declara 1.5.0. El instalador compara **fichero a fichero por hash**,
  independientemente del número de versión, así que un `-Modo actualizar`
  seguiría enseñando lo que falta. Lo contrario —declarar 1.5.1 sin tenerla—
  sí engañaría a quien lea el sello.

**Decisión que necesito de ti (una de las dos):**

- **A) Completar la 1.5.1 aquí.** Copiar de `arnes-base` los dos ficheros que
  faltan (`harness/mutacion.py` y `tests/test_mutacion_informe.py`); es un
  avance limpio, porque este repositorio no tiene ninguna adaptación local en
  ellos. Después sí: `harness/VERSION` a 1.5.1 y la entrada en
  `harness/ARNES_VERSION.md` con las dos mitades de la versión. Cambia el
  comportamiento de una herramienta del arnés, así que no lo hago sin tu «sí».
- **B) Dejarlo en 1.5.0** y que la actualización a 1.5.1 entre entera cuando
  se pase el instalador, con el resto de la versión.

En ambos casos, `harness/ARNES_VERSION.md` está **sin tocar** (y por tanto sin
el literal de la marca de adaptación, que dejaría un aviso falso permanente en
la sección 8 de `init.sh`).

---

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (servicio `api`) | **95 passed in 2.30 s** (94 antes; +1, ninguno roto) |
| Tests del arnés | **10 passed in 0.21 s** |
| Portero `bash harness/init.sh` | exit 0, `ENTORNO LISTO`; ruff sin avisos |
| Cobertura de las líneas cambiadas | **N/A por configuración**: `init.sh` la declara N/A con su motivo impreso —«la rama `chore/postreview-F-002` no corresponde a ninguna feature declarada»—, que es lo correcto: esto no es una feature del backlog |
| Mutación | **no ejecutada**, con motivo: la campaña se lanza **por feature** y su alcance sale del diff de la rama de la feature (`f5328f2..feature/F-002-ingesta-troceado`), así que **no incluiría la línea añadida hoy**; además la herramienta se niega a arrancar con el árbol sucio y hay un fichero de otro agente sin commitear (`progress/explore_F-003.md`). La línea nueva sí está cubierta por el test nuevo, y su mutación evidente (`if textos:` en vez de `if not textos:`) lo rompería |
| Tiempo de la suite del servicio | 2,30 s (3,99 s dentro de `init.sh`, con cobertura) |

---

## Commits

**`postventa-incidencias`**, rama `chore/postreview-F-002` (local, sin push):

| Commit | Trabajo |
|---|---|
| `46f9afc` | 1 · el PDF válido de 0 páginas ya no se descarta en silencio |
| `6048c19` | 2 · `CONVENTIONS` distingue componer un PDF de manipularlo |
| `c6c63d7` | 3 · el reviewer reejecuta la campaña de mutación si es barata |

**`arnes-base`**, rama `main` (local, sin push):

| Commit | Qué |
|---|---|
| `8b5148d` | 1.5.1: el reviewer reejecuta la campaña de mutación cuando es barata (`reviewer.md`, `CHECKPOINTS.md`, `GUIA_INSTALACION.md`) |

`git add` siempre con rutas concretas; nunca `-A` ni `.`. El fichero
`progress/explore_F-003.md`, del agente que trabaja en F-003, sigue sin
versionar y **no está en ningún commit** (comprobado en el `git show --stat`
de los tres).

## Qué queda pendiente

1. **La decisión A o B de arriba**, y con ella `harness/VERSION` y
   `harness/ARNES_VERSION.md` de este repositorio.
2. Nada más: los trabajos 1, 2 y 3 están cerrados y verificados. La rama
   `chore/postreview-F-002` está lista para que la mergees a `dev` detrás de
   F-002 (cuando tú lo hagas: los agentes no hacen push ni PR).
