<!-- specs/F-065-revision-sigrid-backend/tasks.md -->
# F-065 · Las reclamaciones de Sigrid en la revisión, en el backend — Tareas

> Tramo A de la spec conjunta de F-064 (Q-1, aprobada por el humano el
> 2026-10-21). **Spec aprobada por el humano el 2026-10-21**: Q-1 a Q-10 y
> N-1 a N-3 (`design.md` §14). T-A0 puede mover el umbral de N-2, la columna de
> fecha o activar la lectura por trozos de N-1: si lo hace, se enmienda la spec
> antes del Bloque A2.
>
> Rama `feature/F-065-revision-sigrid-backend` desde `dev`, base fija anotada
> en `progress/impl_F-065.md` (la usan la guarda de alcance y la mutación).
> Cada bloque es **un encargo** al implementer y termina en **«Parar.
> Review»**. Cada tarea es un commit `F-065 Tn: …`; los tests,
> `test_f065_rN_…`. El implementer **no** ejecuta `bash harness/init.sh`
> (P-4): lo hace el líder al final de cada bloque. Nada se ejecuta contra
> Sigrid ni contra la base desde un puesto de trabajo salvo las tareas
> `MANUAL (humano)`, que son **solo lectura**.
>
> **Datos de prueba** (R39): solo inventados —«Ejemplo …», correos
> `@ejemplo.invalid`, teléfonos `000 000 000`—. Nada copiado de Sigrid.
>
> **Conciliado el 2026-10-28 con `dev` `f7f63da`.** La rama sale de ahí
> (commit `6eb23fa`); la base fija la anota el implementer al empezar. Lo
> **nuevo** —la guarda del ensayo, R41–R49 y R70–R71— añade **T2 bis** y
> **T-A0 bis** al Bloque A1, el **Bloque A4 bis** (T13–T17), una línea a T10
> y **T-A17–T-A18** al Bloque A7. **Esas tareas esperan al OK del humano a
> S-1–S-9** (`design.md` §16); las demás se pueden empezar ya. Las
> numeraciones nuevas no siguen el orden de ejecución: el orden es el de los
> bloques, y **T12** (`init.sh`) sigue siendo la última.

## Bloque A1 · El script de medición, y medir antes del dominio

- [x] **T1**: tests RED de `infra/29_reclamaciones_obra_sigrid.ps1`
  (`tests/test_f065_scripts_infra.py`): existe; ASCII sin BOM y CRLF; carga
  `08_lectura_sigrid_comun.ps1`; solo `Invoke-SigridLectura` (ni `sql/write`,
  ni `partes-reclamacion`, ni `concepto-grafico`); todos los valores por `?`;
  ningún valor de pasarela, base, clave ni obra en el texto; ningún
  `Write-Host` de una columna de texto (`cod`, `res`, `resubi`, `valt`, `tex`,
  `nom`, `tel`, `ele`…) ni de una fila: solo recuentos, bytes y segundos
  (R29); la consulta no nombra `dni`, `esiglog`, `esigpas`, `clamai` ni
  direcciones. | Verificación: `python -m pytest tests/test_f065_scripts_infra.py` (desde `services/postventa-api`) en **rojo**, traza en `progress/impl_F-065.md`
- [x] **T2**: el script (R29), con el SQL de `design.md` §3 en un
  here-string; `-CodigoObra` (con y sin ceros, como el 28) y `-MaxFilas 500000`;
  los recuentos de R29, con el parecido de §5.3 aproximado en PowerShell (dicho
  en la ayuda); los bytes de la respuesta con todos los campos y los de R33
  aparte, `truncated` y los segundos; y si la pasarela aceptó la consulta. | Verificación: `python -m pytest tests/test_f065_scripts_infra.py` en verde
- [x] **T2 bis** *(nuevo, 2026-10-28; espera a S-5)*: `-Unidades` en el script
  29 (R70): con ella lanza la consulta de la guarda de `design.md` §15.5 (las
  12 columnas de R6, sin R33, con `u.cod IN (?, …)`), un marcador por unidad;
  imprime filas, `truncated`, bytes y segundos, y **cuántas** unidades (no
  cuáles). Tests en `tests/test_f065_scripts_infra.py`, primero en rojo: las
  reglas de T1 también en esta rama del script, y que el texto para 1 y para 5
  unidades es **idéntico** al de `select_reclamaciones_de_las_unidades` (que
  aún no existe: el test compara contra el texto de §15.5 escrito en el test, y
  T15 lo cambia a comparar con la función). | Verificación: `python -m pytest tests/test_f065_scripts_infra.py` en rojo y después en verde, traza en el informe

