<!-- progress/review_F-065.md -->
# F-065 · Revisión con Sigrid en el backend — Informe del reviewer

## Review del Bloque A1 (T1, T2, T2 bis) · 2026-10-28

- **Veredicto:** **CHANGES_REQUESTED** (RECHAZADO), por **un** hallazgo: C-A1-1.
- **Alcance revisado:** `git diff b863b46..f4a9195` (T1 `e57a60c`, T2 `fe78ca8`, T2 bis `63d1daa`, `062025c`,
  `aa693fb`, `2616857`; casillas `e119e9f`; informe `f4a9195`). Solo `infra/29_reclamaciones_obra_sigrid.ps1` y
  `services/postventa-api/tests/test_f065_scripts_infra.py`, contra R29, R70, `design.md` §3 y §15.5,
  `docs/CONVENTIONS.md` y `CHECKPOINTS.md`. Nada del Bloque A2 ni posterior.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED con traza pegada,
  cobertura ≥ 80 % de lo cambiado (o N/A con motivo impreso), campaña de mutación con **cero supervivientes**
  salvo justificación escrita aceptada por el humano (también los mutantes a mano), la sección «Evidencias» y las
  verificaciones `MANUAL (humano)` con su comando exacto.

El bloque está muy bien hecho. Las tres cosas que pidió el líder están en orden: el script es **solo lectura**
(solo `Invoke-SigridLectura` del `08`, que solo llama a `POST /api/sql/read`); **ningún valor de una fila sale por
la consola** (lo he intentado sacar por seis caminos distintos y los tests los han cazado todos); y **no lleva
ningún secreto, host, ID ni IP**. El único hallazgo es un hueco de los tests: en `critico`, un mutante a mano que
sobrevive pide un test o una justificación que acepte el humano, y yo no puedo aceptarla.

### Qué he verificado yo, y cómo

No me he conectado a Sigrid, a la base ni a SharePoint. Las mutaciones y la RED las he hecho en dos copias
desechables del scratchpad (`infra/` y `services/postventa-api/` sin `.venv`), nunca en el árbol de trabajo. Al
terminar, `git status` limpio.

| Verificación | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual, en el worktree | **exit 0, `ENTORNO LISTO`**. Raíz: 115 passed. Servicios api y front: `caché: árbol sin cambios desde el último verde` (el verde de la 2.ª ejecución del implementer sobre `2616857`; el árbol no ha cambiado desde entonces). `PUERTA COBERTURA: N/A (F-065 no cambia líneas Python de producción frente a dev)`. Ruff: 76 avisos, deuda previa |
| Tests del bloque y los barridos de `infra/` (`test_f065_scripts_infra.py`, `test_f010_prompt_keys_infra.py`, `test_f036_scripts_infra.py`, `test_f059_scripts_infra.py`, `test_f010_scripts_infra.py`), ejecutados por mí porque `init.sh` tiró de caché | **304 passed, 3 skipped in 58.65s**. Los 41 de F-065, todos en verde (los 7 que lanzan PowerShell contra el lector doble, incluidos) |
| RED de T1 reproducida: el test de `e57a60c`, sin el script | **23 failed, 3 passed**, lo mismo que la traza pegada (los 3 que pasan son los controles no ciegos y el del `08`) |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature("F-065", base="b863b46")`, y también con `base="dev"`) | **0 ficheros, 0 líneas**. Coincide con el informe |
| Recálculo puro de los mutantes (`generar_mutantes` sobre el alcance) | **0**. Coincide |
| Prueba de control del cero: `generar_mutantes` sobre los `.py` del diff **sin** la exclusión de alcance | **210** mutantes en `test_f065_scripts_infra.py`: el generador funciona y el cero es por diseño (un `.ps1` no es Python y un test no es producción, `harness/alcance.py` l. 134) |
| Campaña reejecutada (el informe declara 0.0 s, < 5 min): `python -m harness.mutacion --feature F-065 --base b863b46 --salida <scratchpad>` | **0 mutantes, 0 muertos, 0 supervivientes, 0 timeouts**, igual que `progress/mutacion_F-065_bloqueA1.md`. El coste por mutante no se puede calcular (0 mutantes), y no hay nada que sospechar en ello |
| Que `-Unidades '<u1>','<u2>'` con `powershell -File` llega como un solo texto con comas (decisión 12 del informe) | Comprobado lanzándolo desde PowerShell con un guion de prueba: `n=1`, `[VILLA 15,B 2,C 3]`. El `-split ","` del script es necesario y correcto |
| Mutantes a mano míos (12), solo con los tests de F-065 | **10 muertos, 2 supervivientes** (C-A1-1). Detalle abajo |
| Barrido de datos sensibles en el script y en el test | Ver «Datos sensibles» |

### Mutantes a mano del reviewer

Aplicados uno a uno en la copia desechable, con `pytest tests/test_f065_scripts_infra.py` **entero y sin `-x`**
(para ver qué test caza cada uno). Todos los tests que caen son **de la propia feature**: no hay ninguna suite
vecina implicada. Elegidos para atacar las tres cosas que pidió el líder por caminos que el implementer no probó.

| Id | Mutación | Resultado | Lo caza |
|---|---|---|---|
| R01 | `Anotar -Que "truncated" -Valor $filas[0][10]` (la descripción) | muerto | estáticos de impresión y de truncado; ejecutado (consola y cuentas) |
| R02 | `Comprobar … -Obtenido ([string]$filas[0][23])` (un nombre) | muerto | estáticos; ejecutado (consola, cuentas y guarda) |
| R03 | `$ESTADOS_CONOCIDOS` reasignada **desde los datos** tras leer | muerto | solo los **ejecutados** (`no_saca_ningun_valor`, `cuenta_lo_que_pide_r29`) |
| R04 | los `Nombre` de `$CAMPOS_R33` reescritos con la primera fila | muerto | solo los ejecutados |
| R05 | `$modo` (variable permitida) rellenada con un nombre y luego `Write-Host $modo` | muerto | solo `ejecutado_no_saca_ningun_valor_de_las_filas` |
| R06 | la guarda imprime **cuáles** unidades (`-join ","`) | muerto | estáticos (`imprime_cuantas_unidades_y_no_cuales`, impresión) y ejecutados |
| R07 | un `UPDATE` en una cadena normal (no here-string) mandado por `Invoke-SigridLectura` | muerto | solo `ejecutado_manda_a_la_pasarela_el_texto_de_design` (cuatro llamadas en vez de tres) |
| R08 | la validación de `-MaxFilas` (1..500.000) movida **después** de la lectura de la obra | **superviviente** | ninguno (41 passed) |
| R09 | el tope de 50 unidades movido **después** de la lectura | **superviviente** | ninguno (41 passed) |
| R10 | un host `*.azurewebsites.net` escrito en el fichero | muerto | `ningun_valor_en_el_fichero` |
| R11 | la guarda lee `r.tel` (un dato de R33) | muerto | los dos estáticos de §15.5 y el ejecutado de la guarda |
| R12 | Q0 sin su `-MaxFilas 10` | muerto | `ejecutado_manda_a_la_pasarela_el_texto_de_design` |

Lectura: los tests **leyendo** el script son buenos, pero la defensa de verdad contra una fuga son los siete
**ejecutados** contra el lector doble (R03, R04, R05 y R07 solo los cazan ellos). Esos siete se saltan si el
puesto no tiene PowerShell; en los puestos de este proyecto (Windows) siempre lo hay, así que no lo pido como
cambio, pero queda dicho (O-1).

### Datos sensibles

Barrido mío sobre `infra/29_reclamaciones_obra_sigrid.ps1` y `test_f065_scripts_infra.py`, con
`azurewebsites|postgres|huyke|rs9k2|ruesma|IPv4|GUID (8-4)|password|secret|x-functions-key|correo`:

- **El script: cero coincidencias.** Ni raíz de la pasarela, ni base, ni clave, ni código de obra (la obra entra
  por `-CodigoObra`; la raíz y la base, por parámetro o por `$env:`; la clave, de `$env:SIGRID_API_KEY` o pedida
  como `SecureString` por el `08`). Además lo fija `test_f065_r29_ningun_valor_en_el_fichero` con su control no
  ciego, y lo confirma R10.
- **El test:** solo los propios patrones de detección (compuestos a trozos), la palabra «Ruesma» en un comentario
  (el nombre de la empresa, no un secreto) y datos inventados de R39 (`Ejemplo …`, `@ejemplo.invalid`,
  `000 000 000`, raíz `http://pasarela.ejemplo.invalid`, que no resuelve).
