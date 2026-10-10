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

## Bloque 2 · El lote en la base · T4 hecha; **BLOQUEADO antes de T5** · 2026-10-10

Encargo: T4 (RED), T5, T6 y T8; T7 es MANUAL del humano. Rama `feature/F-060-normalizar-ubicaciones`, HEAD de
partida `66c981d` (el hash anterior a T4: el `--base` de la mutación de este bloque).

**Resultado: T4 hecha y en su commit (`e259f23`). T5 no se puede hacer como dice la spec sin romper un test de
F-056 que la propia spec prohíbe tocar. Paro e informo (regla de `tasks.md` y del encargo: «no se relaja»).
T5, T6 y T8, y la sección «Para el humano · T7», quedan sin hacer.**

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

### BLOQUEO antes de T5 · la spec choca con un test de F-056 que no se puede tocar

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

### Lo que queda del bloque (sin hacer)

- **T5** (GREEN: `ResultadoDelLote` inmutable y `registrar_lote` en el puerto y en el repositorio, con las
  sentencias de `sentencias_revision.py` sin cambiar): espera la decisión. El código no depende de ella; solo
  cambia dónde se declara el método.
- **T6** (`tests_bbdd/tests/test_f060_bbdd_lote.py`), **T8** (mutación con `--base 66c981d`) y la sección
  «Para el humano · T7»: van detrás de T5.

### Ficheros tocados en el Bloque 2 (hasta aquí)

- `services/postventa-api/tests/test_f060_repositorio_lote.py` (nuevo).
- `services/postventa-api/domain/ports/revision.py` y
  `services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py`: **solo el esqueleto de RED**,
  marcado como tal en sus docstrings. T5 lo sustituye.
- `specs/F-060-normalizar-ubicaciones/tasks.md`: T4 marcada.
- `harness/features.json` (F-060 pasa a `blocked`), `BACKLOG.md` (regenerado con `harness/backlog.py`),
  `progress/current.md` (nota del bloqueo) y este informe.

### Evidencias (Bloque 2, parciales)

| Evidencia | Valor |
|---|---|
| Tests de T4 en rojo | 27 casos: **24 failed** (todos por aserción) y 3 passed (justificados arriba), en 0,53 s |
| Colindantes de F-056 con el esqueleto | `test_f056_repositorio_revision.py` y `test_f056_ddl.py`: **135 passed** en 0,79 s |
| F-056 con `registrar_lote` en el puerto (experimento revertido) | **1 failed, 356 passed** en 4,78 s: es el bloqueo |
| Cobertura de lo cambiado | Sin medir: este bloque aún no tiene código de producción, solo el esqueleto |
| Mutación del bloque | Sin lanzar: va detrás de T5 |