**Parar. Review del Bloque A1.**

- [x] **T-A0 · MANUAL (humano)**, solo lectura, **antes del Bloque A2**:
  ```
  powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
  powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0626 -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
  ```
  Anotar en `progress/impl_F-065.md` **solo recuentos, bytes y segundos**:
  filas y `truncated`, **bytes de la respuesta de la 0677 con todos los campos
  de R33** (y cuántos son de R33), segundos, si la pasarela aceptó el
  `OUTER APPLY`, la población por estado y antigüedad, por unidad, cuántas
  traen cada campo de R33, el ruido de R14 y los pares con parecido 40/50/60, y
  `con.fec` frente a `rcp.fec`. Con eso el líder lleva al humano si hace falta
  leer por trozos (N-1: más de ≈ 10 s), si el umbral 50 se queda (N-2) y la
  columna de fecha; si alguno cambia, se enmienda la spec **antes** del Bloque
  A2. |
  Verificación: MANUAL (humano)
- [x] **T-A0 bis · MANUAL (humano)** *(nuevo, 2026-10-28; espera a S-5)*,
  solo lectura, junto con T-A0 y **antes del Bloque A4 bis** (R71): el coste
  de la guarda.
  ```
  powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -Unidades 'VILLA 15' -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
  powershell -ExecutionPolicy Bypass -File infra\29_reclamaciones_obra_sigrid.ps1 -CodigoObra 0677 -Unidades '<u1>','<u2>','<u3>','<u4>','<u5>' -SigridBaseUrl <raíz de la pasarela> -SigridBaseDatos ruesma
  ```
  (cinco unidades cualesquiera de la 0677, las que el humano elija). Anotar
  en `progress/impl_F-065.md` **solo** filas, `truncated`, bytes y segundos de
  cada una, junto a los de la obra entera de T-A0, y repetir cada comando
  tres veces (los picos de F-061). Si la obra pasa de ≈ 10 s o la guarda de
  ≈ 3 s, el líder vuelve al humano antes del Bloque A4 bis (S-5: obra entera
  o por unidades). |
  Verificación: MANUAL (humano)

## Bloque A2 · El dominio puro

- [x] **T3**: tests RED de `domain/models/sigrid_bandeja.py`
  (`tests/test_f065_dominio.py`): R10 (UUID con y sin mayúsculas, `PVI-` sin
  UUID, de otra obra), R11, R12 (los tres avisos), R13, R13 bis, R14 (cada lado
  sin oficio, ubicación vacía, `COCINA`/`Cocina`, `Cocina 1`), R15 (umbral
  justo, 49 y 50, una sola palabra en común con parecido alto, descripción
  vacía o solo de palabras vacías), R16 (las seis situaciones), R17 (las
  severidades, sin corte de fecha, un estado desconocido contado), R18 (tope
  10, orden y total), R21, R36 (tildes, mayúsculas, puntuación, plural, palabras
  vacías, menos de 3 letras, cifras) y los ejemplos E1–E13 de `design.md` §5.4
  tal cual; y que el cruce es por unidad (una obra de 50.000 reclamaciones y
  10.000 incidencias se cruza en un tiempo acotado). Sin red, sin base, sin
  reloj. | Verificación: `python -m pytest tests/test_f065_dominio.py` en **rojo**, traza en el informe
- [x] **T4**: `domain/models/sigrid_bandeja.py` (`design.md` §10.1), sin tocar
  `revision.py`, `normalizacion.py`, `plantilla_incidencias.py` ni
  `volcado.py`. | Verificación: `python -m pytest tests/test_f065_dominio.py` en verde