- `git log --diff-filter=A b863b46..HEAD`: solo entran el script, el test y dos informes de `progress/`. Ningún
  PDF ni parte escaneado.

### Lo que no sale por la consola (atención especial del líder)

Repasado a mano, línea a línea, además de los mutantes:

- Toda cifra medida pasa por `Anotar-Cifra` (l. 302–318), que valida con `TryParse` y, si no es cifra, para con
  5 **sin repetir el valor** (lo fija el ejecutado `un_texto_en_una_cifra_para_sin_repetirlo`).
- Las etiquetas variables salen de listas constantes (`$ESTADOS_CONOCIDOS`, `$TRAMOS`, `$CAMPOS_R33`,
  `$UMBRALES`); los recuentos por estado distinguen mayúsculas (`-ccontains`), así que un estado raro de los
  datos cae en «otro estado» y nunca se convierte en etiqueta.
- `Write-Host` (l. 511–517) y los `Salir-Con` solo llevan lo tecleado (`$codigo`, `$conCeros`, `$sinCeros`), el
  código de la obra que devuelve Q0 (que por construcción es una de esas dos formas), `$Tip`, `$MaxFilas` y
  `$modo`. Ningún `ide` (`v.obride` solo se cuenta).
- Los fallos de la pasarela los cuenta el `08` por **tipo y código HTTP**, nunca por el cuerpo (l. 222–242); el
  truncado devuelve `$null` con `-Tolerante` y el script lo convierte en NO PASA sin contar nada.
- Con `-Unidades`: solo filas, columnas, segundos, bytes y **cuántas** unidades; el veredicto sale antes de las
  cuentas de la obra y de Q2.

### Solo lectura (atención especial del líder)

- Las cuatro llamadas son `Invoke-SigridLectura` del `08` (Q0, Q1 de la obra o de la guarda, Q2), que solo hace
  `Invoke-WebRequest -Method Post -Uri ($BaseUrl + "/api/sql/read")`. Sin HTTP propio, sin `sql/write`,
  `partes-reclamacion` ni `concepto-grafico`.
- Las cuatro sentencias son `SELECT` con todo valor por `?`, sin `$` dentro; el `IN` de la guarda se compone con
  marcadores, nunca con los códigos. Nada se escribe en disco.
- `$SQL_RECLAMACIONES_DE_LA_OBRA` es **carácter a carácter** la de `design.md` §3 (comparado por mí contra el
  diseño, no solo por el test) y la de la guarda, la de §15.5 con 1 y con 5 marcadores. Las dos viajan en LF
  (`ConvertTo-SqlConLf`), comprobado por el ejecutado. Ninguna nombra `dni`, `esiglog`, `esigpas`, `clamai`,
  direcciones ni `per.tex`; la de la guarda no lee ni un campo de R33.

### Checkpoints

Review de **bloque**: lo que solo se puede juzgar al cerrar la feature se marca N/A con su motivo.

**C1 — El arnés está completo y en verde**
- [x] `bash harness/init.sh` exit 0 (arriba).
- [x] Existen los ficheros del arnés (los comprueba `init.sh`).

**C2 — El estado es coherente**
- [x] Una sola `in_progress` (F-065), según `init.sh`.
- [x] Rama `feature/F-065-revision-sigrid-backend`.
- N/A `progress/current.md` describe solo la sesión activa: lo lleva el líder y el encargo me prohíbe tocarlo; no
  es objeto de una review de bloque. Ver O-2.
- N/A Toda feature `done` en `history.md`: este bloque no cierra ninguna feature.

**C3 — Arquitectura y convenciones**
- N/A Arquitectura hexagonal: el bloque no toca código del servicio (un script de `infra/` y un test).
- [x] Primera línea con la ruta, en el script y en el test.
- [x] Sin `print()` de debug, sin TODOs, sin secretos, sin dependencias nuevas (solo la biblioteca estándar y
  `pytest` en el test).
- [x] Convención de `infra/`: ASCII puro, sin BOM, CRLF (`docs/CONVENTIONS.md` l. 66–69; lo fija un test y lo
  comprueban los barridos de `test_f010_prompt_keys_infra.py`).
- N/A Parte como unidad de trabajo, firma, manuscritos, reprocesar: el bloque no procesa partes.
- [x] Nada se archiva ni se cierra: el script es de solo lectura, sin escritura en Sigrid ni en disco.
- [x] Ningún número de estado: el estado se lee por código contra `conest` (`e.cod`); el 708 es el **tipo** de
  concepto, por parámetro y con su defecto documentado, como en los scripts 24 y 28.
- [x] Ningún parte escaneado ni PDF en git (`git log --diff-filter=A`).

**C3 bis — Documentos de fuera**
- N/A El bloque no toca `docs/referencia/`.

**C4 — La verificación es real**
- [x] R29 y R70 tienen tests trazables (`test_f065_r29_…`, `test_f065_r70_…`, `test_f065_r8_r29_…`), todos en
  verde. Tabla abajo.
- [x] Sin red, sin base, sin IA: el lector doble sustituye a `Invoke-SigridLectura` y la raíz es `.invalid`.
- N/A Verificaciones MANUAL en `progress/current.md`: T-A0 y T-A0 bis están con su comando exacto en `tasks.md` y
  en `progress/impl_F-065.md` («Órdenes para el humano»), pero no en `current.md`, que lleva el líder y no puedo
  tocar. Se exige al cerrar la feature; pido al líder que las copie antes de pasárselas al humano (O-2).

**C4 bis — El rigor declarado se cumple**
- [x] `rigor: critico` declarado.
- [x] Fase RED con traza real, para T1 y para T2 bis, **reproducida por mí** la de T1 (23 failed, 3 passed).
- [x] Cobertura: `PUERTA COBERTURA: N/A` **con el motivo impreso** por `init.sh` (ninguna línea Python de
  producción). El `.ps1` no lo mide la herramienta; lo ejecutan siete tests.
- [x] Mutación de la herramienta: informe generado por ella, totales (0) recalculados, control del cero hecho
  (210 mutantes sin la exclusión) y campaña reejecutada con los mismos totales.
- [x] Los muertos comprobados: campaña de 0.0 s reejecutada (arriba).
- [x] Tiempo de la campaña: no aplica la fórmula (0 mutantes); nada sospechoso.
- [ ] **Cero supervivientes, también a mano (critico)**: los 58 del implementer están muertos, pero **dos míos
  sobreviven** (R08, R09). C-A1-1.
- [x] «Evidencias» con los cuatro números y los workers (1).
- N/A Guarda por definiciones de un fichero que sale de «no se toca»: no aplica a este bloque.
- [x] Ningún N/A sin motivo en este bloque.

**C4 ter — Rutas sensibles**
- N/A No existe `harness/rutas_sensibles.json` (solo el `.ejemplo.json`) e `init.sh` no señala ninguna ruta.

**C5 — La sesión se cerró bien**
- [x] T1, T2 y T2 bis `[x]` en `tasks.md`, con commits `F-065 T1: …`, `F-065 T2: …`, `F-065 T2 bis: …`. El resto
  de tareas es de bloques posteriores (N/A en este bloque).
- [x] Sin ficheros sin trackear (`git status` limpio).
- N/A `features.json`: F-065 sigue `in_progress`, que es su estado real a mitad de feature; no me toca.

### Cobertura: requisito → test

