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