- [x] **T4 bis** *(nuevo, 2026-10-28: la corrección del Bloque A2 tras su
  review, con las decisiones del humano sobre las lecturas 1–4 y 9 y los
  cambios C-A2-1 y C-A2-2 de `progress/review_F-065.md`)*. Primero los tests
  en `tests/test_f065_dominio.py`, en **rojo** contra el dominio de T4 (traza
  en el informe), y después `domain/models/sigrid_bandeja.py`. Lo que cambia:
  1. **`guardado_cod`** (R12, R20, `design.md` §10.1, tabla «Los códigos de
     cada hallazgo»): `Hallazgo` gana `guardado_cod: str | None = None`. En
     `volcada_no_encontrada`, `sigrid_cod=None` y el guardado en
     `guardado_cod`; en `codigo_distinto`, la emparejada en `sigrid_cod`, el
     guardado en `guardado_cod` y `sigrid_cods=()`. La docstring de `Hallazgo`,
     con la tabla. Tests: cada tipo con sus tres campos según la tabla, y las
     invariantes (`sigrid_cod` no nulo siempre está en `Cruce.reclamaciones`;
     `sigrid_cods` solo no vacío en `varias_en_sigrid`; `guardado_cod` solo en
     los dos tipos), sobre un juego que dé los siete tipos.
  2. **`codigo_distinto` con varias** (R12): no se da si el guardado está entre
     las emparejadas. `test_f065_r13_bis_varias_de_una_volcada_y_el_codigo_contra_la_mayor`
     cambia con la decisión: `volcada` guardada como `0081`, `PVI-` en `0081`
     y `0082` → `varias_en_sigrid` y **ningún** `codigo_distinto`; y uno
     nuevo: guardada como `0080`, `PVI-` en `0081` y `0082` →
     `varias_en_sigrid` y `codigo_distinto` con `sigrid_cod` `0082` y
     `guardado_cod` `0080`. (Códigos ficticios de §5.4.)
  3. **`anulada_en_sigrid` solo contra la mayor** (R12; **C-A2-1**): una
     `volcada` guardada como la mayor, dos `PVI-` suyas y la **menor** en
     `NPR` → `varias_en_sigrid` y **ningún** `anulada_en_sigrid`; el caso
     simétrico (la mayor en `NPR`) → `anulada_en_sigrid` sobre la mayor. Debe
     matar M12 de la review (`if mayor.estado == EstadoSigrid.NPR:` →
     `if any(r.estado == EstadoSigrid.NPR for r in suyas):`): la traza del
     mutante muerto, en el informe.
  4. **R13 con varias** (lectura 3, ya implementada así en T4): comprobar que
     un test fija que **ninguna** de las que llevan la referencia de la
     incidencia da `coincide` con ella (también la menor) y que **sí** lo dan
     frente a otra incidencia; si el de T4 no fija las dos cosas, se completa.
     Su nombre o docstring cita la enmienda de R13.
  5. **El orden de los `coincide`** (R21, lectura 9; `design.md` §10.1, «El
     orden de `Cruce.hallazgos`»): a igual severidad, tipo e `incidencia_id`,
     los `coincide` en el orden de R18 (fecha descendente, sin fecha al final,
     código descendente), no por código ascendente; los demás tipos, por
     `sigrid_cod` ascendente (`None` delante). Tests: una incidencia con
     `coincide` de conflicto y de aviso cuyas fechas **no** siguen el orden de
     sus códigos (el de código menor, el más reciente), uno sin fecha y dos de
     la misma fecha, y que filtrar `hallazgos` por `incidencia_id` y `coincide` da
     exactamente el orden de R18 y los mismos 10 que elige el tope;
     `test_f065_r21_…` se adapta a la decisión.
  6. **La enmienda a S-3** (lectura 4) **no** toca el dominio de este bloque:
     es del veredicto (R41), que nace en T13/T14 (Bloque A4 bis). Aquí nada.
  7. **C-A2-2**: con todo lo anterior confirmado y `git status` limpio **antes
     de empezar**, regenerar `progress/mutacion_F-065_bloqueA2.md` (con la
     suite reducida a `tests/test_f065_dominio.py` y su nota, que la review
     acepta) sobre ese commit, para que el alcance y el commit que declara el
     informe sean los que se midieron. Cero supervivientes (`critico`), también
     a mano: repetir M1–M18 de la review que sigan aplicando, más uno por cada
     cambio de 1, 2 y 5 (quitar `guardado_cod`, volver a dar `codigo_distinto`
     con el guardado entre las suyas, volver al orden por código).
  | Verificación: `python -m pytest tests/test_f065_dominio.py` en **rojo** y
  después en verde (trazas en `progress/impl_F-065.md`); `ruff check` del
  módulo y del test; `progress/mutacion_F-065_bloqueA2.md` regenerado desde un
  árbol confirmado, con 0 supervivientes; la tabla de mutantes a mano en el
  informe