| Requisito | Tests |
|---|---|
| R29 · solo lectura, por el `08` | `carga_el_comun_y_solo_lee_por_el`, `no_escribe_en_disco_ni_lanza_nada`, `hay_consultas_y_todas_son_select_con_marcadores`, `el_comun_sigue_siendo_de_solo_lectura`, `ejecutado_manda_a_la_pasarela_el_texto_de_design` |
| R29 · ASCII sin BOM y CRLF | `ascii_puro_sin_bom_y_crlf`, `empieza_por_su_ruta` |
| R29 · la misma consulta que el adaptador (§3) | `la_consulta_de_la_obra_es_la_de_design_caracter_a_caracter`, `el_sql_viaja_con_saltos_lf_como_el_del_adaptador`, `los_parametros_van_en_el_orden_de_los_marcadores`, `ejecutado_manda_a_la_pasarela_el_texto_de_design` |
| R29 · R33 cerrado, nada vetado | `ninguna_consulta_nombra_lo_vetado_de_r33`, `los_campos_de_r33_son_los_diecinueve_y_en_su_columna` |
| R29 · solo recuentos, bytes y segundos (ningún texto, nombre, teléfono, correo, código ni referencia) | `nada_de_una_fila_sale_por_la_consola`, `el_detector_de_impresion_no_es_ciego`, `anotar_cifra_solo_deja_pasar_cifras_y_no_repite_lo_que_recibe`, `las_etiquetas_variables_salen_de_listas_constantes`, `ejecutado_no_saca_ningun_valor_de_las_filas`, `ejecutado_un_texto_en_una_cifra_para_sin_repetirlo` |
| R29 · los recuentos pedidos (filas, `truncated`, bytes, segundos, estado, antigüedad, unidad, R14, parecido 40/50/60, fechas) | `imprime_los_recuentos_de_r29`, `el_parecido_es_el_de_r36_aproximado`, `los_grupos_y_las_unidades_distinguen_mayusculas`, `ejecutado_cuenta_lo_que_pide_r29` (las 58 cifras) |
| R29/R8 · la pasarela tiene que aceptarla, sin truncar y bajo el techo | `la_pasarela_tiene_que_aceptarla_y_sin_truncar`, `ejecutado_si_la_pasarela_la_rechaza_no_pasa`, `r8_r29_ejecutado_llegar_al_techo_no_es_quedar_por_debajo` |
| R29 · ningún valor de pasarela, base ni clave | `ningun_valor_en_el_fichero`, `los_detectores_no_son_ciegos` |
| T2 · obra con y sin ceros | `la_obra_con_y_sin_ceros_como_el_28`, `las_consultas_auxiliares_son_las_que_dice_la_ayuda` |
| R70 · `-Unidades` y la consulta de §15.5, idéntica con 1 y con 5 | `r70_admite_unidades_y_lo_explica`, `r70_la_consulta_de_la_guarda_es_la_de_design_con_una_y_con_cinco`, `r70_la_guarda_es_la_de_la_obra_sin_r33_y_con_el_filtro_de_unidades`, `r70_un_marcador_por_unidad_y_los_parametros_en_orden`, `r70_ejecutado_la_guarda_manda_su_texto_y_solo_cuenta` |
| R70 · reglas de R29 en la guarda (cuántas, no cuáles; sin cuentas de la obra) | `r70_imprime_cuantas_unidades_y_no_cuales`, `r70_con_unidades_no_hace_las_cuentas_de_la_obra`, `r70_la_lista_se_parte_por_comas_y_tiene_tope` |
| R70 · de 1 a 50 unidades, y `-MaxFilas` de 1 a 500.000, **antes de leer** | **sin test que lo ejecute**: C-A1-1 |

### Cambios requeridos

1. **C-A1-1 · Las precondiciones se pueden bajar por debajo de la lectura y la suite sigue en verde.** En
   `infra/29_reclamaciones_obra_sigrid.ps1`, las comprobaciones de parámetros (l. 455–476: falta `-CodigoObra`,
   código no válido, `-MaxFilas` fuera de 1..500.000, `-Unidades` vacía, más de 50 unidades) van hoy **antes**
   de la primera llamada al ERP, que es lo correcto. Pero ningún test lo fija: los que las miran solo comprueban
   que la línea existe (`los_parametros_van_en_el_orden_de_los_marcadores`, `la_lista_se_parte_por_comas_y_tiene_tope`),
   y ninguno ejecuta el script con un parámetro malo. Mis mutantes R08 (la de `-MaxFilas` movida justo después de
   `$reloj.Stop()`, l. 539) y R09 (la de las 50 unidades, al mismo sitio) dejan **41 passed**: el script mandaría a
   la pasarela de producción una lectura de la obra con un `max_rows` fuera de rango, o una guarda con 51
   marcadores, y solo después se quejaría. Es la familia de la regla 7 del protocolo («la puerta va antes de
   hablar con el ERP»), y en `critico` un superviviente a mano pide un test o la aceptación escrita del humano.
   **Qué hacer**, en `services/postventa-api/tests/test_f065_scripts_infra.py`: un test ejecutado
   (`@necesita_powershell`, con `_lanzar`) parametrizado por cada rechazo —`-MaxFilas 0`, `-MaxFilas 500001`,
   `-Unidades " , "`, `-Unidades` con 51 códigos (`",".join(...)`), `-CodigoObra "0 9"` (no válido) y sin
   `-CodigoObra` si `_lanzar` lo permite (hoy lo pasa siempre; basta con añadirle un parámetro para no pasarlo)—
   que exija **salida 3** y **cero llamadas** al lector doble (`llamadas == []`), es decir, que no se llegó ni a
   Q0. Nombre sugerido `test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer`. Después, rehacer R08 y
   R09 (y, de paso, mover la del código de obra) y comprobar que caen **por ese test**. No hace falta tocar el
   script.

### Observaciones (no bloquean)

- **O-1 · La defensa fuerte son los tests ejecutados.** R03, R04, R05 y R07 (estados o nombres de R33 sacados
  de los datos, una variable permitida rellenada con una fila, un `UPDATE` en una cadena normal) solo los cazan
  los siete tests que lanzan PowerShell, que se saltan sin PowerShell en el puesto. En Windows siempre está.
  Mejora posible, si el implementer quiere: que `hay_consultas_y_todas_son_select_con_marcadores` mire también
  cualquier literal que llegue a `ConvertTo-SqlConLf`, no solo los here-strings.
- **O-2 · Para el líder:** T-A0 y T-A0 bis no están en `progress/current.md`. Sus comandos exactos están en
  `tasks.md` y en «Órdenes para el humano» de `progress/impl_F-065.md`; conviene copiarlos al pasárselos al
  humano (C4 lo exige al cerrar la feature).
- **O-3 · Para el líder o el spec-author:** el título de `design.md` §15 y su nota de la l. 576 siguen diciendo
  «PENDIENTE DE OK» y «todo depende de S-1 a S-9», aunque `b863b46` y `progress/spec_F-065.md` dejan constancia
  de la aprobación del humano (2026-10-28). No afecta al código de este bloque, pero quien lea solo el diseño
  creerá que T2 bis se hizo sin OK.
- **O-4 · Q2 supone que `rcp.fec` es un entero `YYYYMMDD`** (`r.fec = 0`). Si en Sigrid fuera otro tipo, la
  consulta falla, `-Tolerante` la recoge y el script anota «no se ha podido leer» sin tumbar la medición: el
  comportamiento es seguro, y T-A0 lo dirá.
- **Decisiones del implementer que doy por buenas:** el SQL a LF antes de mandarlo, las columnas por posición
  con la comprobación previa de 31/12, `-Tolerante` en Q1 para medir también el rechazo, los bytes aproximados
  (dicho en la ayuda), el tramo de 24 meses en «más de 24» (fijado por test) y la desviación de P-4 (`init.sh`
  ejecutado por encargo del líder).

### Automejora (propuesta, no aplicada)

Para `CHECKPOINTS.md` C4 bis, o para la regla 7 del protocolo del reviewer: **en un script de `infra/` que habla
con un sistema de producción, las precondiciones de parámetros se prueban ejecutándolo con un parámetro malo y
exigiendo que no se llegue a la primera llamada**, no viendo que la línea existe. Vale para cualquier proyecto
con scripts de medición o de despliegue (es la misma familia de «la puerta va antes del ERP», con la consola en
vez del backend): candidata a portarse a `arnes-base` si el humano la aprueba.

## Re-review del Bloque A1, tras C-A1-1 · 2026-10-28

- **Veredicto:** **APPROVED** (APROBADO). C-A1-1 queda cerrado.
- **Alcance:** `git diff 1c7cfdf..43b822f`: `4fa1b61` (solo el test), `4ab142b` (informe del implementer,
  «Corrección C-A1-1») y `43b822f` (del líder: O-2 y O-3). `infra/` sin cambios (`git diff --quiet` sobre
  `infra/`, y el script y el `08` idénticos byte a byte a los de mi copia de la primera review).
- **Nivel de rigor:** `critico`, como antes.
- **`init.sh` no ejecutado por mí**, por encargo del líder (lo está ejecutando él en el worktree). El último
  `init.sh` mío en verde es el de la primera review; el del líder sobre `43b822f` es el que cuenta para cerrar el
  bloque.

### 1 · El test nuevo cubre lo que pedí

`test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer`, ejecutado con el lector doble y
parametrizado con los seis casos que pedí: `-MaxFilas 0`, `-MaxFilas 500001`, `-Unidades " , "`, 51 unidades,
`-CodigoObra "0 9"` y sin `-CodigoObra` (`_lanzar` gana `obra: str | None`, solo por nombre; las llamadas de
siempre no cambian). Cada caso exige **salida 3**, **`llamadas == []`** (no se llega ni a Q0) y el trozo del
mensaje de **su** comprobación, para que un 3 de otra comprobación no lo dé por bueno. Es lo pedido, y un poco
más (el mensaje).

