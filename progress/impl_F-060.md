<!-- progress/impl_F-060.md -->
# F-060 · Normalizar las ubicaciones de la bandeja al texto exacto de Sigrid — Informe del implementer

Rama `feature/F-060-normalizar-ubicaciones`. Rigor **`critico`**.
Spec: `specs/F-060-normalizar-ubicaciones/` (aprobada por el humano el 2026-10-09: D-1 a D-10 tal cual;
Q-1, las normalizadas pasan de `nueva` a `editada`).

**Base fija: `33d8938`** (`dev` en `704cfca` más el commit del backlog; fijada en `tasks.md` y por el líder el
2026-10-09). Las guardias de alcance y la mutación del Bloque 1 usan esa.

## Bloque 1 · La regla y el plan (dominio puro) · T1, T2, T3 · 2026-10-09

### T1 · Fase RED

`tests/test_f060_normalizacion_dominio.py` (80 casos) contra un **esqueleto neutro** de
`domain/models/normalizacion.py` con los nombres de `design.md` §6 y cuerpos que no deciden nada:
`clave_de_ubicacion` devuelve el texto tal cual, `ubicacion_de_sigrid` siempre `sin_coincidencia`,
`revision_de_normalizacion` devuelve los vigentes sin cambiar y con huella vacía, `planificar_normalizacion` un
plan vacío con el recuento a cero, `TEXTO_SISTEMA` y `QUIEN_SISTEMA` vacíos, `ESTADOS_NORMALIZABLES` vacío y los
tres tipos sin `frozen`. Así cada test falla por **aserción** y no por la importación.

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py -q -p no:cacheprovider --tb=line -rf
```

Salida real (una línea por fallo con `--tb=line`, la lista de `FAILED` y el total; solo se ha recortado el prefijo
absoluto de la ruta):

```
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert 'Sala Ejemplo' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert 'SALA EJEMPLO' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '  Sala Ejemplo\t' == 'sala ejemplo'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '\nPATIO Ficticio  ' == 'patio ficticio'
tests\test_f060_normalizacion_dominio.py:208: AssertionError: assert '   ' == ''
tests\test_f060_normalizacion_dominio.py:215: AssertionError: assert 'Straße Ejemplo' == 'strasse ejemplo'
tests\test_f060_normalizacion_dominio.py:223: AssertionError: assert 'Ban\u0303o Ejemplo' == 'Ba\xf1o Ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala  Ejemplo' == 'sala  ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sála Ejemplo' == 'sála ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Pingüino Ejemplo' == 'pingüino ejemplo'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala Ejemplo.' == 'sala ejemplo.'
tests\test_f060_normalizacion_dominio.py:238: AssertionError: assert 'Sala-Ejemplo' == 'sala-ejemplo'
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio ficticio')
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:276: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:282: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:291: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio Ficticio')
tests\test_f060_normalizacion_dominio.py:301: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:309: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:316: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Sala Ejemplo')
tests\test_f060_normalizacion_dominio.py:322: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...Baño Ejemplo')
tests\test_f060_normalizacion_dominio.py:331: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...raße Ejemplo')
tests\test_f060_normalizacion_dominio.py:365: AssertionError: assert <Coincidencia.SIN_COINCIDENCIA: 'sin_coincidencia'> is <Coincidencia.NORMALIZABLE: 'normalizable'>
tests\test_f060_normalizacion_dominio.py:373: AssertionError: assert <Coincidencia.SIN_COINCIDENCIA: 'sin_coincidencia'> is <Coincidencia.NORMALIZABLE: 'normalizable'>
tests\test_f060_normalizacion_dominio.py:384: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:393: AssertionError: assert frozenset() == frozenset({<E...VA: 'nueva'>})
tests\test_f060_normalizacion_dominio.py:402: Failed: DID NOT RAISE FrozenInstanceError
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:422: AssertionError: assert '' == 'sistema:normalizar_ubicacion'
tests\test_f060_normalizacion_dominio.py:447: AssertionError: assert 'SALA EJEMPLO' == 'Sala Ejemplo'
tests\test_f060_normalizacion_dominio.py:476: AssertionError: assert () == (RevisionNuev...mezone.utc)),)
tests\test_f060_normalizacion_dominio.py:511: AssertionError: assert [] == [UUID('000000...00000000001')]
tests\test_f060_normalizacion_dominio.py:526: AssertionError: assert [] == [UUID('000000...00000000002')]
tests\test_f060_normalizacion_dominio.py:535: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:543: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:543: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:552: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:559: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:574: AssertionError: assert [] == [UUID('000000...00000000003')]
tests\test_f060_normalizacion_dominio.py:589: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=1)
tests\test_f060_normalizacion_dominio.py:589: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=1)
tests\test_f060_normalizacion_dominio.py:599: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:599: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:607: assert 0 == 1
tests\test_f060_normalizacion_dominio.py:627: AssertionError: assert {} == {UUID('000000...0000003'): 91}
tests\test_f060_normalizacion_dominio.py:642: AssertionError: assert [] == [UUID('000000...0000000001e')]
tests\test_f060_normalizacion_dominio.py:671: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=2)
tests\test_f060_normalizacion_dominio.py:698: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_normalizacion_dominio.py:741: AssertionError: assert <EstadoRevision.NUEVA: 'nueva'> is <EstadoRevision.EDITADA: 'editada'>
tests\test_f060_normalizacion_dominio.py:772: assert 0 == 2
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[Sala Ejemplo-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[SALA EJEMPLO-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[  Sala Ejemplo\t-sala ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[\nPATIO Ficticio  -patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas[   -]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_casefold_y_no_lower
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_nfc_frente_a_nfd
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala  Ejemplo-sala  ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[S\xe1la Ejemplo-s\xe1la ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Ping\xfcino Ejemplo-ping\xfcino ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala Ejemplo.-sala ejemplo.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_no_toca_nada_mas[Sala-Ejemplo-sala-ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Sala Ejemplo-lista0-exacta-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[patio ficticio-lista1-exacta-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[ Sala Ejemplo -lista2-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[\tpatio ficticio\n-lista3-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[SALA EJEMPLO-lista4-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[sala ejemplo-lista5-normalizable-Sala Ejemplo]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Patio Ficticio-lista6-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[  PATIO FICTICIO -lista7-normalizable-patio ficticio]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[PATIO FICTICIO-lista8-ambigua-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_cada_fila_de_la_tabla[Patio ficticio-lista9-ambigua-None]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_el_exacto_gana_aunque_otro_tenga_la_misma_clave
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_el_exacto_tras_recortar_gana_a_la_ambiguedad
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_ambigua_con_tres_candidatos
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_ambigua_por_la_forma_unicode_de_la_lista
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_un_valor_repetido_tal_cual_no_es_ambiguo
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_nfd_frente_a_nfc
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_casefold_en_la_clasificacion
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r5_el_resultado_es_el_valor_de_la_lista_caracter_a_caracter
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r5_el_resultado_conserva_la_forma_unicode_de_la_lista
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_identidad_del_sistema
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_estados_normalizables_son_nueva_y_editada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_los_tipos_son_inmutables
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[-]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[oid-de-prueba-f060-]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema[oid-de-prueba-f060-    ]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_revision_cambia_solo_la_ubicacion_de_los_vigentes
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_normalizable_da_una_revision
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_mira_la_unidad_vigente_y_no_la_importada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_mira_la_ubicacion_vigente_y_no_la_importada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_ubicacion_de_otra_unidad_no_vale
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_unidad_sin_lista_no_normaliza[9901.03VILLA 3.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_una_unidad_sin_lista_no_normaliza[9901.03VILLA 9.]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_sin_ubicacion_o_exacta_se_examina_y_no_cuenta
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r6_ambigua_no_se_normaliza
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_nueva_y_editada_se_normalizan
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_aprobada_y_descartada_son_no_editables[aprobar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_aprobada_y_descartada_son_no_editables[descartar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_no_editable_solo_cuenta_las_normalizables[aprobar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r7_no_editable_solo_cuenta_las_normalizables[descartar]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_revision_del_plan_es_la_de_normalizacion
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r9_la_esperada_es_la_ultima_revision_leida
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r9_las_revisiones_van_en_orden_de_incidencia_id
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r10_el_recuento_de_una_obra_y_su_suma
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r10_el_plan_acepta_un_iterable_de_una_pasada
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r22_la_normalizada_queda_editada_y_sin_el_motivo
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r21_una_segunda_pasada_no_tiene_nada_que_normalizar
58 failed, 22 passed in 0.53s
```

**58 fallan, todos por aserción** (57 `AssertionError` y un `Failed: DID NOT RAISE FrozenInstanceError`); ninguno
por `ImportError`, `TypeError` ni `ValueError`. Los **22 que pasan en RED** son controles cuya respuesta correcta
coincide con la neutra, y tienen que seguir en verde:

| Tests que pasan en RED | Por qué |
|---|---|
| `test_f060_r2_cada_fila_de_la_tabla` (las 4 filas `sin_coincidencia`), `test_f060_r3_lista_vacia` (×5), `test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide` (×10) | `sin_coincidencia` es justo lo que devuelve el esqueleto: son el control negativo de R2–R4 (lo que **no** se puede normalizar). Su contraparte positiva sí falla |
| `test_f060_r1_la_clave_recorta_y_pliega_mayusculas[-]` | La clave de `""` es `""`, también sin hacer nada |
| `test_f060_r6_sin_situaciones_el_plan_esta_vacio` | Sin incidencias, el plan vacío es la respuesta correcta y la neutra |
| `test_f060_r23_ambigua_y_sin_coincidencia_siguen_fuera_de_lista` | Guarda: lo que no se normaliza no recibe revisión y sigue con el motivo de F-056 |

R11 (`validar_quien` rechaza el correo del sistema) **ya se cumple con el código de F-056** (el literal no tiene
`@`): en RED falla por la comprobación del literal (`'' == 'sistema:normalizar_ubicacion'`), que es lo que F-060
añade; el rechazo en sí es una guarda que no se puede ver fallar sin tocar `revision.py`, que no se toca.

### T2 · GREEN

`domain/models/normalizacion.py` con lo de `design.md` §6, **sin tocar** `domain/models/revision.py` (solo se
importa: `git diff 33d8938 -- services/postventa-api/domain/models/revision.py` vacío).

Comando de la verificación, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py tests/test_f056_revision_dominio.py tests/test_f005_arquitectura.py tests/test_f036_arquitectura.py -q -p no:cacheprovider
```

Salida real: `404 passed in 17.47s` (los 80 de F-060, y los de F-056 y de arquitectura **sin tocarlos**).
`tests/test_f006_repo_sin_identificadores.py`, con los de F-060: `128 passed in 50.67s`. `ruff check` de los dos
ficheros: `All checks passed!`.

Cobertura del módulo nuevo con esos tests (`coverage run --branch --include=domain/models/normalizacion.py`):
**76 sentencias, 20 ramas, 100 %**, sin líneas ni ramas sin cubrir.

#### Decisiones de diseño (dentro de la spec)

| Decisión | Por qué |
|---|---|
| `ubicacion_de_sigrid` cuenta los candidatos **distintos** (`dict.fromkeys`) | R2.4 habla de «dos o más **valores** de la lista»: un valor repetido tal cual es uno solo. Con la lista de `ubicaciones_de_tipologia` no pasa (ya quita los repetidos exactos), pero la función no depende de quién la llame. Test: `test_f060_r2_un_valor_repetido_tal_cual_no_es_ambiguo` |
| Un valor NFC y otro NFD iguales a la vista en la lista son **dos** candidatos → `ambigua` | Son dos textos distintos de Sigrid con la misma clave; el sistema no elige (§3). Test: `test_f060_r2_ambigua_por_la_forma_unicode_de_la_lista` |
| `normalizables` del recuento es `len(revisiones)` | Así `normalizables == len(plan.revisiones) == len(plan.esperadas)` por construcción, que es lo que R20 suma después |
| `esperadas` se construye en el orden de las revisiones (por `incidencia_id`) | El lote de §7 bloquea y escribe en ese orden; el plan ya lo da ordenado. Test: `test_f060_r9_las_revisiones_van_en_orden_de_incidencia_id` |
| Una `aprobada`/`descartada` cuya ubicación es `ambigua` o `sin_coincidencia` cuenta ahí, no en `no_editables` | R7 y R10: `no_editables` son las **normalizables** que no se pueden editar. Test: `test_f060_r7_no_editable_solo_cuenta_las_normalizables` |

#### Nota para el Bloque 6 (no es una desviación)

El paso 1 de T26 exige `no_exactas == por_motivo.ubicacion_fuera_de_lista`. Hay un caso en que no cuadran: una
vigente **sin recortar** cuyo texto recortado está en la lista. Para F-056 no es `ubicacion_fuera_de_lista`
(compara recortado), y para F-060 es `normalizable` por R2.2 (no es `exacta` tal cual), así que suma en
`no_exactas`. El design §3 dice que hoy es inalcanzable (la importación y la edición guardan recortado), así que
la comprobación de T26 vale; si alguna vez no cuadra por poco, este es el primer sospechoso.

### T3 · Mutación del bloque

Comando, desde la raíz: `python -m harness.mutacion --feature F-060 --base 33d8938 --timeout 1800` (8 workers, los de
`harness/rigor.json`). Lanzado tras el commit de T2 (`fda8418`) y esperado hasta el final, con el árbol quieto.

Salida real (cola):

```
F-060: 1 fichero(s), 211 línea(s) de producción (origen rama, 33d89385ccf0c76a7ba00208744282936ba9e04a..feature/F-060-normalizar-ubicaciones)
Campaña paralela: hasta 8 workers, uno por worktree.
...
19 mutantes evaluados, 19 muertos, 0 supervivientes, 0 timeouts en 2768.9 s
Informe: progress/mutacion_F-060.md
```

**19/19 muertos, 0 supervivientes, 0 timeouts** (`progress/mutacion_F-060.md`). Por familias: `frozen=True` de los
tres tipos (3, los mata `test_f060_los_tipos_son_inmutables`); la comparación de clave y el `not candidatos` del
recuento de candidatos (2); `> 1` → `>= 1` y `> 1` → `> 2` (2, los matan las filas `normalizable` y la `ambigua`
de dos candidatos); `candidatos[0]` → `[1]` (1); y los contadores del plan, su `0` inicial, sus `+= 1` → `-= 1` y
`+= 2` (11, los matan los tests de recuento de R6, R7 y R10).

**Lo que el mutador no muta** (aviso del encargo): `harness.mutacion` no muta condiciones sin operadores de su tabla
—`in`, `not in`, `is`, `is not`—, y en `normalizacion.py` las hay en ramas de verdad: `texto in lista` (exacta),
`recortado in lista` (normalizable por recorte), `vigentes.ubicacion is None`, los `is Coincidencia.…` del plan,
`estado_de(…) not in ESTADOS_NORMALIZABLES` y el `ultima is None` de la esperada. El fichero **no** sale con 0
mutantes, pero esas ramas no tienen mutante. Cada una la fija un test que fallaría si se invirtiera o se quitara:
`test_f060_r2_cada_fila_de_la_tabla` (filas `exacta` y de recorte), `test_f060_r2_el_exacto_tras_recortar_gana_a_la_ambiguedad`,
`test_f060_r6_sin_ubicacion_o_exacta_se_examina_y_no_cuenta`, `test_f060_r7_aprobada_y_descartada_son_no_editables`,
`test_f060_r7_nueva_y_editada_se_normalizan` y `test_f060_r9_la_esperada_es_la_ultima_revision_leida`; y la cobertura
de ramas del módulo es del 100 % (20/20).

### Ficheros tocados en el Bloque 1

| Fichero | Cambio |
|---|---|
| `services/postventa-api/domain/models/normalizacion.py` | **Nuevo**: `Coincidencia`, `TEXTO_SISTEMA`, `QUIEN_SISTEMA`, `ESTADOS_NORMALIZABLES`, `UbicacionDeSigrid`, `RecuentoNormalizacion`, `PlanDeNormalizacion`, `clave_de_ubicacion`, `ubicacion_de_sigrid`, `revision_de_normalizacion`, `planificar_normalizacion` |
| `services/postventa-api/tests/test_f060_normalizacion_dominio.py` | **Nuevo**: 80 casos (R1–R11, y R21–R23 en el dominio) |
| `specs/F-060-normalizar-ubicaciones/tasks.md` | T1, T2 y T3 marcadas |
| `progress/impl_F-060.md`, `progress/mutacion_F-060.md` | Este informe y el de la campaña |

**Sin tocar**: `domain/models/revision.py` y el resto de F-056, F-036, `.env`, `services/postventa-front/`, la
plantilla. Ningún test de F-036 ni de F-056 cambiado. Datos de los tests, ficticios (obra `9901`, «Sala Ejemplo»,
«Patio Ficticio», `@ejemplo.invalid`, `UUID(int=n)`).

### Commits del Bloque 1

| Commit | Qué |
|---|---|
| `2c92a10` | **T1 · RED**: el test, el esqueleto neutro y la cabecera de este informe con la base fija |
| `fda8418` | **T2 · GREEN**: `domain/models/normalizacion.py` |
| (este commit) | **T3**: `progress/mutacion_F-060.md`, T3 marcada y este informe |

### Pendiente

Nada del Bloque 1. **Parar: review del Bloque 1.** El Bloque 2 (el lote en la base) no se ha empezado.

### Evidencias (Bloque 1)

| Evidencia | Valor real |
|---|---|
| Tests de F-060 | 80 passed (`tests/test_f060_normalizacion_dominio.py`) |
| Tests de la verificación de T2 (F-060 + F-056 dominio + arquitectura F-005/F-036) | 404 passed in 17.47 s |
| `tests/test_f006_repo_sin_identificadores.py` + F-060 | 128 passed in 50.67 s |
| Cobertura de lo cambiado | `domain/models/normalizacion.py`: 76/76 sentencias y 20/20 ramas, **100 %** (medido con `coverage run --branch` sobre los tests de F-060; la `PUERTA COBERTURA` de `init.sh` se mide en T23 con la suite entera) |
| Mutantes | **19 generados, 19 muertos, 0 supervivientes, 0 timeouts** |
| Workers y tiempo de la campaña | 8 workers, 2768.9 s |
| Suite entera | No ejecutada en este bloque (solo en T23, por `tasks.md`) |

### Review del Bloque 1 · C-1 y C-2 (solo tests) · 2026-10-09

`progress/review_F-060_bloque1.md`: CHANGES_REQUESTED **solo en tests**. Se resuelven C-1 y C-2 tal como los
describe la review, en `tests/test_f060_normalizacion_dominio.py`; `domain/models/normalizacion.py` **no** cambia.
**C-3** (X01, NFC después de `casefold`) no es de este encargo: lo decide el humano con el líder, y no se ha añadido
ningún test de «ſ́». Los espacios duros van escritos como ` ` en el fuente, para que se vean.

| Hallazgo | Tests añadidos |
|---|---|
| **C-1** (M11, NFKC) | `test_f060_r1_nfc_y_no_nfkc` (`clave_de_ubicacion("Sala Ejemplo 1º") != clave_de_ubicacion("SALA EJEMPLO 1O")`, y lo mismo con «1ª»/«1A»); el caso `"SALA EJEMPLO"` (espacio duro interior) en `test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide`; y `test_f060_r4_la_forma_de_compatibilidad_no_coincide` («SALA EJEMPLO 1O» contra «Sala Ejemplo 1º» y «SALA EJEMPLO 1A» contra «Sala Ejemplo 1ª» → `sin_coincidencia`) |
| **C-2** (X07, `strip(' ')`) | `test_f060_r2_el_recorte_es_el_de_strip_no_solo_de_espacios`: `"\tPatio Ficticio\n"` → `normalizable` «Patio Ficticio» y `"patio ficticio "` → `normalizable` «patio ficticio», los dos contra `L_AMBIGUA` |

#### Rojo con los mutantes, en una copia del scratchpad

Copia de `services/postventa-api` (sin `.venv` ni `local.settings.json`) en el scratchpad; cada mutante aplicado
**solo en la copia** y restaurado después; el árbol de trabajo no se tocó (`git status`: solo el test modificado).
Comando en la copia, con el intérprete del servicio:

```
PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py -q -p no:cacheprovider --tb=line -rf
```

**M11** — `normalizacion.py:107`, `unicodedata.normalize("NFC", texto)` → `unicodedata.normalize("NFKC", texto)`.
Salida real (solo se ha recortado el prefijo absoluto de la copia):

```
tests\test_f060_normalizacion_dominio.py:222: AssertionError: assert 'sala ejemplo 1o' != 'sala ejemplo 1o'
tests\test_f060_normalizacion_dominio.py:377: AssertionError: assert UbicacionDeSi...Sala Ejemplo') == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:394: AssertionError: assert UbicacionDeSi...a Ejemplo 1º') == UbicacionDeSi...>, texto=None)
tests\test_f060_normalizacion_dominio.py:394: AssertionError: assert UbicacionDeSi...a Ejemplo 1ª') == UbicacionDeSi...>, texto=None)
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r1_nfc_y_no_nfkc
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide[SALA\xa0EJEMPLO]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r4_la_forma_de_compatibilidad_no_coincide[SALA EJEMPLO 1O-lista0]
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r4_la_forma_de_compatibilidad_no_coincide[SALA EJEMPLO 1A-lista1]
4 failed, 81 passed in 0.79s
```

**X07** — `normalizacion.py:122`, `recortado = texto.strip()` → `recortado = texto.strip(' ')`. Salida real:

```
tests\test_f060_normalizacion_dominio.py:310: AssertionError: assert UbicacionDeSi...>, texto=None) == UbicacionDeSi...tio Ficticio')
FAILED tests/test_f060_normalizacion_dominio.py::test_f060_r2_el_recorte_es_el_de_strip_no_solo_de_espacios
1 failed, 84 passed in 0.71s
```

El test se para en su primera aserción; los **dos** casos de C-2 caen con X07, comprobado uno a uno contra la copia
mutada:

```
'\tPatio Ficticio\n' -> UbicacionDeSigrid(coincidencia=<Coincidencia.AMBIGUA: 'ambigua'>, texto=None)
'patio ficticio\xa0' -> UbicacionDeSigrid(coincidencia=<Coincidencia.AMBIGUA: 'ambigua'>, texto=None)
```

Con el original restaurado en la copia: `85 passed in 0.59s`.

#### Verde en el árbol de trabajo

Desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py tests/test_f006_repo_sin_identificadores.py -q -p no:cacheprovider
```

Salida real: `133 passed in 15.45s` (85 de F-060, antes 80, y los de F-006). `ruff check` del test: `All checks
passed!`. Sin campaña de mutación nueva (lo indica el encargo: el código de producción no cambia, y los 19
mutantes de `progress/mutacion_F-060.md` siguen siendo los mismos).

**Evidencias, al día**: tests de F-060 **85 passed**; los mutantes a mano M11 y X07 de la review, **muertos**; X01
queda pendiente de C-3 (decisión del humano).

### C-3 de la review del Bloque 1 · aceptación del humano (2026-10-10)

El humano **acepta por escrito** («si», 2026-10-10, opción (a) de la review): el mutante a mano **X01**
(NFC aplicado después de `casefold`) queda vivo. Solo agrupa distinto con caracteres ajenos al castellano
(«ſ» con marca combinante, griego con diéresis y tilde, cirílico histórico); con Á, É, Í, Ó, Ú, Ü y Ñ el
resultado es el mismo. R1 se queda como se aprobó.

## Bloque 2 · El lote en la base · T4, T5, T6 y T8 hechas; T7 MANUAL del humano · 2026-10-10

Encargo: T4 (RED), T5, T6 y T8; T7 es MANUAL del humano. Rama `feature/F-060-normalizar-ubicaciones`, HEAD de
partida `66c981d` (el hash anterior a T4: el `--base` de la mutación de este bloque).

**Resultado.** Hice T4 (`e259f23`) y paré antes de T5: la spec chocaba con un test de F-056 que prohibía tocar
(sección «BLOQUEO» más abajo). El humano eligió la **opción (a)** el 2026-10-10. Apliqué esa decisión en su propio
commit (`fabbd7f`) y seguí con T5 (`29bb77b`), T6 (`5bf9686`) y T8. La sección «Para el humano · T7» está al
final del bloque.

### Precondiciones

- Rama comprobada: `feature/F-060-normalizar-ubicaciones`, árbol limpio en `66c981d`.
- `bash harness/init.sh`: en verde todo lo que llegó a correr (estructura, `features.json`, `BACKLOG.md`, rigor,
  `compileall`, ruff con 73 avisos de deuda previa, suite de la raíz **115 passed**, `servicios.json`). La suite
  del servicio `api` (~35 min) **la paré yo** hacia el 10 %, porque el encargo prohíbe la suite completa fuera de
  T23. La última ejecución entera (primera pasada de la review del Bloque 1: 7767 passed, cobertura 100 %) sigue
  representando el código de producción, que no había cambiado desde entonces.

### T4 · Fase RED

`tests/test_f060_repositorio_lote.py` (27 casos) contra un **esqueleto neutro**, como en el Bloque 1:
`ResultadoDelLote` sin `frozen` en `domain/ports/revision.py`, y `RepositorioRevisionPostgres.registrar_lote`
devolviendo un resultado vacío sin ejecutar nada. **El esqueleto no toca `RevisionPort`** (ver el bloqueo).

El test usa el doble de `tests/utiles_pg.py` con una subclase local, `ConexionDeLote`, que cuenta los cursores
abiertos, devuelve un `revision_id` distinto en cada `INSERT … RETURNING` (101, 102 y 103, en el orden de
ejecución) y puede hacer fallar el `n`-ésimo `INSERT` (para demostrar que el `ROLLBACK` deshace los anteriores).
Las revisiones se pasan **desordenadas** (U3, U1, U2) a propósito.

| Caso | R |
|---|---|
| El puerto tiene `registrar_lote` (solo por nombre: `revisiones`, `esperadas`) y conserva las seis de F-056 | R12 |
| `ResultadoDelLote` es inmutable, con `registradas` y `desactualizadas` | R12 |
| Una transacción (un cursor, un `COMMIT`). Las sentencias ejecutadas son **exactamente** las de `sentencias_revision.py`, texto y parámetros: bloqueo de las tres en orden, últimas de las tres, `INSERT` de U1, U2 y U3 | R12, R15 |
| El bloqueo es `ORDER BY incidencia_id FOR UPDATE`, sin `ADVISORY` | R12 |
| Lo insertado es la revisión del sistema: `editar`, sin motivo, `TEXTO_SISTEMA` en `revisado_por` y en `revisado_correo`, la huella y la hora | R12, R8 |
| Una desactualizada (cinco variantes; también con el `incidencia_id` en texto, como lo puede dar la base) se salta y las otras se insertan en orden; `COMMIT` sin `ROLLBACK` | R13 |
| Todas desactualizadas (también con las esperadas cruzadas entre incidencias): ningún `INSERT` | R13 |
| Fallo de la base al bloquear, al leer las últimas, en el primer `INSERT` y en el tercero: `ROLLBACK` y `PersistenciaNoDisponible` con `registrar_lote` y `LockNotAvailable`; sin textos, sin `sistema:…`, sin `incidencia_id` y sin el texto del error | R14 |
| Un fallo que no es de la base (hora sin zona en la segunda): `ROLLBACK`, y el `ValueError` sube tal cual | R14 |
| En todo lo ejecutado, ningún `UPDATE`, `DELETE`, `TRUNCATE`, `ON CONFLICT` ni `ADVISORY`. Contra `bandeja_incidencias`, solo el bloqueo; las escrituras, solo `INSERT INTO postventa.revisiones_bandeja` | R15 |
| El código del repositorio (sin docstrings) no lleva SQL escrito a mano | R15 |
| Lote vacío: resultado vacío, ningún cursor, nada ejecutado, ni `COMMIT` ni `ROLLBACK` | R16 |
| Precondiciones (una revisión sin su esperada, la única sin esperada, una repetida, la misma dos veces) → `ValueError` sin abrir nada | §7, paso 2 |

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_repositorio_lote.py -q -p no:cacheprovider --tb=line -rf
```

Salida real: las líneas `--tb=line` de cada fallo, con el prefijo absoluto recortado, y el total. **Los 24 fallos
son de aserción** (`AssertionError` o `Failed: DID NOT RAISE`). Dos los levanta `ConexionDoble.primera_con` de
`utiles_pg.py`, que es una aserción con mensaje.

```
tests\test_f060_repositorio_lote.py:163: AssertionError: assert ['aprobadas',..., 'situacion'] == ['aprobadas',...ar_lote', ...]
tests\test_f060_repositorio_lote.py:176: AssertionError: el puerto no tiene registrar_lote
tests\test_f060_repositorio_lote.py:188: Failed: DID NOT RAISE FrozenInstanceError
tests\test_f060_repositorio_lote.py:206: AssertionError: assert ResultadoDelL...s=frozenset()) == ResultadoDelL...s=frozenset())
tests\utiles_pg.py:179: AssertionError: no se ejecutó ninguna sentencia con 'FOR UPDATE'; se ejecutaron: []
tests\utiles_pg.py:179: AssertionError: no se ejecutó ninguna sentencia con 'INSERT INTO'; se ejecutaron: []
tests\test_f060_repositorio_lote.py:271: AssertionError: assert ResultadoDelL...s=frozenset()) == ResultadoDelL...000000002')}))
tests\test_f060_repositorio_lote.py:271: AssertionError: assert ResultadoDelL...s=frozenset()) == ResultadoDelL...000000002')}))
tests\test_f060_repositorio_lote.py:294: AssertionError: assert frozenset() == frozenset({UU...0000000001')})
tests\test_f060_repositorio_lote.py:294: AssertionError: assert frozenset() == frozenset({UU...0000000003')})
tests\test_f060_repositorio_lote.py:294: AssertionError: assert frozenset() == frozenset({UU...0000000002')})
tests\test_f060_repositorio_lote.py:316: AssertionError: assert ResultadoDelL...s=frozenset()) == ResultadoDelL...000000003')}))
tests\test_f060_repositorio_lote.py:316: AssertionError: assert ResultadoDelL...s=frozenset()) == ResultadoDelL...000000003')}))
tests\test_f060_repositorio_lote.py:342: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_repositorio_lote.py:342: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_repositorio_lote.py:342: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_repositorio_lote.py:342: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_repositorio_lote.py:368: Failed: DID NOT RAISE ValueError
tests\test_f060_repositorio_lote.py:391: assert []
tests\test_f060_repositorio_lote.py:391: assert []
tests\test_f060_repositorio_lote.py:461: Failed: DID NOT RAISE ValueError
tests\test_f060_repositorio_lote.py:461: Failed: DID NOT RAISE ValueError
tests\test_f060_repositorio_lote.py:461: Failed: DID NOT RAISE ValueError
tests\test_f060_repositorio_lote.py:461: Failed: DID NOT RAISE ValueError
24 failed, 3 passed in 0.53s
```

Los **3 que pasan en rojo**, y por qué no es un problema:

- `test_f060_r12_el_repositorio_cumple_el_puerto`: el esqueleto ya tiene el método y el puerto aún no lo exige. Es
  la guarda para GREEN.
- `test_f060_r15_el_repositorio_no_escribe_sql_propio`: guarda estática. El repositorio no tenía SQL escrito a mano
  y no debe empezar a tenerlo.
- `test_f060_r16_lote_vacio_sin_transaccion`: el esqueleto no abre nada. En GREEN vigila que el lote vacío no abra
  transacción.

Colindantes con el esqueleto: `tests/test_f056_repositorio_revision.py tests/test_f056_ddl.py` → **135 passed**.
`ruff check` de los tres ficheros: `All checks passed!`.

Commit: `e259f23 F-060 T4: RED del lote en la base (test con conexión falsa y esqueleto neutro)`. Lleva el test, el
esqueleto en `domain/ports/revision.py` y `repositorio_revision_pg.py`, y T4 marcada en `tasks.md`.

### BLOQUEO antes de T5 · la spec choca con un test de F-056 que no se puede tocar (resuelto: opción (a))

**Qué pide la spec.** `design.md` §7 dice que «`domain/ports/revision.py` **gana** un método» en `RevisionPort`
(`registrar_lote`), y §12 lo repite. T5 lo implementa, y su verificación incluye
`tests/test_f056_repositorio_revision.py`.

**Qué lo impide.** `tests/test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`
fija la lista **exacta** de los públicos de `RevisionPort` (`sorted(vars(RevisionPort))` igual a las seis de
F-056). Un séptimo método lo rompe. Y la spec prohíbe tocar ese test en tres sitios:

- `design.md` §12: «No se toca: … los tests de F-036 y F-056». Los únicos que se amplían son
  `test_f010_endpoints_protegidos.py` y `test_f053_documentacion.py`.
- R39 y T19: «los tests de F-036 y F-056 sin tocar salvo los dos ampliados», y ninguno de esos dos es de F-056.
- La cabecera de `tasks.md`: «si un test de F-036 o de F-056 … falla por un cambio de F-060, se para y se
  informa: no se relaja».

**Comprobado, no supuesto.** Con el esqueleto de T4 ya commiteado, añadí **de forma temporal, solo en el árbol de
trabajo**, un `registrar_lote` vacío a `RevisionPort`, y lancé los tres ficheros de F-056 que miran el puerto, el
pipeline y el borde:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_repositorio_revision.py tests/test_f056_pipeline_revision.py tests/test_f056_revision_http.py -q -p no:cacheprovider --tb=short -rf
```
```
___________ test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5 ___________
tests\test_f056_repositorio_revision.py:403: in test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5
    assert publicos == [
E   AssertionError: assert ['aprobadas',...ar_lote', ...] == ['aprobadas',..., 'situacion']
E     
E     At index 5 diff: 'registrar_lote' != 'situacion'
E     Left contains one more item: 'situacion'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5
1 failed, 356 passed in 4.78s
```

Lo revertí con `git checkout -- domain/ports/revision.py`, y el árbol quedó limpio. Es el **único** test de F-056
que cae. Los dobles de F-056 (`RevisionEnMemoria` de `tests/utiles_revision.py`) no se comprueban con `isinstance`
contra el puerto, así que no les afecta.

**No he elegido salida**: sería improvisar sobre una spec aprobada. Opciones para el humano, con lo que cuesta
cada una:

- **(a) Recomendada: ampliar ese test de F-056 sin quitar nada**, como ya se hace con `test_f010` y `test_f053`.
  La lista pasaría a ser las seis más `registrar_lote` (o el test comprobaría que las seis siguen y que lo único
  nuevo es `registrar_lote`). Exige enmendar la spec en tres sitios: `design.md` §12 (añadir
  `test_f056_repositorio_revision.py` a «ampliando sin quitar»), R39 y T19 («salvo los **tres** ampliados»).
  El código de §7 queda tal cual y T4 no cambia.
- **(b) Un puerto aparte para el lote**, por ejemplo `LoteDeRevisionPort` en `domain/ports/revision.py`, con
  `registrar_lote`, que implementa el mismo `RepositorioRevisionPostgres`. `RevisionPort` no cambia y no se toca
  ningún test de F-056. A cambio, cambian `design.md` §7 y §8 (`normalizar_ubicaciones` recibiría el repositorio
  tipado por los dos puertos, o en dos parámetros) y el primer caso de T4
  (`…_el_puerto_gana_registrar_lote…`), que pasaría a mirar el puerto nuevo. Además deja más superficie a F-059,
  que amplía la misma costura.
- **Descartada:** declarar `registrar_lote` en una clase base de `RevisionPort` para que `vars(RevisionPort)` no lo
  vea. Cumpliría el test en la letra y lo burlaría en el fondo.

### Decisión del humano (2026-10-10) · commit `fabbd7f`

**Opción (a).** `test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5` se amplía sin relajarse: sigue
comparando la lista **exacta** de los públicos de `RevisionPort`, que ahora tiene siete elementos (las seis de
F-056 más `registrar_lote`). Lo único añadido es esa entrada y un docstring que cita la decisión. Ninguna otra
aserción de F-056 cambia (`git diff 66c981d -- services/postventa-api/tests/test_f056_repositorio_revision.py`:
+4 líneas, ninguna quitada).

La excepción queda declarada en la spec, con «Decisión del humano 2026-10-10»: `design.md` §12 (y su fila R37–R39
de §13), R39 en `requirements.md`, T19 y la cabecera de `tasks.md`. En el mismo commit, F-060 volvió a
`in_progress` en `harness/features.json`, regeneré `BACKLOG.md` con `harness/backlog.py` y sustituí el rótulo de
bloqueo de `progress/current.md` por una línea con la decisión.

Entre `fabbd7f` y `29bb77b` ese test de F-056 estuvo en rojo, porque el puerto aún no tenía el séptimo método. Es
el rojo esperado de la ampliación, y T5 lo puso en verde.

### T5 · GREEN · commit `29bb77b`

- `domain/ports/revision.py`: `ResultadoDelLote` pasa a `frozen`, con `registradas` (incidencia → `revision_id`)
  y `desactualizadas`. `RevisionPort` gana `registrar_lote(*, revisiones, esperadas)`. El docstring del módulo
  cuenta la séptima operación. Las seis de F-056 no cambian.
- `infrastructure/persistencia/repositorio_revision_pg.py`, `registrar_lote` en cuatro pasos, en el orden de §7:
  1. Lote vacío: devuelve un resultado vacío sin abrir nada.
  2. Precondiciones: si alguna incidencia está repetida, o si a alguna revisión le falta su esperada,
     `ValueError` antes de abrir nada.
  3. `_en_transaccion("registrar_lote", …)`, el mismo de F-036/F-056: `ROLLBACK` y `PersistenciaNoDisponible` con
     la operación y el tipo si la base falla; `ROLLBACK` y el error tal cual si falla otra cosa.
  4. `_registrar_lote`: `select_bloquear` y `select_ultimas_revisiones` de las incidencias del lote. Después,
     recorriendo las revisiones en orden de `incidencia_id`, la frescura de cada una (`como_uuid` sobre lo que
     devuelve la base). Las frescas van a `insert_revision` y las demás a `desactualizadas`.
- **Sentencias reutilizadas sin cambiar**: `git diff 66c981d -- …/sentencias_revision.py` está vacío. El
  repositorio no lleva SQL propio (lo vigila `test_f060_r15_el_repositorio_no_escribe_sql_propio`).
- Decisiones dentro de la spec:
  - Se bloquean y se comparan **solo** las incidencias de las revisiones del lote. Si `esperadas` trae una
    incidencia de más, se ignora: §7 pide «cada revisión con su esperada» y no dice nada de las sobrantes. El plan
    de F-060 da exactamente una por revisión.
  - **Sin línea de log en el repositorio**: §9.3 pone los logs en el endpoint y en la importación (Bloques 3 y
    4), con los recuentos.

Verificación de `tasks.md`, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_repositorio_lote.py tests/test_f056_repositorio_revision.py tests/test_f056_ddl.py -q -p no:cacheprovider --tb=short
162 passed in 2.64s
```

Colindantes: `test_f056_pipeline_revision.py`, `test_f056_revision_http.py`, `test_f056_alcance_cerrado.py`,
`test_f005_arquitectura.py`, `test_f036_arquitectura.py`, `test_f006_repo_sin_identificadores.py` y
`test_f060_normalizacion_dominio.py` dan **426 passed, 9 skipped** en 27,22 s. Los 9 saltados son los controles de
diff de `test_f056_alcance_cerrado.py`, que solo corren en la rama de F-056 (`_diff_de_la_rama_o_saltar`). No son de
este bloque.

Cobertura de los dos ficheros de producción del bloque, con `coverage run --include=…` sobre
`test_f060_repositorio_lote.py` y `test_f056_repositorio_revision.py`: `domain/ports/revision.py` **20/20** y
`repositorio_revision_pg.py` **82/82**, es decir, **100 %**. `ruff check` de los ficheros tocados:
`All checks passed!`.

### T6 · `tests_bbdd/tests/test_f060_bbdd_lote.py` · commit `5bf9686`

Cinco tests contra la base efímera, todos con `@requiere_base`. Las fixtures son las de `tests_bbdd/tests/conftest.py`
y la limpieza es la de `test_f056_bbdd_revision.py`, solo en la base del contenedor. El plan **no** se escribe a
mano: sale de `planificar_normalizacion` sobre lo que devuelve `listar`, con la lista inventada `("Sala Ejemplo",
"Patio Ficticio")` de la unidad `9903.01VIVIENDA 1.` y tres filas importadas como «sala ejemplo», «PATIO
FICTICIO» y «Sala ejemplo».

| Test | Qué demuestra | R |
|---|---|---|
| `test_f060_r12_r15_un_lote_de_tres_escribe_tres_del_sistema_y_la_bandeja_intacta` | 3 filas `editar` con el texto exacto, `revisado_por` y `revisado_correo` iguales a `sistema:normalizar_ubicacion` (los `CHECK` de F-056 lo admiten), en orden de `incidencia_id`; los `revision_id` devueltos son los de la base; la bandeja, igual fila a fila; la importada sigue en minúsculas | R12, R15 |
| `test_f060_r12_la_esperada_de_una_ya_revisada_es_su_ultima` | Con una edición humana previa, la esperada es su `revision_id` y la normalización se apila encima sin perder la descripción editada | R9, R12 |
| `test_f060_r13_una_revision_humana_entre_el_plan_y_el_lote_se_salta` | **Dos conexiones**: la otra registra una edición humana entre el plan y el lote; esa se salta (su última sigue siendo la humana, con su correo y la ubicación sin normalizar) y las otras dos se escriben | R13 |
| `test_f060_r12_r13_el_lote_espera_al_for_update_de_otra_conexion` | **Dos conexiones con bloqueo**: la otra hace `FOR UPDATE` de una sin confirmar; el lote, en un hilo, **espera** (sigue vivo al cabo de 1 s); la otra inserta y confirma; el lote la salta y escribe las otras dos | R12, R13 |
| `test_f060_r13_el_lote_repetido_no_escribe_nada` | El mismo lote con las esperadas viejas: las tres desactualizadas y la tabla igual; un plan nuevo ya no propone ninguna | R13, R21 |

Verificación de `tasks.md`:

```
.venv/Scripts/python.exe -m pytest --collect-only -q tests_bbdd/tests/test_f060_bbdd_lote.py
5 tests collected in 0.27s
```

Sin DSN, `pytest tests_bbdd/tests/test_f060_bbdd_lote.py -q -rs` da **5 skipped**, cada uno con el motivo de
`requiere_base`. Es el fusible esperado. `ruff check`: `All checks passed!`. Un aviso de ruff (`BLE001`, capturar
`Exception` en el hilo) se resolvió capturando `ErrorDePersistencia`, que es lo único que el repositorio puede
levantar desde la base. Cualquier otra cosa deja vacía la lista de resultados y el test cae al desempaquetarla.

**Que estos tests pasen contra PostgreSQL no está comprobado**: lo comprueba T7, que es del humano.

### Para el humano · T7 (MANUAL)

Con **Docker Desktop arrancado**, desde la raíz del repositorio en PowerShell:

```
powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
```

El script levanta un PostgreSQL desechable en `127.0.0.1`, ejecuta `pytest tests_bbdd -q` y lo destruye pase lo que
pase. Nunca toca `psql-albaranes-rs9k2`: el `conftest` aborta si el DSN no es local.

**Lo que debe salir**: **58 passed**, con **0 skipped** y 0 failed. Desglose (recogida real con
`--collect-only`, 2026-10-10):

| Fichero | Tests |
|---|---|
| `test_f005_bbdd_aislamiento.py` | 4 |
| `test_f005_bbdd_ddl_idempotente.py` | 4 |
| `test_f005_bbdd_reproceso.py` | 2 |
| `test_f036_bbdd_bandeja.py` | 15 |
| `test_f056_bbdd_revision.py` | 28 |
| `test_f060_bbdd_lote.py` | **5** (nuevos) |
| **Total** | **58** |

Sin F-060 eran 53, la misma cifra que la T8 de F-056. Si la última línea dice `skipped`, la variable
`POSTVENTA_PG_TEST_DSN` no ha llegado a la suite y **la ejecución no vale**.

**Qué copiar** a este informe (o pegárselo al líder): la última línea de `pytest`, con el número de passed y el
tiempo (`58 passed in N.NNs`); la línea final del script (`SUITE DE BASE DE DATOS EN VERDE.`); y, si algo falla,
el bloque `FAILURES` entero. Las trazas solo llevan datos ficticios.

### Ficheros tocados en el Bloque 2

- Nuevos: `services/postventa-api/tests/test_f060_repositorio_lote.py`,
  `services/postventa-api/tests_bbdd/tests/test_f060_bbdd_lote.py`.
- Producción: `services/postventa-api/domain/ports/revision.py`,
  `services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py`.
- Test de F-056 ampliado (decisión del humano): `services/postventa-api/tests/test_f056_repositorio_revision.py`
  (+4 líneas).
- Spec: `requirements.md` (R39), `design.md` (§12 y §13) y `tasks.md` (cabecera, T19, T4–T6 y T8 marcadas).
- Arnés y memoria: `harness/features.json` (`blocked` y vuelta a `in_progress`), `BACKLOG.md`, `progress/current.md`,
  `progress/mutacion_F-060_bloque2.md` y este informe.
- **No se tocaron**: `sentencias_revision.py`, ningún `.sql` (sin DDL), `.env`, `services/postventa-front/` ni la
  plantilla.

### Commits del Bloque 2

| Commit | Qué |
|---|---|
| `e259f23` | F-060 T4: RED (test y esqueleto neutro) |
| `3df8399` | Bloqueo antes de T5: informe y estado |
| `fabbd7f` | Decisión del humano: test del puerto de F-056 con siete operaciones; excepción en la spec |
| `29bb77b` | F-060 T5: GREEN |
| `5bf9686` | F-060 T6: tests contra la base efímera |
| `be10cf2` | F-060 T8: mutación del bloque, dos tests que matan mutantes a mano, e informe |

### T8 · Mutación del bloque

```
python -m harness.mutacion --feature F-060 --base 66c981d --timeout 1800 --salida progress/mutacion_F-060_bloque2.md
```

Esperé a que terminara. Informe en `progress/mutacion_F-060_bloque2.md`. Alcance: **2 ficheros y 94 líneas** de
producción (`domain/ports/revision.py`, 38; `repositorio_revision_pg.py`, 56). **4 mutantes, 4 muertos, 0
supervivientes, 0 timeouts**, en 744,4 s con **4 workers**:

| Mutante | Línea | Lo mata |
|---|---|---|
| `if not revisiones:` → `if revisiones:` | `repositorio_revision_pg.py:123` | toda la suite del lote |
| `!=` → `==` en la frescura | `repositorio_revision_pg.py:216` | R12 y R13 |
| `!=` → `==` en la precondición de repetidas | `repositorio_revision_pg.py:126` | R12 y las precondiciones |
| `frozen=True` → `frozen=False` | `domain/ports/revision.py:55` | `test_f060_r12_el_resultado_del_lote_es_inmutable` |

**Cuatro mutantes para 94 líneas es poco, y lo digo.** Ningún fichero del alcance sale con 0, pero la herramienta
no muta `not in`, ni quita un `sorted`, ni cambia un `continue`, ni una llamada como `como_uuid`, ni un literal de
texto. Por eso hice además **diez mutantes a mano** sobre las decisiones del lote. Los apliqué de forma temporal
al fichero de producción, uno a uno, con un script fuera del repositorio. Cada uno se ejecutó contra
`tests/test_f060_repositorio_lote.py` y `tests/test_f056_repositorio_revision.py` con `-x`, y el fichero se
restauró al final (`git status` limpio en producción).

**Primera pasada: 8 muertos y 2 vivos.** Los dos vivos eran huecos reales de los tests, no mutantes equivalentes:

- **H8 · bloquear y comparar las claves de `esperadas` en vez de las incidencias del lote.** Con un lote bien
  formado da lo mismo, pero con una esperada de más bloquearía otra fila de la bandeja. Severidad **media**: el plan
  de F-060 nunca da esperadas de más, pero R12 dice «las filas de la bandeja de todas» (las del lote). Lo mata el
  test nuevo `test_f060_r12_se_bloquean_solo_las_del_lote_aunque_sobre_una_esperada`.
- **H9 · `desactualizadas` como `set` mutable en vez de `frozenset`.** `set() == frozenset()` es verdadero, así que
  las igualdades no lo veían. Severidad **baja**: rompe el contrato del tipo, no el resultado. Lo mata una aserción
  `isinstance(…, frozenset)` añadida a `test_f060_r13_una_desactualizada_se_salta_y_las_demas_se_escriben`.

**Segunda pasada, con los dos tests añadidos: 10 de 10 muertos.**

| # | Mutante a mano | Resultado | Primer test que cae |
|---|---|---|---|
| H1 | `not in esperadas` → `in esperadas` | MUERTO | `…_bloquea_todas_mira_todas_inserta_en_orden_y_confirma` |
| H2 | sin `sorted` (orden de entrada) | MUERTO | `…_bloquea_todas_mira_todas_inserta_en_orden_y_confirma` |
| H3 | sin `como_uuid` en las últimas | MUERTO | `…_una_desactualizada_se_salta…[otro-guardo-la-primera]` |
| H4 | `continue` → `break` | MUERTO | `…_una_desactualizada_se_salta…[otro-guardo-la-primera]` |
| H5 | sin el atajo del lote vacío | MUERTO | `test_f060_r16_lote_vacio_sin_transaccion` |
| H6 | operación `registrar_lote` → `registrar_revision` | MUERTO | `…_si_la_base_falla_rollback_y_503_sin_parametros[al-bloquear]` |
| H7 | sin la precondición de repetidas | MUERTO | `…_precondiciones_value_error_sin_abrir_nada[una-repetida]` |
| H8 | bloquear las claves de `esperadas` | MUERTO (vivo antes de los tests nuevos) | `…_se_bloquean_solo_las_del_lote_aunque_sobre_una_esperada` |
| H9 | `desactualizadas` sin `frozenset` | MUERTO (vivo antes de los tests nuevos) | `…_una_desactualizada_se_salta…[otro-guardo-la-primera]` |
| H10 | sin la precondición de la esperada | MUERTO | `…_precondiciones_value_error_sin_abrir_nada[una-sin-esperada]` |

Los dos tests añadidos solo tocan `tests/test_f060_repositorio_lote.py`, con 28 casos y +19 líneas. El código de
producción no cambia, así que la campaña de la herramienta sigue valiendo. Después de añadirlos,
`test_f060_repositorio_lote.py`, `test_f056_repositorio_revision.py`, `test_f056_ddl.py` y
`test_f006_repo_sin_identificadores.py` dan **211 passed** en 18,62 s. `ruff check`: `All checks passed!`.

**Supervivientes abiertos: ninguno.**

### Evidencias (Bloque 2)

| Evidencia | Valor |
|---|---|
| Tests de T4 en rojo (RED) | 27 casos: **24 failed** (todos por aserción) y 3 passed (justificados), en 0,53 s |
| Tests del bloque en verde | `test_f060_repositorio_lote.py` **28 passed**. Con `test_f056_repositorio_revision.py`, `test_f056_ddl.py` y `test_f006_repo_sin_identificadores.py`: **211 passed** en 18,62 s |
| Colindantes (F-056 pipeline/HTTP/alcance, arquitectura F-005/F-036, F-006, dominio de F-060) | **426 passed, 9 skipped** en 27,22 s (los 9: controles de diff de F-056, que solo corren en su rama) |
| `tests_bbdd` de F-060 | 5 recogidos; sin DSN, 5 skipped (fusible). **Contra PostgreSQL: pendiente de T7 (humano)** |
| Cobertura de las líneas cambiadas | `domain/ports/revision.py` 20/20 y `repositorio_revision_pg.py` 82/82: **100 %** (`coverage run --include`, ficheros enteros) |
| Mutación (herramienta) | **4 generados, 4 muertos, 0 supervivientes**, 0 timeouts, 744,4 s, **4 workers** |
| Mutación (a mano) | **10 de 10 muertos** (H8 y H9 vivos en la primera pasada; muertos con dos tests nuevos) |
| `bash harness/init.sh` | No relanzado en este bloque, por indicación del líder. Se pasa en T23 |
| Suite completa | No ejecutada (solo en T23) |

## Bloque 3 · La normalización de una obra y su endpoint · T9, T10, T11 y T12 · 2026-10-10

Encargo: T9 (RED), T10, T11 y T12 (mutación). Nada del Bloque 4. Rama `feature/F-060-normalizar-ubicaciones`, HEAD de
partida **`91ad35d`** (el hash anterior a T9: el `--base` de la mutación de este bloque).

### Precondiciones

- Rama comprobada: `feature/F-060-normalizar-ubicaciones`, árbol limpio en `91ad35d`.
- `bash harness/init.sh` en verde, completo, antes de tocar nada: suite del servicio `api` **7785 passed, 123
  skipped en 883,40 s**; `PUERTA COBERTURA: 100.0% de 110 líneas cambiadas cubiertas (110/110, umbral 80%, nivel
  critico)`; `ENTORNO LISTO`.

### T9 · Fase RED

Tres ficheros de test y un doble nuevo, contra un **esqueleto neutro** (como en los Bloques 1 y 2):

- `application/pipelines/revision.py` gana `ResultadoNormalizacion` (sin `frozen`) y `normalizar_ubicaciones`, que
  devuelve un recuento a cero sin leer ni escribir nada. Lo que ya había no cambia.
- `interface_adapters/api/normalizacion.py` (nuevo): solo los nombres que los tests sustituyen (`time`,
  `obtener_ajustes`, `construir_catalogo_obra`, `construir_fuente_de_ubicaciones`, `construir_revision`) y
  `normalizar_obra`, que devuelve `{}` sin validar ni construir.
- **Sin ruta en `function_app.py`**: añadirla es T11. Por eso los tests que van por la ruta caen en la aserción de
  `_ruta` («function_app no publica la ruta») o de `ruta_registrada` («el host no publica ninguna ruta»); los del
  handler caen cada uno en su aserción.

| Fichero | Qué fija |
|---|---|
| `tests/utiles_normalizacion.py` (nuevo) | `RevisionConLote`: subclase de `RevisionEnMemoria` de F-056 (**sin tocar** `utiles_revision.py`) con `registrar_lote` y la semántica del repositorio del Bloque 2: lote vacío, precondiciones, frescura por fila en orden de `incidencia_id`, fallo de la base sin nada escrito, y un gancho `antes_del_lote` para la «otra persona» |
| `tests/test_f060_pipeline_normalizacion.py` (nuevo, 28 casos) | R17 (10.001 → `BandejaDemasiadoGrande` con `contar` y sin leer ubicaciones ni escribir, con ensayo y sin él; 10.000 justas sí); R18 (una lectura con el catálogo recibido, el mismo objeto; la lista es la de la fuente); R10 (el recuento de diez incidencias con cada caso y su suma); R19 (ensayo sin lote); R20 (el lote del plan: ids, textos de Sigrid, `editar`, `QUIEN_SISTEMA`, hora, sin motivo, huella, esperadas; la esperada de una ya editada; un conflicto se cuenta sin abortar; plan vacío sin lote); R21 (segunda ejecución a cero); R22 (fila y historial por los handlers de F-056, y el resumen baja en las normalizadas); R7/R23 (ambigua, sin coincidencia y lista vacía, iguales y fuera de lista; aprobada y descartada intactas); R24 (normalizar y aprobar → candidata con «Baño»); R25 (sin normalizar, 409 y 400); **O-3** (las listas salen de `fuente_de_ubicaciones` de F-056, ya filtradas: un valor de Sigrid de 49 con la misma clave que un texto de 48 —«Straße…»/«Strasse…»— no llega al plan; y su control: sin el filtro, la regla lo propondría); los fallos (ubicaciones caídas o al techo, la base al listar y en el lote) suben sin nada escrito; el resultado es inmutable y sin textos |
| `tests/test_f060_normalizar_http.py` (nuevo, 98 casos) | R26 (30 cuerpos malos —lista, texto, nulo, número, vacío, sin cada clave, `confirmado` `"true"`/`1`/`false`/`null`, `ensayo` `"true"`/`"false"`/`1`/`0`/`null`/lista, claves de más `usuario_oid`/`usuario_correo`/`tope`, clave en mayúsculas, obra vacía, en blanco, número, nula, con barra, de 25, con «Ñ»—: en el handler, la excepción exacta sin construir nada y sin repetir lo recibido; en la ruta, 400 `peticion_invalida`, sin repetirlo en la respuesta ni en el log; un cuerpo que no es JSON; la obra normalizada como F-036); R27 (las diez claves exactas, solo enteros salvo `obra` y `ensayo`; la ruta, 200 sin ningún texto, `incidencia_id`, `oid` ni correo); R19/R20 (el ensayo no escribe; la real escribe la revisión del sistema con la hora inyectada; sin hora inyectada, la de ahora en UTC; la identidad es la del sistema aunque venga `x-ms-client-principal`); R29 (Sigrid antes que la base, tres lecturas; si falla la construcción de Sigrid, la base no se construye y la ruta da 503); R28 (nueve errores: sin unidades 404, ambigua 409, al techo 409, ubicaciones al techo 409, bandeja de más 409 con el total, Sigrid caído, ubicaciones caídas, la base al listar y **el lote** 503 «no se ha escrito nada» —O-3 del Bloque 2—, en el handler y en la ruta, y sin secretos en el log); **O-3** en el borde (el endpoint compone `construir_fuente_de_ubicaciones` de F-056 sin sustituirla: el valor de 49 no llega); R30 (una sola línea, con la forma exacta, con ensayo y sin él; los segundos con un reloj falso, `2.50`; sin secretos); la ruta `POST` anónima |
| `tests/test_f010_endpoints_protegidos.py` (ampliado) | `revision/normalizar` en `ENDPOINTS` y la cuenta de 20 a **21**; el comentario de F-060 y «veintiuno» en el docstring. **No se quita nada** (`git diff`: +9 líneas, 3 cambiadas por la cuenta: «veinte» → «veintiun(o)» y `== 20` → `== 21`) |

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_pipeline_normalizacion.py tests/test_f060_normalizar_http.py tests/test_f010_endpoints_protegidos.py -q -p no:cacheprovider --tb=line -rf
```

Salida real (las líneas `--tb=line` de cada fallo, la lista de `FAILED` y el total; solo se ha recortado el prefijo
absoluto de la ruta):

```
tests\test_f060_pipeline_normalizacion.py:191: Failed: DID NOT RAISE BandejaDemasiadoGrande
tests\test_f060_pipeline_normalizacion.py:191: Failed: DID NOT RAISE BandejaDemasiadoGrande
tests\test_f060_pipeline_normalizacion.py:210: AssertionError: assert 0 == 10000
tests\test_f060_pipeline_normalizacion.py:225: AssertionError: assert [] == ['revision.li...gistrar_lote']
tests\test_f060_pipeline_normalizacion.py:237: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=2)
tests\test_f060_pipeline_normalizacion.py:237: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=2)
tests\test_f060_pipeline_normalizacion.py:256: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_pipeline_normalizacion.py:277: AssertionError: assert [] == ['revision.li...'ubicaciones']
tests\test_f060_pipeline_normalizacion.py:300: AssertionError: assert ResultadoNorm... conflictos=0) == ResultadoNorm... conflictos=0)
tests\test_f060_pipeline_normalizacion.py:330: assert 0 == 1
tests\test_f060_pipeline_normalizacion.py:346: assert (0, 0) == (2, 1)
tests\test_f060_pipeline_normalizacion.py:363: AssertionError: assert [] == ['revision.li...'ubicaciones']
tests\test_f060_pipeline_normalizacion.py:387: AssertionError: assert 0 == 10
tests\test_f060_pipeline_normalizacion.py:423: AssertionError: assert 'baño' == 'Baño'
tests\test_f060_pipeline_normalizacion.py:449: assert 0 == (0 + 3)
tests\test_f060_pipeline_normalizacion.py:460: AssertionError: assert 0 == 3
tests\test_f060_pipeline_normalizacion.py:498: AssertionError: assert 0 == 3
tests\test_f060_pipeline_normalizacion.py:610: AssertionError: assert RecuentoNorma...o_editables=0) == RecuentoNorma...o_editables=0)
tests\test_f060_pipeline_normalizacion.py:634: Failed: DID NOT RAISE CatalogoNoDisponible
tests\test_f060_pipeline_normalizacion.py:634: Failed: DID NOT RAISE CatalogoSinVerificar
tests\test_f060_pipeline_normalizacion.py:647: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_pipeline_normalizacion.py:658: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_pipeline_normalizacion.py:673: Failed: DID NOT RAISE FrozenInstanceError
tests\test_f060_pipeline_normalizacion.py:685: AssertionError: assert 0 == 3
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:287: Failed: DID NOT RAISE Exception
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:324: AssertionError: assert None == '9901'
tests\test_f060_normalizar_http.py:337: AssertionError: assert {} == {'obra': '990...ctas': 3, ...}
tests\test_f060_normalizar_http.py:337: AssertionError: assert {} == {'obra': '990...ctas': 3, ...}
tests\test_f060_normalizar_http.py:358: AssertionError: assert [] == [(UUID('00000...imezone.utc))]
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:410: AssertionError: assert [] == ['catalogo', ...', 'revision']
tests\test_f060_normalizar_http.py:410: AssertionError: assert [] == ['catalogo', ...', 'revision']
tests\test_f060_normalizar_http.py:439: Failed: DID NOT RAISE ConfiguracionSigridIncompleta
tests\test_f060_normalizar_http.py:439: Failed: DID NOT RAISE CatalogoNoDisponible
tests\test_f060_normalizar_http.py:439: Failed: DID NOT RAISE ConfiguracionSigridIncompleta
tests\test_f060_normalizar_http.py:439: Failed: DID NOT RAISE ConfiguracionPgIncompleta
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE ObraSinUnidades
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE ObraAmbigua
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE CatalogoSinVerificar
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE CatalogoSinVerificar
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE BandejaDemasiadoGrande
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE CatalogoNoDisponible
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE CatalogoNoDisponible
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_normalizar_http.py:518: Failed: DID NOT RAISE PersistenciaNoDisponible
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:196: AssertionError: function_app no publica la ruta «revision_normalizar»
tests\test_f060_normalizar_http.py:585: assert (None, None, None) == (1, 1, 1)
tests\test_f060_normalizar_http.py:612: assert 0 == 1
tests\test_f060_normalizar_http.py:612: assert 0 == 1
tests\test_f060_normalizar_http.py:631: assert 0 == 1
tests\utiles_rutas.py:43: AssertionError: el host no publica ninguna ruta «revision_normalizar»
tests\test_f010_endpoints_protegidos.py:203: AssertionError: assert ['adjuntar', ...'cerrar', ...] == ['adjuntar', ...'cerrar', ...]
tests\test_f010_endpoints_protegidos.py:272: assert 20 == 21
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe[True]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe[False]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r17_justo_en_el_tope_si_se_normaliza
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r18_una_lectura_de_ubicaciones_con_el_catalogo_recibido
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r10_r18_el_recuento_de_la_obra_y_su_suma[True]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r10_r18_el_recuento_de_la_obra_y_su_suma[False]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r18_mira_la_lista_de_la_fuente_y_no_otra
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r19_el_ensayo_no_llama_al_lote_ni_escribe
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r20_la_real_registra_el_lote_del_plan
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r9_r20_la_esperada_es_la_ultima_leida
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r13_r20_un_conflicto_se_cuenta_y_no_aborta_las_demas
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r20_un_plan_vacio_no_llama_al_lote
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r21_dos_ejecuciones_la_segunda_no_tiene_nada_que_normalizar
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r22_la_fila_normalizada_en_el_listado_y_su_historial
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r22_el_resumen_baja_en_las_normalizadas
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r7_r23_lo_que_no_se_normaliza_sigue_como_estaba
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r24_normalizar_y_aprobar_da_la_candidata_con_el_texto_de_sigrid
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_o3_las_listas_salen_de_la_fuente_de_f056_ya_filtradas
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r28_un_fallo_de_las_ubicaciones_sube_sin_escribir[sigrid-caido]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r28_un_fallo_de_las_ubicaciones_sube_sin_escribir[al-techo]
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r14_un_fallo_de_la_base_en_el_lote_sube_sin_nada_escrito
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_r17_un_fallo_de_la_base_al_listar_sube_sin_leer_sigrid
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_el_resultado_es_inmutable
FAILED tests/test_f060_pipeline_normalizacion.py::test_f060_el_resultado_no_lleva_textos
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[lista]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[numero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[vacio]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[sin-obra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[sin-confirmado]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[sin-ensayo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[solo-obra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[confirmado-texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[confirmado-uno]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[confirmado-falso]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[confirmado-nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-texto-falso]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-uno]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-cero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[ensayo-lista]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[de-mas-oid]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[de-mas-correo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[de-mas-tope]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[clave-en-mayusculas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-vacia]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-blancos]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-numero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-nula]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-con-barra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-larga]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[obra-con-enye]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[lista]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[numero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[vacio]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[sin-obra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[sin-confirmado]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[sin-ensayo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[solo-obra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[confirmado-texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[confirmado-uno]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[confirmado-falso]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[confirmado-nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-texto]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-texto-falso]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-uno]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-cero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-nulo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[ensayo-lista]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[de-mas-oid]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[de-mas-correo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[de-mas-tope]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[clave-en-mayusculas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-vacia]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-blancos]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-numero]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-nula]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-con-barra]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-larga]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada[obra-con-enye]
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_un_cuerpo_que_no_es_json_es_400_sin_construir_nada
FAILED tests/test_f060_normalizar_http.py::test_f060_r26_la_obra_se_normaliza_como_en_f036
FAILED tests/test_f060_normalizar_http.py::test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento[True]
FAILED tests/test_f060_normalizar_http.py::test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento[False]
FAILED tests/test_f060_normalizar_http.py::test_f060_r20_la_real_escribe_revisiones_del_sistema_con_la_hora_de_la_peticion
FAILED tests/test_f060_normalizar_http.py::test_f060_r27_la_ruta_responde_200_con_solo_numeros
FAILED tests/test_f060_normalizar_http.py::test_f060_d4_la_identidad_es_la_del_sistema_aunque_vengan_cabeceras
FAILED tests/test_f060_normalizar_http.py::test_f060_r20_sin_hora_inyectada_es_la_de_ahora_en_utc
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas[True]
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas[False]
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sin_sigrid_no_se_llega_a_construir_la_base[config-sigrid]
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sin_sigrid_no_se_llega_a_construir_la_base[entorno-sin-sigrid]
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sin_sigrid_no_se_llega_a_construir_la_base[config-ubicaciones]
FAILED tests/test_f060_normalizar_http.py::test_f060_r29_sin_sigrid_no_se_llega_a_construir_la_base[config-pg]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[sin-unidades]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[ambigua]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[al-techo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[ubicaciones-al-techo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[bandeja-de-mas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[sigrid-caido]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[ubicaciones-caidas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[base-caida]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_el_handler_deja_subir_el_error_sin_escribir[lote-caido]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[sin-unidades]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[ambigua]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[al-techo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[ubicaciones-al-techo]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[bandeja-de-mas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[sigrid-caido]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[ubicaciones-caidas]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[base-caida]
FAILED tests/test_f060_normalizar_http.py::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir[lote-caido]
FAILED tests/test_f060_normalizar_http.py::test_f060_o3_el_endpoint_compone_la_fuente_de_f056_con_su_filtro
FAILED tests/test_f060_normalizar_http.py::test_f060_r30_una_linea_con_la_obra_el_recuento_y_los_segundos[True]
FAILED tests/test_f060_normalizar_http.py::test_f060_r30_una_linea_con_la_obra_el_recuento_y_los_segundos[False]
FAILED tests/test_f060_normalizar_http.py::test_f060_r30_los_segundos_son_los_de_la_peticion
FAILED tests/test_f060_normalizar_http.py::test_f060_s9_la_ruta_es_post_y_anonima
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada
FAILED tests/test_f010_endpoints_protegidos.py::test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay
123 failed, 11 passed in 1.73s
```

**123 fallan, todos por aserción** (`AssertionError`, `assert …` o `Failed: DID NOT RAISE`); ninguno por
`ImportError`, `AttributeError`, `TypeError` ni `IndexError` (una primera pasada tuvo un `IndexError` en
`test_f060_r9_r20_la_esperada_es_la_ultima_leida`, al indexar `lotes[0]` sin comprobar antes que hubiera lote; se
añadió `assert len(lotes) == 1` delante y la traza de arriba es la de después). De los 123, **44** son los de la
ruta, que caen en la aserción de que la ruta no existe (T11 la añade); los demás, en su propia aserción.

Los **11 que pasan en rojo**, y por qué:

| Test | Por qué pasa con el esqueleto |
|---|---|
| `test_f060_r25_sin_normalizar_aprobar_sigue_siendo_409`, `test_f060_r25_editar_con_la_variante_sigue_siendo_400[BAÑO]` y `[bAño]` | Guardas de D-5: la comparación de F-056 no cambia y ya da 409 y 400. Su contraparte (R24: normalizar y aprobar sí da candidata) falla |
| `test_f060_o3_el_detector_no_es_ciego_sin_filtro_se_propondria_el_de_49` | Control del test de O-3: demuestra que la regla del dominio (Bloque 1) **sí** propondría el valor de 49 si le llegara sin filtrar |
| `test_f060_r19_el_ensayo_no_escribe_nada` (HTTP) | El esqueleto no escribe nada, que es justo lo que pide el ensayo. Su contraparte (la real escribe) falla |
| Seis de `test_f010_endpoints_protegidos.py` (`…_cabecera_dice_donde_esta_la_proteccion_de_verdad`, `…_que_anade_la_cola_al_cuadro`, `…_donde_esta_el_control_de_acceso`, `…_de_identidad_no_protege`, `…_health_sigue_anonimo`, `…_ventana_de_escritura_en_archivar`) | No dependen de la cuenta de rutas: miran la cabecera de `function_app.py`. Los dos que cuentan rutas fallan (`assert 20 == 21` y la lista ordenada) |

Colindantes con el esqueleto: `tests/test_f056_pipeline_revision.py tests/test_f056_revision_http.py` en verde (ver
T10 y T11).

### T10 · GREEN · la aplicación

`application/pipelines/revision.py`: `ResultadoNormalizacion` pasa a `frozen` (con su docstring) y
`normalizar_ubicaciones` hace lo de `design.md` §8, en este orden: `revision.listar(tope=10.000)`; si vuelven más,
`contar` y `BandejaDemasiadoGrande` (sin leer las ubicaciones ni escribir); `ubicaciones(catalogo)` una vez;
`planificar_normalizacion` del dominio; y, solo si no es un ensayo **y** el plan trae revisiones,
`registrar_lote(revisiones=plan.revisiones, esperadas=plan.esperadas)`, con `normalizadas = len(registradas)` y
`conflictos = len(desactualizadas)`. Lo que ya había en el módulo **no cambia** (solo se añaden el import del
dominio, dos nombres a `__all__` y un apartado del docstring).

Decisión dentro de la spec: el comprobante del tope está **repetido** y no extraído de `listar_para_revisar` a una
función común, para no tocar el código de F-056 (T10: «sin cambiar lo que ya hay»). El mensaje del 409 dice
«normalización» en lugar de «revisión».

Verificación de `tasks.md`, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_pipeline_normalizacion.py tests/test_f056_pipeline_revision.py -q -p no:cacheprovider --tb=short
108 passed in 1.61s
```

Colindantes (dominio de F-060, arquitectura de F-005 y F-036, alcance de F-056): **144 passed, 9 skipped** en
6,74 s (los 9, los controles de diff de F-056 que solo corren en su rama). `ruff check`: `All checks passed!`.

### T11 · GREEN · el handler y la ruta

- `interface_adapters/api/normalizacion.py` (nuevo de verdad; sustituye al esqueleto): `normalizar_obra(cuerpo, *,
  revision, catalogo_obra, ubicaciones, ahora)`. En este orden: el cuerpo entero (`_peticion`: objeto con
  **exactamente** `obra`, `confirmado` y `ensayo`; `confirmado is True`; `ensayo` de tipo `bool`; la obra por
  `normalizar_codigo_obra`) **antes** de construir nada; la hora (la inyectada o `datetime.now(UTC)`); Sigrid
  primero (`construir_catalogo_obra`, `construir_fuente_de_ubicaciones` **de F-056, importada** de
  `interface_adapters/api/revision.py`, que no se toca) y la base después (`construir_revision`); `leer_catalogo`
  (las dos lecturas de F-036) y `normalizar_ubicaciones` (la tercera). Responde las diez claves de R27, solo
  números, y registra **una** línea `F-060 normalización de ubicaciones: obra=… ensayo=… examinadas=… no_exactas=…
  normalizables=… ambiguas=… sin_coincidencia=… no_editables=… normalizadas=… conflictos=… segundos=…` (§9.3), con
  los segundos de `time.perf_counter` desde la entrada.
- `function_app.py`: la ruta `revision_normalizar` (`POST revision/normalizar`, `ANONYMOUS`) con la traducción de
  errores del listado (400 `peticion_invalida` también para el cuerpo que no es JSON, como `revision/acciones`; 404
  `obra_sin_unidades`; 409 `obra_ambigua`, `catalogo_sin_verificar` y `bandeja_demasiado_grande` con el total; 503
  de Sigrid, su configuración y la base). Sin `ConfiguracionPlantillaInvalida`: este endpoint no carga la
  plantilla. En la cabecera, la entrada de la ruta en la lista de endpoints y un párrafo: no añade nada al cuadro
  de seguridad (solo recuentos) y «con él los anónimos son veintiuno». La frase de F-056 («Con él los anónimos son
  veinte») se conserva: es la historia del cuadro, y ningún test la fija.
- **O-3 de la review del Bloque 2 (un `CHECK` que falla tumba el lote).** El 503 del lote dice, con el mensaje
  común de `_sin_sigrid_o_sin_base`, «no se ha escrito nada», y es verdad: el `ROLLBACK` del Bloque 2 deshace el
  lote entero. Lo fijan `test_f060_r28_…[lote-caido]` (handler y ruta) y `test_f060_r14_…` del pipeline. Y la causa
  conocida de ese `CHECK` (un valor de más de 48) no puede llegar: las listas salen de la fuente de F-056
  (**O-3 de la review del Bloque 1**), fijado en la aplicación (`test_f060_o3_las_listas_salen_de_la_fuente_de_f056_ya_filtradas`)
  y en el borde sin sustituir la fuente (`test_f060_o3_el_endpoint_compone_la_fuente_de_f056_con_su_filtro`).
- **`docs/INTEGRACION.md` no se toca** (la cuenta de anónimos es del Bloque 5, T20). Ningún test lo exige ahora:
  `test_f012_…_declara_el_endpoint_nuevo…`, `test_f019_…` y `test_f053_…` cuentan las filas de la tabla de §8 del
  documento, no las rutas de `function_app.py`, y siguen en verde con «Los veinte». Hasta T20, el documento dice
  veinte y el código tiene veintiuna: es lo esperado entre bloques.

Test añadido en GREEN (no es de requisito central, es de la costura): `test_f060_r29_los_adaptadores_inyectados_no_se_construyen`.
Lo pidió la cobertura de ramas: sin él, los tres `if … is None` del handler solo se recorrían por un lado. Ahora
`interface_adapters/api/normalizacion.py` da **42/42 sentencias y 12/12 ramas**.

Verificación de `tasks.md`, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f060_normalizar_http.py tests/test_f010_endpoints_protegidos.py tests/test_f056_revision_http.py -q -p no:cacheprovider --tb=short
288 passed in 2.06s
```

(antes del test de la costura; con él, `test_f060_normalizar_http.py` tiene 99 casos y la línea es `289 passed`).

Colindantes: **todos** los tests que leen o importan `function_app.py` (47 ficheros, de F-001 a F-060, incluidos los
`…_alcance_cerrado` de F-031, F-034, F-036 y F-056 y `test_f019_logs_sin_datos_personales.py`), más los de pipeline y
repositorio de F-056, dominio y lote de F-060, arquitectura de F-005 y F-036, documentación de F-012, F-019 y F-053 y
`test_f006_repo_sin_identificadores.py`: **2229 passed, 29 skipped** en 66,18 s. Los saltados son controles de diff
que solo corren en la rama de su feature. `ruff check` de los ficheros tocados: `All checks passed!`.

### T12 · Mutación del bloque

```
python -m harness.mutacion --feature F-060 --base 91ad35d --timeout 1800 --salida progress/mutacion_F-060_bloque3.md
```

Lanzada tras el commit de T11 (`97a33ff`; los worktrees de la campaña salen de ese commit) y **esperada hasta el
final**, sin tocar el árbol mientras corría. Salida real (cabecera y cola):

```
F-060: 3 fichero(s), 308 línea(s) de producción (origen rama, 91ad35dbb0b6ae1a3c810ca2452f551987606bae..feature/F-060-normalizar-ubicaciones)
Campaña paralela: hasta 8 workers, uno por worktree.
...
17 mutantes evaluados, 17 muertos, 0 supervivientes, 0 timeouts en 1801.1 s
Informe: progress/mutacion_F-060_bloque3.md
```

**17/17 muertos, 0 supervivientes, 0 timeouts, 8 workers, 1801,1 s.** Por fichero (ninguno sale con 0 mutantes):
`application/pipelines/revision.py` 5 (el `>` del tope, `frozen`, el `not` y el `and` de «ni ensayo ni plan
vacío», el `0` inicial de los contadores); `function_app.py` 6 (los códigos 400 —del cuerpo que no es JSON y del
contrato—, 404, los dos 409 y el 200); `interface_adapters/api/normalizacion.py` 6 (el `not`, el `or` y el `!=` de
las claves exactas, `is not True`, el `not isinstance(ensayo, bool)` y el `-` de los segundos).

**Lo que la herramienta no muta**, y por eso hice **mutantes a mano**: no muta `is` / `is not None`, ni llamadas, ni
el orden de las sentencias, ni literales de texto, ni la lista de excepciones de un `except`. En este bloque hay
decisiones de verdad en todo eso (el orden de construcción, validar antes de construir, la hora en UTC, cada
excepción traducida). Los apliqué **solo en una copia** de `services/postventa-api` en el directorio temporal (sin
`.venv`, `.env` ni `local.settings.json`), uno a uno y restaurando el fichero después, con un script **fuera del
repositorio**; cada uno contra `tests/test_f060_pipeline_normalizacion.py` y/o `tests/test_f060_normalizar_http.py`
con `-x`. El árbol de trabajo no se tocó.

| # | Mutante a mano | Resultado | Primer test que cae |
|---|---|---|---|
| P1 | `not ensayo and plan.revisiones` → `not ensayo` (lote con el plan vacío) | MUERTO | `test_f060_r20_un_plan_vacio_no_llama_al_lote` |
| P2 | → `plan.revisiones` (ignora el ensayo) | MUERTO | `test_f060_r17_justo_en_el_tope_si_se_normaliza` |
| P3 | `normalizadas` y `conflictos` cruzados | MUERTO | `test_f060_r20_la_real_registra_el_lote_del_plan` |
| P4 | `normalizadas = len(plan.revisiones)` (cree al plan, no a la base) | MUERTO | `test_f060_r13_r20_un_conflicto_se_cuenta_y_no_aborta_las_demas` |
| P5 | `total = len(situaciones)` en vez de `contar` | MUERTO | `test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe[True]` |
| P6 | dos lecturas de las ubicaciones | MUERTO | `test_f060_r17_justo_en_el_tope_si_se_normaliza` |
| P7 | tope `> TOPE + 1` | MUERTO | `test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe[True]` |
| P8 | esperadas todas `None` (sin frescura) | MUERTO | `test_f060_r9_r20_la_esperada_es_la_ultima_leida` |
| P9 | `ensayo=False` en el resultado | MUERTO | `test_f060_r19_el_ensayo_no_llama_al_lote_ni_escribe` |
| P10 | `ResultadoNormalizacion` sin `frozen` | MUERTO | `test_f060_el_resultado_es_inmutable` |
| P11 | la hora del plan, la del reloj y no la recibida | MUERTO | `test_f060_r20_la_real_registra_el_lote_del_plan` |
| H1 | admitir claves de más (`>=` en vez de `!=`) | MUERTO | `…_handler_rechaza_cada_cuerpo_malo…[de-mas-oid]` |
| H2 | `is not True` → `not …` (admite `"true"`, `1`) | MUERTO | `…[confirmado-texto]` |
| H3 | `isinstance(ensayo, bool)` → `int` (admite `0`, `1`) | MUERTO | `…[ensayo-uno]` |
| H5 | `datetime.now()` sin zona | MUERTO | `test_f060_r20_sin_hora_inyectada_es_la_de_ahora_en_utc` |
| H6 | ignorar la hora inyectada | MUERTO | `test_f060_r20_la_real_escribe_revisiones_del_sistema_con_la_hora_de_la_peticion` |
| H7 | la base antes que la fuente de ubicaciones | MUERTO | `test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas[True]` |
| H8 | validar **después** de construir el catálogo (RM7) | MUERTO | `…_handler_rechaza_cada_cuerpo_malo…[lista]` |
| H9 | la obra sin `normalizar_codigo_obra` | MUERTO | `…[obra-vacia]` |
| H10 | los segundos sin restar el inicio | MUERTO | `test_f060_r30_los_segundos_son_los_de_la_peticion` |
| H11 | `leer_catalogo(catalogo_obra, cuerpo["obra"])` en vez de la obra normalizada | **VIVO · equivalente** | — |
| H12 | una clave de más en la respuesta con el texto del sistema | MUERTO | `test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento[True]` |
| F1 | sin `CodigoDeObraInvalido` en el 400 | MUERTO | `…_la_ruta_responde_400…[obra-vacia]` |
| F2 | sin `PersistenciaNoDisponible` en el 503 | MUERTO | `…_la_ruta_responde_como_el_listado…[base-caida]` |
| F3 | sin unidades → 409 | MUERTO | `…[sin-unidades]` |
| F4 | la bandeja de más sin el `total` | MUERTO | `…[bandeja-de-mas]` |
| F5 | el cuerpo que no es JSON con otro código | MUERTO | `test_f060_r26_un_cuerpo_que_no_es_json_es_400_sin_construir_nada` |
| F6 | la ruta admite también `GET` | MUERTO | `test_f060_s9_la_ruta_es_post_y_anonima` |
| F7 | el 503 sin el «no se ha escrito nada» | MUERTO | `…[sigrid-caido]` |

**28 de 29 muertos.** El vivo, **H11, es equivalente** y no un hueco: `leer_catalogo` (F-036) aplica ella misma
`normalizar_codigo_obra` a lo que recibe, y `cuerpo["obra"]` ya ha pasado esa misma función en `_peticion`; con
cualquier obra que llegue hasta ahí, las dos versiones piden a Sigrid el mismo código. Severidad: **ninguna**. No
se añade test (no hay comportamiento que lo distinga). Dos mutantes previstos no se ejecutaron: `H4` (`ensayo` con
valor por defecto vía `cuerpo.get`) es inalcanzable, porque el control de las claves exactas va antes y ya lo
rechaza (lo cubren `sin-ensayo` y `solo-obra` de la tabla); y `H13` (meter el cuerpo en el log) no aporta: con las
claves exactas, el cuerpo solo puede llevar la obra y dos booleanos, que ya van en la línea.

**Supervivientes abiertos: ninguno.**

### Ficheros tocados en el Bloque 3

- Producción: `services/postventa-api/application/pipelines/revision.py` (se **añaden** `ResultadoNormalizacion`,
  `normalizar_ubicaciones`, el import del dominio, dos nombres en `__all__` y un apartado del docstring),
  `services/postventa-api/interface_adapters/api/normalizacion.py` (**nuevo**), `services/postventa-api/function_app.py`
  (la ruta, su import, su entrada en la cabecera y el párrafo «veintiuno»).
- Tests nuevos: `tests/test_f060_pipeline_normalizacion.py` (28), `tests/test_f060_normalizar_http.py` (99),
  `tests/utiles_normalizacion.py` (doble).
- Test ampliado sin quitar nada: `tests/test_f010_endpoints_protegidos.py` (la ruta y la cuenta a 21). Es uno de los
  dos que R39 permite ampliar.
- Spec: `tasks.md` (T9–T12 marcadas). Informes: este y `progress/mutacion_F-060_bloque3.md`.
- **No se tocaron**: `interface_adapters/api/revision.py`, `tests/utiles_revision.py`, ningún test de F-036 ni de
  F-056, ningún `.sql`, `docs/INTEGRACION.md` (Bloque 5), `.env`, `services/postventa-front/`, la plantilla ni
  `Ajustes`. Nada escribe en Sigrid: el endpoint solo compone los lectores de F-036 y F-056 (`sql/read`).

### Commits del Bloque 3

| Commit | Qué |
|---|---|
| `0c7d9e9` | F-060 T9: RED (tests, doble con lote, esqueleto neutro, `test_f010` ampliado) |
| `6a4c889` | F-060 T10: GREEN de la aplicación |
| `97a33ff` | F-060 T11: GREEN del handler y la ruta |
| (este commit) | F-060 T12: mutación del bloque e informe |

### Pendiente

Nada del Bloque 3. **Parar: review del Bloque 3.** El Bloque 4 (tras cada importación) no se ha empezado. Sigue
pendiente la **T7** del Bloque 2 (MANUAL, humano).

Para la review:

- `docs/INTEGRACION.md` §8 dice «Los veinte» y el código ya tiene veintiuna rutas: lo cierra T20 (Bloque 5).
- El `obra` de la línea de log y de la respuesta es el código normalizado (`" 99 01 "` → `9901`).
- La línea de log lleva `ensayo=True`/`False` (el `bool` de Python, como `ya_importado` en la importación).

### Evidencias (Bloque 3)

| Evidencia | Valor real |
|---|---|
| RED (T9) | 134 casos: **123 failed** (todos por aserción; 44 de ellos, los de la ruta, por la aserción de que la ruta no existe) y 11 passed (justificados), en 1,73 s |
| Tests del bloque en verde | `test_f060_pipeline_normalizacion.py` **28 passed**; `test_f060_normalizar_http.py` **99 passed**; verificación de T10 **108 passed** en 1,61 s; de T11 **289 passed** en 1,80 s |
| Colindantes | Los 47 ficheros que leen o importan `function_app.py`, más F-056 (pipeline, repositorio), F-060 (dominio, lote), arquitectura, documentación de F-012/F-019/F-053 y `test_f006`: **2229 passed, 29 skipped** en 66,18 s |
| Cobertura de lo cambiado | `interface_adapters/api/normalizacion.py` **42/42 sentencias, 12/12 ramas (100 %)**; `ResultadoNormalizacion` y `normalizar_ubicaciones` (desde la línea 395 de `revision.py`) y `revision_normalizar` (desde la 1761 de `function_app.py`), **sin líneas ni ramas sin cubrir** (`coverage run --branch` sobre los dos tests de F-060). La `PUERTA COBERTURA` de `init.sh` se pasa en T23 |
| Mutación (herramienta) | **17 generados, 17 muertos, 0 supervivientes**, 0 timeouts, **8 workers**, 1801,1 s |
| Mutación (a mano) | **28 de 29 muertos**; el vivo (H11), equivalente y justificado arriba |
| `bash harness/init.sh` | En verde **al empezar** el bloque (7785 passed, 123 skipped, 883,40 s; cobertura 100 % de 110 líneas). No relanzado al terminar: la suite entera es de T23 |
| Suite completa | Solo la de la precondición; no se relanza (T23) |

### C-1 de la review del Bloque 3 · aceptación del humano (2026-10-11)

El humano **acepta por escrito** («si», 2026-10-11) que el mutante a mano **H11**
(`leer_catalogo(catalogo_obra, cuerpo["obra"])` en lugar de la obra ya normalizada, en
`interface_adapters/api/normalizacion.py`) queda vivo por **equivalente**: `leer_catalogo` aplica ella misma
`normalizar_codigo_obra`, que es idempotente, y `cuerpo["obra"]` ya pasó por ella al validar la petición; Sigrid
recibe el mismo código en los dos casos y no hay comportamiento observable que los distinga. Con esto, la review
del Bloque 3 pasa a APPROVED (`progress/review_F-060_bloque3.md`).