**Parar. Review del Bloque A2** (otra vez, sobre T4 bis).

## Bloque A3 · Las consultas y el adaptador

- [x] **T5**: tests RED (`tests/test_f065_consulta.py`,
  `tests/test_f065_adaptador.py`): el SQL carácter a carácter e **idéntico** al
  del script 29; los parámetros en orden; las columnas de R6 y la lista cerrada
  de R33, y ninguna prohibida (`dni`, `esiglog`, `esigpas`, `clamai`,
  direcciones, `per.tex`);
  el mapeo (columnas exactas, `obra_ref` y `cod` obligatorios, `YYYYMMDD` a
  fecha, `0` a nulo, un entero imposible a error **sin la fila**);
  *(enmienda del 2026-10-28, decisión del líder sobre la lectura 6 de la review
  del Bloque A2; `design.md` §10.2)* el mapeo **recorta** `estado_codigo`,
  `cod`, `tipo_codigo` y `clase_codigo`: con su test, `'SAT     '` y `' PTE'`
  quedan en la fila como `SAT` y `PTE`, un `cod` rellenado
  (`'RS26.09/0123  '`) queda sin blancos, un código de solo blancos es `None`
  y un `cod` de solo blancos es error sin la fila; **`unidad_codigo` y `oficio_codigo`
  tal cual, sin recortar**, como el catálogo de F-036 (decisión del líder del
  2026-10-28, opción (a) de `progress/spec_F-065.md`), con un test que lo fije; las filas
  sin valores en su `repr` (R40); el adaptador: puerta de entorno sin abrir
  conexión (R2), `max_rows` 500.000, y 409 con `truncated` **o** al techo, 503
  con una respuesta mal formada (R8), reintento de lo transitorio, solo `/api/sql/read` (R27), y
  el log con obra, filas, techo y segundos y **nada más** (R25, R38). La
  fábrica, con sus dos puertas en orden. | Verificación: `python -m pytest tests/test_f065_consulta.py tests/test_f065_adaptador.py` en **rojo**, traza en el informe
- [x] **T6**: `domain/ports/reclamaciones_obra.py`,
  `infrastructure/sigrid/consultas_reclamaciones_obra.py`,
  `infrastructure/sigrid/reclamaciones_obra.py` (hereda
  `AdaptadorCatalogoSigridApi` **sin tocarlo**, `design.md` §2) y
  `construir_reclamaciones_obra` en `fabrica.py`. | Verificación: los dos ficheros de T5 en verde y `python -m pytest tests/test_f036_adaptador_catalogo.py tests/test_f056_ubicaciones.py` sin cambios

**Parar. Review del Bloque A3.**

## Bloque A4 · La aplicación, el borde y las rutas

- [x] **T7**: tests RED (`tests/test_f065_aplicacion.py`,
  `tests/test_f065_http.py`, `tests/test_f065_datos_personales.py`): en el
  listado, el orden de lecturas, **una** de la base y **como mucho una** de
  Sigrid (R3), 409 por la bandeja sin leer Sigrid (R4), 409 al techo sin
  cruzar (R8), 409 `obra_ambigua` y 200 vacío (R9), 400 sin construir nada
  (R1), Sigrid antes que la base (R2), la forma de R20 (con `guardado_cod`,
  `null` donde no toca; *enmienda del 2026-10-28*) y el orden de R21, nada
  de `oid`, correo, `ide` ni `obride` (R22), la traducción de R23 y la línea
  `F-065 sigrid de la bandeja` sin textos ni códigos y con los bytes (R24;
  *conciliado el 2026-10-28*: con `aplicacion` y `calculo`, y que pedir esta
  ruta **no** cambia el `proceso_nuevo` de la siguiente línea de F-060);
  `Cache-Control: no-store` en esta y en ninguna otra ruta (R35); que con
  fichas inventadas en el doble (R33), **ningún** registro de log de la ruta ni
  del adaptador contiene ninguno de sus valores, tampoco con error (R38); que nada se escribe en la base (R37: el doble de `RevisionPort` no
  recibe ninguna escritura); que los ficheros de tests, `specs/` y `progress/`
  de F-065 solo traen correos `@ejemplo.invalid` (R39); y que el listado, el
  historial, las acciones, la normalización y el volcado responden y registran
  igual (R26: sus tests sin tocar). | Verificación: `python -m pytest tests/test_f065_aplicacion.py tests/test_f065_http.py tests/test_f065_datos_personales.py` en **rojo**, traza en el informe