### 2 · R08 y R09 caen por él (copia desechable)

En mi copia desechable del scratchpad, con el test nuevo copiado y el mismo guion de la primera review (suite de
F-065 entera, sin `-x`):

| Id | Mutación | Antes | Ahora | Lo caza |
|---|---|---|---|---|
| R08 | la validación de `-MaxFilas`, detrás de `$reloj.Stop()` | 41 passed | **muerto**, 2 failed, 45 passed | `…parametro_malo…[maxfilas_0]` y `[maxfilas_500001]`, **solo esos** |
| R09 | el tope de 50 unidades, detrás de `$reloj.Stop()` | 41 passed | **muerto**, 1 failed, 46 passed | `…[unidades_51]`, **solo ese** |

Los dos los caza el test **de la propia feature**, y precisamente el caso que corresponde. Los otros tres del
implementer (RC1 código no válido, RC2 sin código, RC3 unidades vacías) los doy por buenos por su traza; no los
he repetido. El árbol de trabajo no se ha tocado (`git status` limpio).

Con esto, la mutación a mano del bloque queda en **cero supervivientes**: 58 + 5 del implementer, 12 míos.

### 3 · Los tests siguen en verde

| Qué | Resultado |
|---|---|
| El test nuevo, en la copia | **6 passed** |
| Los diez `test_*_scripts_infra.py` (f005, f006, f009, f010, f012, f013, f036, f051, f059, f065) y `test_f010_prompt_keys_infra.py`, en el worktree | **529 passed, 3 skipped in 52.26s** (los 47 de F-065 dentro) |
| `ruff check` del test | No lo he podido pasar: el `.venv` del servicio no trae `ruff`. Lo mide el `init.sh` del líder |

### Checkpoints que cambian

- [x] C4 bis · Cero supervivientes, también a mano (era el único `[ ]`).
- [x] C4 · Verificaciones MANUAL en `progress/current.md`: ahora están (O-2), **con el defecto de O-5**.
- O-3 aplicada: `design.md` §15 y su cabecera recogen la aprobación de S-1 a S-9 (`b863b46`).

### O-5 · Para el líder, antes de pasarle T-A0 al humano (no es del implementer)

En `progress/current.md` (`43b822f`), el comando de T-A0 lleva un **byte de control** en vez de `\2`: la ruta se
lee `infra9_reclamaciones_obra_sigrid.ps1`, y `od -c` enseña `i n f r a 002 9 _ r e c …` (el `\2` de
`infra\29_…` se tomó como escape octal al escribirlo). Copiado tal cual, PowerShell no encontraría el fichero.
No rompe nada (fallaría antes de leer), pero es justo el comando que el humano va a copiar: corrígelo a
`infra\29_reclamaciones_obra_sigrid.ps1` y comprueba con `grep -c $'\x02' progress/current.md` que sale 0. Los
comandos de `tasks.md` y de «Órdenes para el humano» en `progress/impl_F-065.md` están bien.

## Review del Bloque A2 (T3, T4) · 2026-10-28

- **Veredicto:** **CHANGES_REQUESTED** (RECHAZADO), por **un** hallazgo de tests (C-A2-1) y un arreglo del
  informe de mutación que va con él (C-A2-2). El código del dominio no tiene ningún defecto que yo haya encontrado.
- **Alcance revisado:** `git diff 16453b5..44c3163`: T3 `3282d8b`, T4 `96d9f54` y `718a633`, informe `44c3163`.
  Solo `services/postventa-api/domain/models/sigrid_bandeja.py` (nuevo, 526 líneas) y
  `services/postventa-api/tests/test_f065_dominio.py` (nuevo, 137 tests), más dos casillas de `tasks.md`.
  Contrastado con R10–R19, R21 y R36, `design.md` §5 y §10.1, `docs/CONVENTIONS.md` y `CHECKPOINTS.md`. Nada del
  Bloque A3 ni posterior.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige: fase RED con la traza pegada,
  cobertura ≥ 80 % de lo cambiado, campaña de mutación con **cero supervivientes** (también a mano) salvo
  justificación escrita que acepte el humano, y la sección «Evidencias» con los workers.
- **No me he conectado** a Sigrid, a la base ni a SharePoint. Las mutaciones las he hecho en dos `git worktree`
  desechables del scratchpad (ya borrados); el árbol de trabajo no se ha tocado (`git status` limpio).

El bloque está muy bien. El dominio es puro (solo biblioteca estándar y `domain.*`, lo fija un test por AST),
fiel a §10.1, el cruce es de verdad por unidad, y los 137 tests nombran su requisito y recorren E1–E13 tal cual.
Lo que falta es pequeño: un comportamiento que el implementer **declara** (lectura 2) y que ningún test fija.

### `init.sh`

`bash harness/init.sh`, tal cual, en el worktree sobre `44c3163`: **exit 0, «ENTORNO LISTO»**. Servicio api **9287 passed, 365 skipped in 3054,32 s** (50 min 54 s, con la máquina cargada por las campañas de otros repositorios); front en verde; raíz 115 passed; `PUERTA COBERTURA: 100.0% de 226 líneas cambiadas cubiertas (226/226, umbral 80%, nivel critico)`; ruff con 76 avisos de deuda previa, **ninguno** de los dos ficheros del bloque (`ruff check` de ambos: «All checks passed!»). Ningún test de tiempo falló, así que no he tenido que repetir ninguno. Los dos tests de F-006 que rompía el GUID literal (`test_f006_r26_…incrusta_un_identificador`) pasan: el arreglo de `718a633` queda verificado con la suite entera, que el implementer no había relanzado.

### 1 · La campaña de mutación con la suite reducida

**El argumento es cierto.** `grep -rn sigrid_bandeja` sobre todo el árbol (sin `.git` ni `.venv`): solo el
módulo, su test y las specs/informes. Ningún otro módulo del servicio lo importa.

**Y el resultado es fiable**, por una razón más fuerte que la del implementer: un mutante que **muere** con un
subconjunto de la suite muere también con la suite entera (pytest sale con error si falla cualquier test, y
`test_f065_dominio.py` está dentro de la suite completa). Con la suite entera, lo único que podría cambiar es que
un mutante muerto saliera `timeout` por la carga; nunca que sobreviviera. Como aquí murieron los 50, la suite
reducida no puede haber escondido ningún superviviente.

**Lo he comprobado tres veces, de forma independiente:**

| Comprobación | Resultado |
|---|---|
| Alcance recalculado (`harness.alcance.alcance_de_feature("F-065", base="16453b5")`) | 1 fichero, **526** líneas |
| Mutantes recalculados (`generar_mutantes`, cálculo puro) | **50** (entero 14, comparación 12, lógico 10, booleano 7, `not` 4, aritmético 3) |
| **Campaña reejecutada** con `harness.mutacion.main` y el mismo `EjecutorPytest` reducido, en una copia desechable de `44c3163`, salida en el scratchpad | **50 generados, 50 muertos, 0 supervivientes, 0 timeouts, 240,6 s**, 1 worker |
| Coste por mutante (`tiempo × workers ÷ mutantes`) | 193,5 s → 3,9 s; el mío, 4,8 s; la suite reducida tarda 4–6 s con el arranque del intérprete. Cuadra |

**Campaña oficial con la suite entera, no reejecutada**, y lo digo: a las 21:0x seguían vivas las campañas de
`partes` (4 workers), `facturas` y `proformas` y las suites de `arnes-trabajo`, y la suite entera del servicio
tarda > 120 s (el timeout por mutante) en estas condiciones: habría dado 50 `timeout`, que no verifican nada. Por
el argumento de arriba, la reducida basta.

**Una discrepancia en el informe** (C-A2-2): el informe dice 528 líneas en alcance y yo calculo 526. La
explicación está en las horas: el informe se generó a las 20:59 y `718a633` es de las 21:00. La campaña corrió
sobre el árbol **sin confirmar** (el módulo de 526 líneas, con los `NamedTuple`), mientras que el alcance lo
calculó la herramienta sobre la rama **confirmada**, todavía `96d9f54` (528 líneas). Como el fichero es nuevo
entero, el alcance cubre todas las líneas igual y los 50 mutantes son los mismos (mi reejecución sobre `44c3163`
lo confirma), pero el informe certifica un commit que no midió. Ver la automejora.

### 2 · Mutantes a mano (donde los operadores de la herramienta no llegan)

La herramienta no borra sentencias ni cambia qué se compara con qué. He aplicado 18 a mano, cada uno contra
`tests/test_f065_dominio.py` entero y sin `-x`, en la copia desechable:

| Id | Mutación | Resultado | Lo caza (tests **de la propia feature**) |
|---|---|---|---|
| M1 | R13: sin `if r.cod in propias: continue` | muerto | `r13_la_emparejada_no_coincide…`, `r13_bis_varias…`, `e7` |
| M2 | R10: la referencia sin `rstrip()` | muerto | `r10_referencia_con_blancos_al_final` |
| M3 | lectura 3: `propias` solo con la mayor | muerto | `r13_bis_varias_emparejadas…` |
| M4 | R15: sin el atajo de la clave igual | muerto | `r15_la_misma_clave_con_una_sola_palabra_casa` |
| M5 | `_texto` con `plegar` en vez de `normalizar_para_clave` | muerto | `r15_la_misma_clave…` |
| M6 | lectura 6: `None` no cuenta como desconocido | muerto | `r17_estado_desconocido…[None]`, `r17_los_desconocidos…` |
| M7 | R15: sin la guarda «la bandeja no tiene palabras» | muerto | `r15_descripcion_vacia_o_sin_palabras…` (2 casos) |
| M8 | lectura 7: el oficio vacío cuenta | muerto | `r14_los_dos_sin_oficio_no_casan` |
| M9 | R14: la ubicación vacía casa | muerto | `r14_ubicacion_vacia_o_ausente…` (3 casos) |
| M10 | lectura 2: `varias` además da `ya_en_sigrid` | muerto | `r13_bis_varias…`, `r13_bis_dos_bastan…` |
| M11 | lectura 9: hallazgos por código descendente | muerto | `r21_hallazgos_por_severidad…`, `r21_dentro_del_tope…` |
| **M12** | **lectura 2: `anulada_en_sigrid` si cualquiera de las suyas está en `NPR`, no solo la mayor** | **SOBREVIVE** | **ninguno** (137 passed) |
| M13 | R10: `referencia_desconocida` solo si hay UUID | muerto | `r10_pvi_sin_uuid…`, `r21_hallazgos…`, `e8` |
| M14 | `codigo_distinto` contra la menor | muerto | `r13_bis_varias_de_una_volcada…` |
| M15 | lectura 4: `ya_en_sigrid` solo para las evaluables | muerto | `r11_emparejada_y_no_volcada…[descartada]` |
| M16 | R13 bis: se empareja con la menor | muerto | `r13_bis_varias…` (2) |
| M17 | R18: sin «conflicto primero» | muerto | `r18_primero_los_conflictos` |
| M18 | R18: el tope sobre la lista sin ordenar | muerto | 4 tests de R18 |

Todos los muertos los caza un test **de la propia feature** (el módulo no lo importa nadie más). **M12 sobrevive**:
la lectura 2 dice que con una `volcada` con varias «las comprobaciones de R12 [van] contra la de código mayor»,
pero el único test del caso (`test_f065_r13_bis_varias_de_una_volcada_y_el_codigo_contra_la_mayor`) fija el
**código**, no la anulación. En `critico`, eso es C-A2-1.

### 3 · Las diez lecturas de la spec, una a una

Ninguna cambia N-1, N-2 ni N-3 (el tope 500.000, el umbral 50 con 2 palabras en común y la ficha sin mirar, con
`repr=False`, están tal cual), y S-1 a S-9 no se tocan en este bloque (son de A4 bis). Pero **cuatro eligen
donde la spec no dice nada y tienen consecuencias fuera del dominio**: las marco **[al humano]** para que las
lleves tú.

| # | Lectura | Mi juicio |
|---|---|---|
| 1 | `sigrid_cod` = la reclamación de la que habla el hallazgo; en `volcada_no_encontrada`, el **guardado**; en `codigo_distinto`, el guardado va en `sigrid_cods` | **[al humano] Elige donde la spec no dice**. R20 solo nombra los campos y R13 bis dice que `sigrid_cods` lleva «todos los códigos» de `varias`. Con esta lectura `sigrid_cods` significa dos cosas distintas según el tipo («todas las de Sigrid» en `varias`, «el de nuestra base» en `codigo_distinto`), y en `volcada_no_encontrada` el `sigrid_cod` **no está** en `reclamaciones`, así que el `lineaDeHallazgo(hallazgo, reclamacionesPorCod)` de F-064 no lo encontrará. No es un error, pero es contrato con F-064: hay que escribirlo en `design.md` §10.1 / R20 antes de F-064, o usar un campo propio (p. ej. `guardado_cod`) |
| 2 | `varias_en_sigrid` sustituye a `ya_en_sigrid`; con una `volcada` con varias, `varias` **y** R12 contra la mayor | Conforme con la tabla de §5.1 y con R41 (las da como alternativas). **[al humano] Una consecuencia a enseñar**: con la letra de R12 + R13 bis, una `volcada` guardada como `0081` con `PVI-` en `0081` y `0082` da `varias_en_sigrid` **y** `codigo_distinto` («otro código que el guardado»), aunque el guardado **sí** está en Sigrid (lo fija el test `r13_bis_varias_de_una_volcada…`). El aviso es literal pero engañoso: el problema es el duplicado, que `varias` ya enseña. Que el humano diga si `codigo_distinto` debe callarse cuando el guardado está entre las suyas |
| 3 | R13 con varias: **ninguna** de las que llevan su referencia se cruza por criterios con ella, no solo la mayor | **[al humano, informativo] Va más allá de la letra**: R13 excluye «la emparejada» y R13 bis dice que la emparejada es la mayor, así que literalmente las otras sí se cruzarían. La lectura es sensata (son sus propios partes; sin ella saldrían `coincide` de la incidencia consigo misma) y solo cambia los hallazgos y `coincidencias_total` de esa incidencia: su veredicto de R41 es `se_enlaza` igual. Recomiendo aceptarla y escribirla en R13 |
| 4 | `ya_en_sigrid` en cualquier estado no `volcada`, también `descartada` y con la emparejada en `NPR` | **Conforme** con R11 literal («una incidencia que **no** está `volcada`»), fijado por test (M15). Para **A4 bis**, no para este bloque: una `aprobada` emparejada con una `NPR` será `se_enlaza` (R41), y el ensayo la dejará `volcada` enlazada a un parte anulado vía `idempotente`. Conviene que el humano lo vea cuando toque S-3 |
| 5 | Toda referencia no nula que no da incidencia es `referencia_desconocida`; `rstrip`; UUID solo de 36 caracteres | **Conforme**. Los dos detalles no los dice la spec, pero son más estrictos o iguales que la pasarela, no cambian nada aprobado y están fijados (M2, M13) |
| 6 | Estado desconocido: cualquiera que no sea uno de los cinco **tal cual**, también `None`; el recorte, «del mapeo del adaptador (A3)» | **[al líder, importante para A3]** La lectura del dominio es correcta, pero **traslada a A3 una obligación que `tasks.md` no recoge**: T5 no dice que el mapeo recorte `estado` (ni `cod`). Si `conest.cod` llegara rellenado con blancos, **todas** las reclamaciones serían «desconocidas» y el cruce daría **cero pares sin error** (solo lo delataría `estados_desconocidos`). T-A0 no lo descarta: el script 29 hace `.Trim()` antes de contar por estado (línea 613). Pido que T5 lo diga explícitamente (con su test) o que se compruebe. Lo de contar `None` como desconocido es una elección menor (el script de T-A0 los separaba en «sin estado»); fijada por test (M6) |
| 7 | Oficio `""` como sin oficio; ubicación vacía o de blancos no casa | **Conforme** con R14 (M8, M9) |
| 8 | R18 sin fecha: detrás de las fechadas | **Conforme** (la regla de R21 para las reclamaciones); fijado por test |
| 9 | R21: hallazgos por tipo del enumerado, `incidencia_id` y código **ascendentes**; el tope elige por fecha y la lista sale por código | **[al humano] Elige donde la spec no dice**, y **tiene consecuencia en F-064**: R56 de F-064 enseña «las 3 primeras y y N más». Si la página toma los tres primeros `coincide` de una incidencia en el orden de `hallazgos`, saldrán los de **código menor** (los más antiguos, `RS23…` antes que `RS26…`), no los tres que R18 prioriza (conflicto, fecha descendente). O la página reordena con la fecha de `reclamaciones`, o el backend emite los `coincide` de cada incidencia en el orden de R18. Hay que decidirlo antes de F-064 |
| 10 | `parecido("por la","por la")` = 100 pero no casa; `Grifos`/`grifo`, 100 y una sola en común, no casa | **Conforme** con R36 y la última frase de R15 (M7). Y `Grifo`/`grifo` (misma clave, una palabra) **sí** casa por la regla «la misma descripción por `normalizar_para_clave`», que es la letra de R15 (M4) |