- [x] **T8**: `application/pipelines/sigrid_bandeja.py`,
  `interface_adapters/api/sigrid_bandeja.py`, `ReclamacionesSinVerificar` en
  `errores.py`, la ruta y `_json_sin_cache` en `function_app.py` (con su
  párrafo de cabecera). | Verificación: los tres ficheros de T7 en verde y `python -m pytest` del servicio entero en verde
- [x] **T9**: la guarda de alcance (`tests/test_f065_alcance_cerrado.py`, base
  fija del tramo, como las de F-056/F-059/F-060): solo cambian los ficheros de
  `design.md` §9.1–9.2; lo de §9.3 intacto; ninguna variable, DDL ni
  dependencia nueva; ninguna pieza nueva nombra otra ruta de la pasarela que
  `sql/read` ni importa las escrituras (R26–R28); con su control no ciego. |
  Verificación: `python -m pytest tests/test_f065_alcance_cerrado.py` en verde

**Parar. Review del Bloque A4.**

## Bloque A4 bis · Sincronizar antes de registrar: la guarda del ensayo (nuevo, 2026-10-28)

> **Espera al OK del humano a S-1–S-9** (`design.md` §16) y a T-A0 bis. Toca
> piezas de F-059: los tests de F-059 se ejecutan **sin cambiar ninguna
> aserción** en cada tarea.

- [ ] **T13**: tests RED del veredicto (`tests/test_f065_veredicto.py`): la
  precedencia de R41 con los ejemplos de `design.md` §15.2 (E1 → `choca`, E1
  con la descripción de E2b → `ya_existe`, E3/E4 → `va`, E7 → `se_enlaza`,
  E12 sin veredicto; *enmienda del humano a S-3, 2026-10-28*: E7 con la
  emparejada en `NPR` → `choca` con solo su código, también con un
  `ya_existe` por criterios, y con la menor de dos en `NPR` → `se_enlaza`;
  `design.md` §15.2, regla 0); que mira **todos** los pares y no los 10 de R18 (una
  incidencia con 12 conflictos da los 12 códigos); los códigos en el orden de
  R18; solo candidatas; el bloque `volcado` de R42 con su `por_unidad`; y R49:
  para un juego de fixtures, el veredicto con todas las reclamaciones de la
  obra es igual al de solo las de sus unidades, con el caso escrito de un
  `PVI-` en otra unidad. | Verificación: `python -m pytest tests/test_f065_veredicto.py` en **rojo**, traza en el informe
- [ ] **T14**: `Veredicto`, `VeredictoDeVolcado`, `ParDeCoincidencia`,
  `Cruce.pares` y `veredictos` en `domain/models/sigrid_bandeja.py`, y el
  bloque `volcado` en el pipeline y el borde de la ruta (R41, R42). | Verificación: `python -m pytest tests/test_f065_veredicto.py tests/test_f065_dominio.py tests/test_f065_http.py` en verde
- [ ] **T15**: tests RED de la guarda (`tests/test_f065_guarda_ensayo.py` y
  `tests/test_f065_consulta.py`): la consulta por unidades carácter a carácter
  (de 1 a `N` marcadores, sin R33, idéntica a la del script 29: T2 bis pasa a
  compararla con la función); el cuerpo de R43 (sin la clave, con lista vacía,
  con un `incidencia_id` que no está en `incidencias`, repetido, sin
  `sigrid_cods`, con un código mal formado o repetido, con 51 códigos, con una
  clave de más; y que `confirmado` y `commit` siguen siendo 400), todo 400
  **sin construir nada**; el orden de R44 (selección → Sigrid → login → lote,
  y **sin** Sigrid si la selección no deja nada); las exclusiones de R45 (las
  dos, la confirmación parcial, la que apareció después, la sobrante, y la
  `choca` por una emparejada en `NPR`: sin confirmar, excluida con ese código;
  confirmada, se manda); los
  errores de R46 **sin login, sin lote y sin ensayo guardado**; el bloque
  `sigrid` de R47 y que las claves de R12 de F-059 no cambian; la línea de R48
  sin códigos `RS` ni textos; y que un ensayo sin la clave nueva y sin nada que
  choque responde lo mismo que hoy más `sigrid` (R49). Con dobles: sin red,
  sin base. | Verificación: `python -m pytest tests/test_f065_guarda_ensayo.py tests/test_f065_consulta.py` en **rojo**, traza en el informe