### Checkpoints

Review de **bloque**: lo que solo se puede juzgar al cerrar la feature se marca N/A con su motivo.

**C1 — El arnés está completo y en verde**
- [x] `bash harness/init.sh` exit 0, suite entera en verde (arriba).
- [x] Existen los ficheros del arnés (los comprueba `init.sh`).

**C2 — El estado es coherente**
- [x] Una sola `in_progress` (F-065), según `init.sh`.
- [x] Rama `feature/F-065-revision-sigrid-backend`.
- N/A `progress/current.md`: lo lleva el líder y el encargo me prohíbe tocarlo; no es objeto de una review de
  bloque.
- N/A Toda feature `done` en `history.md`: este bloque no cierra ninguna feature.

**C3 — Arquitectura y convenciones**
- [x] Hexagonal: el módulo vive en `domain/models/` e importa solo biblioteca estándar y `domain.models.*`
  (`normalizacion`, `plantilla_incidencias`, `revision`, `volcado`); `FichaReclamacion`, del puerto
  (`domain/ports/`), solo bajo `TYPE_CHECKING`, para la anotación. Lo fija `test_f065_r19_el_dominio_es_puro`
  (AST) y lo vigilan las guardas de F-006. Ni `revision.py`, ni `normalizacion.py`, ni
  `plantilla_incidencias.py`, ni `volcado.py` tocados (T4).
- [x] Primera línea con la ruta, en el módulo y en el test.
- [x] Sin `print()`, sin TODOs, sin secretos; sin GUID literal (lo arregló `718a633`; los dos tests de F-006
  vuelven a verde en `init.sh`). Datos inventados (R39): `UUID(int=n)`, `Ejemplo …`, `@ejemplo.invalid`, los
  códigos ficticios de §5.4.
- N/A Parte como unidad de trabajo, firma, manuscritos, reprocesar, archivar: el bloque no procesa partes ni
  escribe nada.
- [x] Ningún número de estado: el estado de Sigrid es su **código** (`EstadoSigrid`), C3.
- [x] Ningún parte escaneado ni PDF en git.

**C3 bis — Documentos de fuera**
- N/A El bloque no toca `docs/referencia/`.

**C4 — La verificación es real**
- [x] R10–R19, R21, R36 y E1–E13 tienen tests trazables, todos en verde (tabla abajo).
- [x] Sin red, sin base, sin IA, sin reloj (el test de pureza prohíbe `.now(`, `.today(`, `perf_counter`… en el
  módulo).
- N/A Verificaciones MANUAL: este bloque no tiene ninguna.

**C4 bis — El rigor declarado se cumple**
- [x] `rigor: critico` declarado.
- [x] Fase RED con la salida real pegada (`ModuleNotFoundError` en la recogida, `3282d8b`).
- [x] Cobertura: `PUERTA COBERTURA` `[OK]`, **100 %** de 226 líneas cambiadas (umbral 80 %).
- [x] Mutación: informe generado por la herramienta (con la nota de la suite reducida), alcance y mutantes
  recalculados (526 líneas, 50 mutantes; la diferencia 528/526 se explica arriba y es C-A2-2).
- [x] Los muertos comprobados: campaña de 193,5 s (< 5 min) **reejecutada** por mí con la misma suite reducida:
  50/50/0/0. Con la suite entera, no (motivo arriba).
- [x] Tiempo de la campaña: 3,9 s por mutante con 1 worker, coherente con la suite reducida.
- [ ] **Cero supervivientes, también a mano (critico)**: la campaña, 0; **a mano, M12 sobrevive**. C-A2-1.
- [x] «Evidencias» con los cuatro números y los workers (1).
- N/A Guarda por definiciones de un fichero que sale de «no se toca»: no aplica a este bloque.
- [x] Ningún N/A sin motivo en este bloque.

**C4 ter — Rutas sensibles**
- N/A No existe `harness/rutas_sensibles.json` (solo el `.ejemplo.json`).

**C5 — La sesión se cerró bien**
- [x] T3 y T4 `[x]` en `tasks.md`, con commits `F-065 T3: …` y `F-065 T4: …`. El resto, de bloques posteriores.
- [x] Sin ficheros sin trackear (`git status` limpio, también tras mis copias).
- N/A `features.json`: F-065 sigue `in_progress`, su estado real; no me toca.

### Cobertura: requisito → test

| Requisito | Tests (`tests/test_f065_dominio.py`) |
|---|---|
| R8 (la constante del tope) | `r8_el_tope_es_el_de_la_pasarela_desplegada` |
| R10 | `r10_referencia_canonica`, `…sin_distinguir_mayusculas`, `…con_blancos_al_final`, `…lo_que_no_es_pvi_y_un_uuid…`, `…empareja_con_y_sin_mayusculas`, `…pvi_sin_uuid…`, `…pvi_de_otra_obra…`, `…sin_referencia_no_hay_aviso`, `e8` |
| R11 | `r11_emparejada_y_no_volcada_es_ya_en_sigrid` (con `descartada`), `r11_…anulada`, `e7` |
| R12 | `r12_volcada_y_encontrada_sin_hallazgo`, `…volcada_no_encontrada`, `…codigo_distinto`, `…anulada_en_sigrid`, `…anulada_y_con_otro_codigo…`, `e13` |
| R13 / R13 bis | `r13_la_emparejada_no_coincide…`, `r13_la_emparejada_si_coincide_con_las_demas`, `r13_bis_varias…`, `r13_bis_dos_bastan…`, `r13_bis_varias_de_una_volcada…` (falta la anulación: C-A2-1), `e6` |
| R14 | los 13 `r14_…` (unidad, oficio, ubicación, sin oficio en cada lado, vacía, mayúsculas, extremos, `Cocina 1`, ambiguo), `e9`–`e11` |
| R15 | los 14 `r15_…` (umbral justo, 49, 50, una palabra, misma clave, vacía, vigente frente a importada, misma unidad), `e2`–`e2d` |
| R16 | `r16_las_seis_situaciones`, `r16_descartada…`, `r16_volcada…`, `e12` |
| R17 | `r17_severidad_por_estado`, `…reincidencia…`, `…sin_corte_de_fecha`, `…anulada_no_da_pares`, `…estado_desconocido…`, `…los_desconocidos_cuentan…`, `r17_los_dos_criterios…`, `e3`–`e5` |
| R18 | los 6 `r18_…` (tope, conflictos primero, código a igual fecha, sin fecha, por incidencia, diez justas) |
| R19 | `r19_el_dominio_es_puro`, `r19_el_cruce_es_por_unidad_y_acotado`, `r19_los_tipos_del_cruce_son_inmutables` |
| R21 | los 4 `r21_…` |
| R36 | los 15 `r36_…` |
| R9 (sin filas) / R33 (la ficha, sin `repr`) | `r9_sin_nada_que_cruzar`, `r33_la_ficha_viaja_sin_tocar…` |

### Cambios requeridos

1. **C-A2-1 · Fijar que `anulada_en_sigrid` mira solo la emparejada (la mayor).** En
   `services/postventa-api/tests/test_f065_dominio.py`, junto a
   `test_f065_r13_bis_varias_de_una_volcada_y_el_codigo_contra_la_mayor` (l. 640), un test con una `volcada`
   guardada como la **mayor**, dos `PVI-` suyas y la **menor** en `NPR`: debe salir `varias_en_sigrid` y **ningún**
   `anulada_en_sigrid`; y el caso simétrico (la mayor en `NPR`) con `anulada_en_sigrid` sobre la mayor. Debe matar
   M12: en `sigrid_bandeja.py` l. 412, `if mayor.estado == EstadoSigrid.NPR:` →
   `if any(r.estado == EstadoSigrid.NPR for r in suyas):`. Pega en el informe la traza del mutante muerto. Si el
   humano decide en la lectura 2 que el comportamiento debe ser otro, el test se escribe con lo que decida.
2. **C-A2-2 · Regenerar `progress/mutacion_F-065_bloqueA2.md` desde un árbol confirmado.** Tras confirmar C-A2-1,
   relanzar la campaña (con la suite reducida y su nota, que acepto) sobre el commit, con `git status` limpio
   antes de empezar, para que el alcance (526) y el commit que dice el informe sean los que se midieron. Hoy el
   informe declara 528 líneas (`96d9f54`) y midió el árbol sin confirmar de `718a633`.

### Para el líder (no son del implementer)

- **Llevar al humano** las lecturas **1, 2, 3 y 9** (tabla de arriba): las cuatro eligen donde la spec no dice
  nada; la 1 y la 9 son contrato con F-064 y conviene fijarlas en `design.md` §10.1 / R20–R21 antes de esa
  feature.
- **Lectura 6 → A3**: añadir a T5 que el mapeo recorta `estado` (y `cod`) y su test, o comprobar con una lectura
  que `conest.cod` no viene rellenado. Sin eso, un relleno daría cero pares sin error.
- **Lectura 4 → A4 bis**: enseñar al humano, con S-3, que una candidata emparejada con una `NPR` será `se_enlaza`.

### Observaciones (no bloquean)

- **O-A2-1 · Unidad nula.** El índice es `dict[str | None, …]`: una incidencia sin unidad casaría con las
  reclamaciones sin unidad. En la práctica no pasa (la consulta de §3 sube a la unidad por `JOIN`, y la revisión
  exige unidad), pero una guarda `if vigentes.unidad_codigo is None: return []` con su test lo cerraría.
- **O-A2-2 · El test de coste cambió de datos tras la RED** (declarado en «Desviaciones»). Lo acepto: sigue
  demostrando el índice (500.000 pares con él, 500 millones sin él, imposibles en 20 s) y el cambio evita medir la
  construcción de 400.000 hallazgos en vez del cruce. El límite de 20 s frente a 3,1 s deja margen para la carga.
- **O-A2-3 · `_codigo_guardado` sin guarda**: de acuerdo con el implementer; `volcada` implica parte en Sigrid
  (R1 de F-059).

### Automejora (propuesta, no aplicada)

1. **`harness/mutacion.py`: negarse (o avisar en la cabecera) si los ficheros del alcance tienen cambios sin
   confirmar.** El alcance sale de `git diff base..rama` (lo confirmado) y los mutantes, del fichero en disco: si
   difieren, el informe certifica un commit que no midió (es lo que ha pasado aquí, 528 frente a 526). Vale para
   cualquier proyecto: candidata a `arnes-base`.
2. **Protocolo del reviewer, regla 4: reconocer la campaña con suite reducida.** Cuando la suite entera no cabe en
   el timeout por mutante, una campaña con solo los tests de la feature es válida si (a) ningún otro módulo
   importa el fichero mutado (comprobado por el reviewer), (b) el informe lo declara en su cabecera y (c) el
   reviewer la reejecuta igual; con cero supervivientes, la suite entera no puede dar menos muertos. Hoy la regla
   pide la orden oficial tal cual y deja este caso al criterio de cada review. Candidata a `arnes-base`.

## Re-review del Bloque A2, tras T4 bis · 2026-10-28

- **Veredicto:** **CHANGES_REQUESTED** (RECHAZADO), por dos cosas que **no piden código al implementer**:
  - **C-A2-3**: la aceptación escrita del humano de un mutante a mano equivalente (R4, abajo). En `critico` yo no
    puedo aceptarla (`CHECKPOINTS.md` C4 bis).
  - **C-A2-4**: un `bash harness/init.sh` en verde de una pasada. El mío salió rojo por un test de tiempo de F-036
    (1,04 s frente a 1 s) con el puesto cargado.

  C-A2-1, C-A2-2 y las decisiones 1, 2, 3 y 9 están cerradas en el código y en los tests. **Con las dos cosas
  anotadas, el bloque queda APROBADO sin otra review del código.**
- **Alcance:** spec `c961345` y `7269617`; código `a0201d7..fbb77dc` (RED `a0201d7`, dominio `c99a0d3`, test
  M8b `d3f94c8`, informe y mutación `fbb77dc`). Solo `sigrid_bandeja.py`, `test_f065_dominio.py`, `tasks.md` y los
  dos informes. Nada de A3 ni posterior.
- **Nivel de rigor:** `critico`, como antes.
- No me he conectado a Sigrid, a la base ni a SharePoint. Mutaciones en dos `git worktree` desechables del
  scratchpad sobre `fbb77dc`, ya borrados; el árbol de trabajo, limpio.

### `init.sh`

`bash harness/init.sh`, tal cual, una vez, sobre `fbb77dc`: **exit 1, en ROJO**, por **un test de tiempo**, no
por este bloque.

- Servicio api: `1 failed, 5324 passed, 49 skipped in 763,84 s`, parado por `-x` en
  `test_f036_excel_lector.py::test_f036_r115_…_se_lee_en_menos_de_un_segundo[combinado-A-H-Incidencias]`:
  **1,04 s frente al tope de 1,0 s**. El puesto estaba cargado: seguían vivas las campañas de mutación de
  `partes`, `facturas` y `proformas`.
- Por ese `-x`, la `PUERTA COBERTURA` sale `[KO]` **46,2 % (108/234)**: midió solo la parte de la suite que llegó a
  correr, y `test_f065_dominio.py` va detrás.
- El resto, en verde: arnés, `features.json`, `BACKLOG.md`, `compileall`, raíz (115 passed), front, rama. ruff: 76
  avisos de deuda previa.

Lo que he hecho después, y lo digo para que se vea qué nivel de verificación hay:

| Qué | Resultado |
|---|---|
| `test_f036_r115_…` **a solas**, tres veces | **9 passed**, las tres (30,3 s, 31,2 s y 52,3 s, los 9 casos) |
| **La parte de la suite que `-x` no llegó a correr** (los 54 ficheros desde `test_f036_excel_lector.py`, sin `-x`) | `1 failed, 4073 passed, 212 skipped in 1101,03 s`. El fallo, **otro test de tiempo del mismo fichero**: `test_f036_r117_…_se_rechazan_en_menos_de_un_segundo[celda-con-estilo-fila-1200]` |
| `test_f036_r117_…` **a solas**, tres veces | **7 passed**, las tres |
| Cobertura del módulo con su test (`coverage run --branch`, datos en el scratchpad) | **234 sentencias, 0 sin cubrir; 66 ramas, 0 parciales: 100 %** |

Entre las dos pasadas han corrido todos los tests del servicio (5324 + 4073 = 9397 passed). Los únicos dos fallos
son topes de 1 s de F-036 por la carga, y pasan a solas. T4 bis no toca nada que lean: solo
`sigrid_bandeja.py`, que únicamente importa su test. **Aun así, `init.sh` no ha salido en verde de una pasada**, y
con `init.sh` en rojo no se aprueba (regla dura del reviewer). C-A2-4.

### 1 · C-A2-1 y C-A2-2: cerrados

- **C-A2-1.** `test_f065_r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid` y su simétrico
  `…_la_mayor_anulada_da_anulada_en_sigrid`. **M12 muere** en mi copia (1 failed, el primero de los dos), como en la
  traza del implementer.
- **C-A2-2.** El informe se regeneró sobre `d3f94c8` (23:06) a las 23:14, con el árbol limpio; `d3f94c8..fbb77dc` no
  toca el módulo. **Recalculado**: 570 líneas en alcance (= `wc -l`), 50 mutantes (los mismos operadores).
  **Reejecutada** la campaña (178,7 s < 5 min) con la misma suite reducida, en una copia de `fbb77dc`: **50 / 50 /
  0 / 0, 250,5 s**, 1 worker; 5,0 s por mutante, coherente con la suite reducida. Los importadores siguen siendo
  solo el módulo y su test, así que la suite reducida sigue siendo válida (argumento de la review anterior).

### 2 · Las decisiones, cumplidas en el código

| Decisión | Código (`sigrid_bandeja.py`) | Lo fija | Mutante mío |
|---|---|---|---|
| **1** · `guardado_cod`; `sigrid_cod` siempre de una reclamación de la respuesta o `None` | `Hallazgo.guardado_cod`; `volcada_no_encontrada` con `None` y el guardado aparte; `codigo_distinto` con `sigrid_cods=()`; la tabla de §10.1 en la docstring | `r12_r20_los_codigos_de_cada_hallazgo_segun_la_tabla` y `r12_r20_las_invariantes_de_los_codigos` (los siete tipos) | R6 (el guardado otra vez en `sigrid_cod`) y R7 (`guardado_cod` en `anulada`): **muertos** (5 tests cada uno) |
| **2** · `codigo_distinto` callado si el guardado está entre las suyas; `anulada` solo contra la mayor | `if all(r.cod != guardado for r in suyas)` (l. 441); `if mayor.estado == NPR` (l. 451) | `r12_r13_bis_…_guardado_entre_ellas_sin_codigo_distinto`, `…_guardado_fuera_da_codigo_distinto`, los dos de la anulación | R2 (como T4) y R1 (= M12): **muertos** |
| **3** · R13 con varias: ninguna de las suyas se cruza con ella, todas con las demás | sin cambio (ya era así en T4) | `r13_enmienda_ninguna_de_las_suyas_coincide_con_ella_y_todas_con_las_demas` (completa la mitad que faltaba) | M1 y M3 del implementer, muertos |
| **9** · los `coincide` de una incidencia en el orden de R18; los demás por `sigrid_cod` ascendente | `_Ordenable(h, puesto)` con el puesto de R18 (l. 558) | `r21_los_coincide_de_una_incidencia_en_el_orden_de_r18_con_el_tope` (fechas que no siguen el orden de los códigos, sin fecha, empates), `r21_los_coincide_por_fecha_y_no_por_codigo`, `r21_hallazgos_por_severidad…` | R3 (por código, como T4) y R5 (orden inverso): **muertos** (3 tests); **R4: sobrevive, equivalente** (C-A2-3) |