- [ ] **T16**: la guarda: `select_reclamaciones_de_las_unidades` y
  `leer(…, unidades=)` (con `unidades=<cuántas>` en el log de R25),
  `application/pipelines/guarda_sigrid.py`, los dos valores de
  `MotivoExclusion`, `ensayar` y `PeticionDeEnsayo`, el borde del ensayo y las
  tres entradas de `function_app.py` (`design.md` §15.6); y el doble vacío del
  lector en `tests/test_f059_volcado_http.py` y
  `tests/test_f059_pipeline_volcado.py`. | Verificación: los ficheros de T15 en verde y `python -m pytest tests/test_f059_volcado_http.py tests/test_f059_pipeline_volcado.py tests/test_f059_volcado_dominio.py tests/test_f059_alcance_cerrado.py` en verde, con el diff de esos dos ficheros de tests limitado al doble (traza en el informe)
- [ ] **T17**: la guarda de alcance de T9 ampliada a §15.6: los ficheros de
  F-059 que cambian, **solo** en las piezas declaradas; en los dos tests de
  F-059, ninguna aserción menos ni cambiada; `infrastructure/sigrid/volcado.py`,
  la persistencia del volcado, `volcar` y `panel_de_volcado` intactos; sin
  DDL ni variables. | Verificación: `python -m pytest tests/test_f065_alcance_cerrado.py` en verde

**Parar. Review del Bloque A4 bis.**

## Bloque A5 · Los documentos

- [ ] **T10**: tests (`tests/test_f065_documentacion.py`) y los documentos de
  R30: `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`,
  `azure-apps/postventa_incidencias.md` y la fila de consumidores de
  `azure-apps/sigrid_api.md` (los de `azure-apps/` con su propio commit local
  en ese repositorio). Que dicen que hay datos personales, dónde se enseñan y
  dónde no van. *(2026-10-28, si S-1:)* y la guarda: en la sección de F-059 de
  `ARCHITECTURE.md`, en `INTEGRACION.md` §1 y en
  `azure-apps/postventa_incidencias.md`, que el ensayo lee Sigrid una vez más
  (solo `sql/read`, por unidades, sin datos personales), los dos motivos
  nuevos y que Sigrid caída = no se ensaya. | Verificación: `python -m pytest tests/test_f065_documentacion.py` en verde

**Parar. Review del Bloque A5.**

## Bloque A6 · Mutación y verde

- [ ] **T11**: la campaña de mutación, cada superviviente con su test o su
  justificación (`critico`: cero sin la aceptación escrita del humano), y
  «Evidencias» con los cuatro números y los workers. |
  Verificación: `python -m harness.mutacion --feature F-065 --base <base fija>` → `progress/mutacion_F-065.md`
- [ ] **T12**: ejecutar `bash harness/init.sh` en verde (**el líder**, P-4). |
  Verificación: `bash harness/init.sh`

**Parar. Review final de F-065.**

## Bloque A7 · Publicar y verificar en producción (MANUAL, humano; solo lectura)

- [ ] **T-A11 · MANUAL (humano)**: merge normal a `dev` desde un worktree
  aparte (el líder) y publicar el backend desde un worktree limpio de `dev`,
  con los mismos parámetros que el último despliegue:
  ```
  git worktree add --detach ..\postventa-publicar dev
  powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
  git worktree remove ..\postventa-publicar
  ```
  Sin DDL. Anotar el commit publicado. **Vuelta atrás**: publicar el anterior
  con el mismo mecanismo; es segura (las rutas solo leen y no dejan nada). |
  Verificación: MANUAL (humano)
- [ ] **T-A12 · MANUAL (humano)**, **antes**: el script 29 para la 0677 y la
  0626 (los dos primeros comandos de T-A0); y en la consola del navegador (F12)
  en una pestaña del front publicado:
  `fetch('/api/revision?obra=0677').then(r => r.json()).then(d => console.log(JSON.stringify(d.resumen)))`.
  Solo recuentos. | Verificación: MANUAL (humano)