El desempate `int | str` no puede comparar un entero con un texto: el tipo va antes en la clave, y a igual tipo los
dos desempates son del mismo tipo. Comprobado leyendo la clave; ningún test da `TypeError`.

**La enmienda de `7269617`** (no recortar `unidad_codigo` ni `oficio_codigo`, como F-036) no toca este bloque: es
del mapeo de T5 y está escrita allí con su test. Sin objeción: recortar solo un lado podía romper R14.

### 3 · La enmienda a S-3 (NPR → `choca`): es correcto dejarla para A4 bis

- Es una regla del **veredicto** (R41, regla 0 de §15.2), y el veredicto no existe en este bloque: `Veredicto`,
  `veredictos` y `Cruce.pares` nacen en T14. Ponerla ahora sería adelantar T14.
- **El dominio de A2 ya da lo que necesita**: `Cruce.reclamaciones` lleva cada reclamación con su `incidencia_id`
  emparejado, y solo la mayor lo lleva (`emparejada_de`), con su `estado`. `veredictos` podrá saber «la emparejada
  de X está en `NPR`» sin que `Cruce` gane nada, como dice §15.2. Los tests de T4 bis ya fijan que la emparejada es
  la mayor (M16) y que la menor anulada no cuenta (M12), que es justo lo que la regla 0 necesita.
- **Está en las tareas**: T13 trae los tres casos (E7 con la emparejada en `NPR` → `choca` con solo su código,
  también con un `ya_existe`; la menor de dos en `NPR` → `se_enlaza`) y T15 la exclusión del ensayo (sin confirmar,
  excluida con ese código; confirmada, se manda). T14 no la nombra, pero su verificación ejecuta los tests de T13.

### 4 · Mutantes a mano

Los 27 del implementer (M1–M26 y M8b) los doy por buenos por su tabla; he repetido los que tocan lo nuevo, en mi
copia, con `tests/test_f065_dominio.py` entero y sin `-x`:

| Id | Mutación | Resultado | Lo caza (tests de la propia feature) |
|---|---|---|---|
| R1 | M12: `anulada` si cualquiera de las suyas está en `NPR` | muerto (1) | `r12_r13_bis_la_menor_anulada_no_da_anulada_en_sigrid` |
| R2 | `codigo_distinto` con `mayor.cod != guardado` (como T4) | muerto (1) | `…_guardado_entre_ellas_sin_codigo_distinto` |
| R3 | los `coincide` por código ascendente (como T4) | muerto (3) | los 3 `r21_…` con `coincide` |
| **R4** | **los `coincide` con desempate constante, `_Ordenable(h, 0)`** | **sobrevive (145 passed)** | **ninguno: equivalente** |
| R5 | los `coincide` en orden inverso (`-puesto`) | muerto (3) | los 3 `r21_…` con `coincide` |
| R6 | `volcada_no_encontrada` con el guardado en `sigrid_cod` | muerto (5) | `r12_volcada_no_encontrada`, los 2 `r12_r20_…`… |
| R7 | `anulada_en_sigrid` con `guardado_cod` | muerto (5) | `r12_anulada_en_sigrid`, `…anulada_y_con_otro_codigo…`, `…la_mayor_anulada…`… |

**R4 es equivalente, no un hueco de los tests.** `sorted` de Python es **estable** (garantía del lenguaje), y los
`coincide` de cada incidencia entran en `hallazgos` **ya** en el orden de R18 (`pares` se ordena antes del
`enumerate`), contiguos y después de los de emparejamiento. A igual severidad, tipo e `incidencia_id` solo empatan
`coincide` de la misma incidencia y severidad, y la estabilidad los deja en su orden de entrada, que es R18. Así
que el `puesto` no cambia ninguna salida posible: ningún test puede matar R4. El implementer eligió el `enumerate`
para que la clave no dependa de la estabilidad ni de un literal que la herramienta mutaría (lo explica en
«Decisiones de diseño»), y me parece bien: quitarlo dejaría la misma equivalencia escondida en la estabilidad, o
un `0` literal que la campaña daría como superviviente equivalente. **No pido cambiar el código.**

### Checkpoints que cambian respecto de la review del Bloque A2

- [ ] C1 · **`init.sh` en rojo** sobre `fbb77dc` por un test de tiempo de F-036 (arriba). C-A2-4.
- [ ] C4 bis · `PUERTA COBERTURA` `[KO]` 46,2 %, **efecto del `-x`**, no de este bloque: medida a mano, 100 % del
  módulo (234/234, 66/66 ramas). Se cierra con C-A2-4.
- [x] C4 · Las enmiendas de R12, R13, R20 y R21 tienen tests trazables (tabla de §2).
- [x] C4 bis · Fase RED de T4 bis con la salida real (11 failed, `a0201d7`); los dos de la anulación y el de R13
  en verde en la RED, explicado (fijan lo que T4 ya hacía; su prueba es que matan M12 y M3).
- [x] C4 bis · Mutación: informe regenerado desde un árbol confirmado, recalculado y reejecutado (50/50).
- [ ] C4 bis · **Cero supervivientes, también a mano (critico)**: la campaña, 0; a mano, **R4 equivalente**, que
  necesita la aceptación escrita del humano. C-A2-3.
- [x] C4 bis · «Evidencias» de T4 bis con los cuatro números y el worker.
- [x] C5 · T4 bis `[x]`, commits `F-065 T4 bis: …`; `git status` limpio.

El resto, como en la review del Bloque A2.

### Cambios requeridos

1. **C-A2-3 · (para el líder y el humano, no para el implementer)**: que el humano acepte **por escrito** R4 como
   mutante equivalente, con el motivo de §4 (la ordenación de Python es estable y los `coincide` entran ya en el
   orden de R18, así que el desempate por puesto no cambia ninguna salida). Basta con que el líder anote la
   aceptación, con fecha, debajo de esta sección o en `progress/current.md`. Sin cambios de código ni de tests, y
   sin otra review.
2. **C-A2-4 · (para el líder)**: `bash harness/init.sh` en verde de una pasada sobre `fbb77dc` (o sobre lo que haya
   encima, si solo son informes), con el puesto más libre, y anotar el resultado aquí. Si vuelve a caer un
   `test_f036_r11x_…_menos_de_un_segundo`, es el tope de 1 s de F-036 frente a la carga de las otras campañas, no
   este bloque: el remedio es lanzarlo con el puesto libre, no tocar el tope.

### Observaciones (no bloquean)

- **O-A2-4 · La cascada a otros bloques está apuntada**: T7 serializa `guardado_cod` (`null` donde no toca) y
  F-064 recoge `guardado_cod`, el `sigrid_cod` `null` en `volcada_no_encontrada` y el orden de R18 sin reordenar.
  F-064 está en otro worktree (`postventa-f064`): conviene que su spec lo recoja antes de empezarla, porque el
  contrato ya ha cambiado aquí.
- **O-A2-1 y O-A2-2** de la review anterior siguen igual (la unidad nula, el test de coste): no bloquean.

### Automejora (propuesta, no aplicada)

Para `CHECKPOINTS.md` C4 bis («cada [mutante a mano] declarado equivalente necesita la aceptación escrita del
humano»): permitir que el reviewer dé por cerrado un mutante a mano cuya equivalencia se **demuestra** con una
garantía del lenguaje o de la biblioteca estándar citada (aquí, la estabilidad de `sorted`), dejándolo anotado para
que el humano lo vea, y reservar la aceptación del humano para las equivalencias que son un juicio. Hoy un caso
demostrable bloquea el bloque igual que uno discutible. Vale para cualquier proyecto: candidata a `arnes-base` si
el humano la aprueba.