- [ ] **T-A13 · MANUAL (humano)**, el listado, en la misma consola:
  ```
  fetch('/api/revision/sigrid?obra=0677').then(r => r.json()).then(d => console.log(JSON.stringify(d.resumen)))
  fetch('/api/revision/sigrid?obra=0626').then(r => r.json()).then(d => console.log(JSON.stringify({resumen: d.resumen, emparejadas: d.reclamaciones.filter(x => x.incidencia_id).map(x => x.cod), hallazgos: d.hallazgos.map(h => [h.tipo, h.severidad, h.sigrid_cod])})))
  ```
  Pasa si `reclamaciones` y `por_estado` cuadran con T-A12 (salvo actividad de
  Posventa, anotada por estado); en la 0626, `RS26.10/0074` sale emparejada y
  sin `volcada_no_encontrada`, y `RS26.09/0439` con `referencia_desconocida`.
  Anotar solo recuentos y códigos `RS`. | Verificación: MANUAL (humano)
- [ ] **T-A14 · MANUAL (humano)**, la cabecera, los datos y los errores, sin
  copiar ningún valor a las notas:
  ```
  fetch('/api/revision/sigrid?obra=0626').then(r => { console.log(r.status, r.headers.get('cache-control')); return r.json(); }).then(d => console.log(JSON.stringify(Object.keys(d.reclamaciones[0].ficha).map(k => [k, d.reclamaciones.filter(x => x.ficha[k] !== null).length]))))
  fetch('/api/revision/sigrid?obra=%25%25').then(r => console.log(r.status))
  ```
  Pasa con `200 no-store`, la lista de **nombres** de campo de R33 con cuántas
  reclamaciones lo traen (sin ningún valor), y `400`. | Verificación: MANUAL (humano)
- [ ] **T-A15 · MANUAL (humano)**, tiempos y logs: diez cargas de la 0677; en Application Insights (Logs):
  ```
  traces
  | where timestamp > ago(1h)
  | where message startswith "F-065" or message startswith "F-060 tiempos del listado"
  | project timestamp, message
  | order by timestamp desc
  ```
  Anotar p50 y máximo de la ruta, de `sigrid.leer` y los bytes, y comprobar que
  **ninguna** línea lleva un texto, un nombre, un teléfono, un correo, una
  referencia, un código `RS` ni un `oid`. | Verificación: MANUAL (humano)
- [ ] **T-A16 · MANUAL (humano)**, **después**: repetir T-A12; mismos
  recuentos salvo la actividad de Posventa. | Verificación: MANUAL (humano)
- [ ] **T-A17 · MANUAL (humano)** *(nuevo, 2026-10-28; si S-1)*, solo lectura,
  el bloque de la sincronización, en la consola del front publicado:
  ```
  fetch('/api/revision/sigrid?obra=0677').then(r => r.json()).then(d => console.log(JSON.stringify({candidatas: d.volcado.candidatas, por_veredicto: d.volcado.por_veredicto, por_unidad: d.volcado.por_unidad})))
  ```
  Pasa si `candidatas` cuadra con `aprobadas + en_duda` del panel de F-059
  (`GET /api/volcado?obra=0677`) y la suma de `por_unidad` con
  `por_veredicto`. Anotar solo recuentos. | Verificación: MANUAL (humano)
- [ ] **T-A18 · MANUAL (humano)** *(nuevo, 2026-10-28; si S-1, y solo con la
  autorización expresa del humano para esa acción)*: **un** ensayo
  (`commit: false`: no escribe en Sigrid, sí guarda sus eventos de ensayo en
  nuestra base, como cualquier ensayo de F-059) en la 0626 de una incidencia
  que la sincronización da `choca`, primero **sin** confirmarla (sale en
  `excluidas` con `conflicto_sin_confirmar`, `ensayo_id: null`) y después
  confirmándola (sale `previsto`). Y en Application Insights, la línea
  `F-065 guarda del ensayo` y la duración del ensayo (R48, R71), sin ningún
  código `RS` ni texto. Anotar solo motivos, estados, recuentos y segundos. | Verificación: MANUAL (humano)
