<!-- progress/impl_F-013.md -->
# F-013 · Informe del implementer

> Rama `feature/F-013-archivo-posventa`. Rigor **`critico`**. Encargos por
> bloques: este informe crece bloque a bloque.

---

## Bloque 0 · T1 (2026-09-24)

**Alcance del encargo: solo T1.** T2 y T3 son del humano (MANUAL) y T4 es una
parada del líder. `harness/features.json` sin tocar. **No se ha ejecutado nada
contra Azure, Graph, Key Vault ni Sigrid**: los ensayos de abajo son locales,
con las llamadas de red sustituidas por datos inventados.

Commit: `553ce39` (`F-013 T1: scripts de solo lectura 23 … y 24 …`), más el de
este informe.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `infra/23_destino_posventa.ps1` (nuevo) | Medición T2 (R27, R28). URL → sitio y biblioteca, roles del token y, con `-CodigoObra`, el árbol **solo de carpetas** obra → `PARTES INCIDENCIAS` → unidades → `PARTES FIRMADOS`. Solo `GET` en Graph + el `POST` del token |
| `infra/24_ubicacion_sigrid.ps1` (nuevo) | Medición T3 (R32). Unidades de posventa de una obra (`upv` → `upv.obride`) con `con.cod`, `con.res` y nº de reclamaciones. Solo `sql/read`, vía `08_lectura_sigrid_comun.ps1` |
| `services/postventa-api/tests/test_f013_scripts_infra.py` (nuevo) | 44 tests del contrato de los dos scripts |
| `specs/F-013-archivo-posventa/tasks.md` | T1 marcada `[x]` |

`08_lectura_sigrid_comun.ps1` **no se ha tocado** (es de F-009 y lo cargan otros
nueve scripts): los dos nuevos lo cargan por punto y usan su veredicto, sus
códigos de salida, su TLS 1.2 y `Invoke-SigridLectura`.

### 2 · Cómo son los dos scripts

**`23_destino_posventa.ps1`**

- Parámetros: `-UrlSitio` (obligatorio salvo con `-WhatIf`),
  `-NombreBiblioteca` («Documentos compartidos»), `-CodigoObra`,
  `-CarpetaBase` (`""` = raíz, D-1), `-CarpetaIncidencias` («PARTES
  INCIDENCIAS»), `-CarpetaFirmados` («PARTES FIRMADOS»),
  `-MostrarIdentificadores`, `-WhatIf`. **Añadidos a lo que pedía el
  `design.md` §7.1**, y por qué, en §3: `-MostrarNombres`, `-DesdeKeyVault`,
  `-CarpetaObra`, `-MaxCarpetasObra`.
- Pasos: 1/4 token y roles (avisa de los amplios, F-018); 2/4 sitio por ruta
  (`GET /sites/{host}:/sites/<x>`) y bibliotecas (`/drives` y `/drive`); 3/4
  carpetas y ficheros de la base; 4/4 con `-CodigoObra`, el árbol. En cada
  nivel dice qué carpetas **casan** y cuáles son **parecidas** (§4.1, §4.2,
  §4.5), recorre también las parecidas (para que T2 vea qué hay dentro), cuenta
  los ficheros de cada hoja **sin nombrarlos**, marca las unidades **sin
  cifras** (riesgo 11: `VILLA CINCO`) y los **números de unidad repetidos**
  (D-6: saldrían ambiguas), y mira las versiones de **un** fichero para saber
  si hay versionado.
- Veredicto con el formato del 08: `PASA` si la aplicación ve el sitio,
  encuentra la biblioteca, tiene permiso de escritura en sitios, existe la base
  y —con `-CodigoObra`— hay **exactamente una** carpeta de obra que casa y
  **una** `PARTES INCIDENCIAS` que casa. Lo demás son datos (`(dato)`).
- Códigos de salida: 0 pasa, 3 parámetro, 5 `-CarpetaObra` inexistente, 6 no
  pasa, 7 credenciales o token, 8 Graph rechaza una lectura (403 lo explica
  como F-018), 9 sitio inexistente, 10 biblioteca no encontrada o ambigua.

**`24_ubicacion_sigrid.ps1`**

- Una consulta parametrizada que parte de `dbo.upv` (y no de `rcp`) para traer
  también las unidades **sin** reclamaciones, con el mismo camino que usará el
  adaptador (`design.md` §6.2): `upv.ide = con.ide` de la unidad,
  `upv.obride = con.ide` de la obra, y un `COUNT(*)` de reclamaciones de
  `tip = ?` por unidad.
- Pregunta el código **en sus dos formas** (`0677` y `677`) y dice si el que
  guarda Sigrid es **literalmente** el pedido: R10 compara literal.
- Dos obras con el mismo código (la 0677 tiene dos filas en el maestro) se
  rotulan «obra 1 / obra 2»: el `ide` del ERP no se imprime.
- Veredicto: al menos una obra y al menos una unidad; datos: nº de obras,
  código literal sí/no, unidades, unidades sin reclamaciones, reclamaciones,
  unidades cuyo `con.cod` no lleva cifras, unidades con **texto no reconocido**
  (posible nombre de persona → descarta `SHAREPOINT_NOMBRE_UNIDAD=nombre`, §4.6).

### 3 · Decisiones de diseño (y las añadidas a la spec)

1. **Nombres enmascarados por defecto (`-MostrarNombres` para el literal).** El
   encargo pide «ningún nombre de cliente en la salida por defecto», y el propio
   `design.md` §4.3 pone de ejemplo una carpeta `VILLA 05 - GARCÍA`.
   `ConvertTo-FormaSinNombres` conserva las palabras con cifras, las letras
   sueltas y un vocabulario de estructura (VILLA, BLOQUE, PORTAL, CHALET,
   PARTES, INCIDENCIAS, FIRMADOS…); el resto sale `<txt>`: `VILLA 05 - GARCIA`
   → `VILLA 05 - <txt>`, `0677 MIRASIERRA` → `0677 <txt>`. Es generosa a
   propósito. **Consecuencia**: para anotar en T2 el literal de la carpeta de
   obra (R36) hace falta `-MostrarNombres`, y por eso las líneas de §7 lo
   llevan.
2. **La máscara está copiada en los dos scripts**, no en el 08 (que es de F-009).
   `test_f013_t1_la_mascara_es_la_misma_en_los_dos` exige que las dos copias
   sean idénticas carácter a carácter.
3. **`-DesdeKeyVault` en el 23.** Las `GRAPH_*` salen de la sesión; con el
   interruptor, las que falten se leen con `az keyvault secret show` del vault
   de `00_vars_postventa.ps1` (nombres del mapa `$PostventaAppSettingsSecretas`,
   ninguno escrito en el script), capturadas en memoria. Si aun así falta
   alguna, se pide por consola (el secreto, como `SecureString`). Motivo: una
   línea `$env:GRAPH_CLIENT_SECRET = "..."` tecleada **queda en disco**, en el
   historial de PSReadLine.
4. **Reglas de casado provisionales en PowerShell.** Para medir antes de que
   exista el dominio (bloque 0) el 23 lleva una traducción directa de §4.1
   (obra: literal o código + blanco), §4.2 (tramo: igualdad de clave) y §4.5
   (parecidas). Lo dice en su cabecera y en su salida. **T14 las sustituye**
   por las del dominio vía `Invoke-PythonDelServicio`.
5. **`-CarpetaObra` y `-MaxCarpetasObra`.** Si la regla no encuentra la carpeta
   de la obra (o Posventa usa otra grafía), T2 puede forzar el literal y medir
   igual. Se recorren como mucho 5 carpetas de obra (casan + parecidas).
6. **La biblioteca se casa por URL** (`webUrl`), luego por nombre, y si pide la
   de por omisión y no casa ninguna, **la biblioteca por defecto del sitio**
   (`/sites/{id}/drive`). Si se pega la URL de la biblioteca
   (`…/Shared%20Documents/Forms/AllItems.aspx`) o un enlace de compartir
   (`/:f:/r/sites/…`), se entiende. Dice siempre por qué regla la eligió.
7. **Versionado**: Graph v1.0 no expone el ajuste de la biblioteca; se mira
   `/items/{id}/versions` de un fichero de una hoja: >1 versión → «sí»; 1 →
   «no concluyente».
8. **Del host del inquilino solo se imprime la ruta**; ni el `nextLink` (lleva
   el ID de la biblioteca) ni la URL de ninguna llamada fallida.

### 4 · Desviación respecto a la spec: **sin BOM**

T1 (`tasks.md:26-27`) y `design.md` §11 (`:701`) piden «UTF-8 con BOM y CRLF».
Los scripts salen **ASCII puro, CRLF y sin BOM**, como los otros 25 de
`infra/`. Motivo, **medido**: con BOM, `bash harness/init.sh` cayó en rojo
porque `tests/test_f010_prompt_keys_infra.py:77` lee **todos** los `.ps1` de
`infra/` con `encoding="ascii"` y la suite no llegaba ni a recolectar
(`UnicodeDecodeError: 'ascii' codec can't decode byte 0xef in position 0`).
`docs/CONVENTIONS.md` admite «excepciones documentadas», y `infra/` lo es de
hecho: ninguno de sus 25 scripts lleva BOM. Un fichero ASCII ya es UTF-8
válido y PowerShell 5.1 lo lee igual con o sin BOM.

No se ha tocado el test de F-010 (es de otra feature). **Para el líder**: si
se quiere BOM en `infra/`, el cambio es `encoding="utf-8-sig"` en ese test (y
revisar los demás que leen `.ps1` como `ascii`: `test_f006_scripts_infra.py`,
`test_f010_scripts_infra.py`), y probablemente enmendar T1/§11. El test de F-013
lo deja escrito con nombre: `test_f013_t1_sin_bom_como_el_resto_de_infra`.

Nota sobre el CRLF: el índice de git guarda LF en **todo** `infra/` y el CRLF
lo pone `core.autocrlf=true` al hacer checkout (`git ls-files --eol`:
`i/lf w/crlf`). El test de CRLF mira el árbol de trabajo, así que depende de esa
configuración, igual que el resto de `infra/`. Un `.gitattributes` con
`*.ps1 text eol=crlf` lo fijaría en cualquier máquina; no se ha añadido
(fuera de T1, afecta a todos los scripts; candidato también para `arnes-base`).

### 5 · Verificación

**Fase RED** — test escrito antes que los scripts. Comando exacto:

```
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f013_scripts_infra.py -q -p no:cacheprovider
```

Salida real (resumen y una traza; las 40 fallan por lo mismo):

```
E       FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\pgris\\PycharmProjects\\postventa-incidencias\\infra\\24_ubicacion_sigrid.ps1'
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\pathlib.py:1013: FileNotFoundError
=========================== short test summary info ===========================
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_los_dos_scripts_existen[23_destino_posventa.ps1]
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_los_dos_scripts_existen[24_ubicacion_sigrid.ps1]
FAILED tests/test_f013_scripts_infra.py::test_f013_t1_utf8_con_bom[23_destino_posventa.ps1]
[...]
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_el_de_graph_solo_hace_get_mas_el_token
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_el_de_graph_no_nombra_nada_que_suba_o_cree
FAILED tests/test_f013_scripts_infra.py::test_f013_r27_az_solo_para_leer_del_key_vault
[...]
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_el_de_sigrid_solo_lee_por_sql_read
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_consulta_va_parametrizada
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_consulta_recorre_upv_hasta_la_obra
FAILED tests/test_f013_scripts_infra.py::test_f013_r32_la_cabecera_avisa_del_texto_libre
40 failed, 4 passed in 1.69s
```

Los 4 que pasaban en RED son los **controles negativos** de los patrones
(host, verbos, SQL), que no dependen de los scripts. `test_f013_t1_utf8_con_bom`
se renombró después a `…_sin_bom_como_el_resto_de_infra` (§4).

**GREEN** — el mismo comando: `44 passed in 0.29s`.

**Mutantes a mano** (la campaña del arnés no muta PowerShell). Inyectados en los
ficheros reales, uno a uno, con el test lanzado y el fichero restaurado byte a
byte (`cmp`) después:

| # | Mutante | Resultado |
|---|---|---|
| M1 | un `Invoke-RestMethod -Method Post` en `Get-Hijos` (crear carpeta) | **muere**: 2 failed |
| M2 | guardar el nombre de los ficheros en la lista de carpetas | **muere**: 1 failed |
| M3 | un `UPDATE dbo.con` en la consulta del 24 | **muere**: 1 failed |
| M4 | `Write-Identificadores` sin el `if ($MostrarIdentificadores)` | **muere**: 1 failed |
| M5 | el 24 con BOM | **muere**: 2 failed |

**PowerShell 5.1 real** (`5.1.26100.9549`), sin red:

- `Parser::ParseFile` de los dos: **0 errores de sintaxis**.
- `-WhatIf` de los dos, lanzados **desde `%TEMP%`** (comprueba el `chdir`):
  salida 0, «no se ha llamado a nada». El 23 descompone bien la URL de una
  biblioteca (`/sites/Postventa` + `Shared Documents`) y no imprime el host.
- **Ensayo completo con datos inventados**: una copia de los dos scripts en el
  scratchpad, con un `08` de mentira que carga el real y sustituye **solo**
  `Invoke-RestMethod`, `Invoke-SigridLectura`, `Get-SigridDestino` y
  `Get-SigridClave` (el falso `Invoke-RestMethod` lanza una excepción ante
  cualquier verbo que no sea `GET` o el token). Resultado del 23 (salida 0,
  `PASA`): paginación seguida (dos páginas), 18 llamadas, **todas `GET`** salvo
  el token; `0677 MIRASIERRA` casa, `0677-ANEXO` y `LISTADO 677` salen
  parecidas, `06770 NO` y `0680 OTRA` no; `PARTES DE INCIDENCIAS` parecida;
  unidades: `VILLA 05` con hoja y 3 ficheros **contados**, `VILLA 05 - <txt>`
  con hoja parecida, `VILLA 07` sin hoja, `VILLA <txt>` sin cifras y con hoja
  ambigua; número repetido `5`; versionado «sí (4 versiones)». Con
  `-MostrarIdentificadores` sale el bloque de IDs con el aviso de Key Vault;
  con `-MostrarNombres`, los literales. Resultado del 24 (salida 0, `PASA`):
  parámetros enviados `708 | 0677 | 677`; la unidad con un nombre inventado en
  `con.res` sale `Villa 7 - <txt> <txt>` y cuenta como «texto no reconocido»;
  `con.res` nulo → `(nulo)`; la segunda obra, guardada como `677 `, sale con
  «literal: NO».

**`bash harness/init.sh`**: en verde — **3.283 passed, 35 skipped en 110,48 s**;
PUERTA COBERTURA N/A (sin líneas Python de producción).

### 6 · Qué queda fuera y qué falta

- **Fuera de T1, a propósito**: la columna «resolvería / crearía (nombre) /
  bloquearía» (R28 completa) es **T14**, con la regla del dominio; hoy el 23 dice
  casan / parecidas / ambigua con reglas provisionales y, si no hay nada, «el
  sistema crearía la carpeta de obra (nombre: T14)».
- El 24 **no** tiene `-DesdeKeyVault`: usa el mecanismo del 08 (sesión o
  parámetro, y la clave por consola), el mismo con el que se lanzaron el 15, el
  16 y el 20.
- **Pendiente**: T2 y T3 (humano, §7) y la parada T4.

### 7 · Para el humano: T2 y T3 (MANUAL)

Las dos se lanzan **desde la raíz del repositorio**
(`C:\Users\pgris\PycharmProjects\postventa-incidencias`), en PowerShell. Ninguna
escribe nada. Se puede probar antes cada una añadiendo `-WhatIf` al final: no
llama a nada y dice qué variables faltan.

**T2 · qué necesita la sesión.** Las tres `GRAPH_*`: `GRAPH_TENANT_ID`,
`GRAPH_CLIENT_ID` y `GRAPH_CLIENT_SECRET`. **No hay que ponerlas a mano**: con
`-DesdeKeyVault` el script las lee del Key Vault del proyecto
(`graph-tenant-id`, `graph-client-id`, `graph-client-secret`) con la CLI de
Azure, en memoria, sin imprimirlas ni escribirlas. Requisitos: `az login` hecho
en esa consola y permiso para **leer secretos** de ese vault. Si no lo hay, el
script pide lo que falte por consola (el secreto, oculto). Lo que **no** hay que
hacer es teclear `$env:GRAPH_CLIENT_SECRET = "..."`: esa línea se guarda en disco,
en el historial de PSReadLine.

```
powershell -ExecutionPolicy Bypass -File infra\23_destino_posventa.ps1 -UrlSitio "<URL del sitio Postventa>" -CodigoObra 0677 -DesdeKeyVault -MostrarNombres
```

**T3 · qué necesita la sesión.** La raíz de la pasarela en
`$env:SIGRID_API_BASE_URL` (como en los guiones de F-009 y F-012); la clave de
`sigrid-api` la pide el script, oculta, si no está en `$env:SIGRID_API_KEY`. La
base va en la línea.

```
$env:SIGRID_API_BASE_URL = "<la raiz de la pasarela>"
```

```
powershell -ExecutionPolicy Bypass -File infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -MostrarNombres
```

`-MostrarNombres` va en las dos porque T2 tiene que anotar el **literal** de la
carpeta de obra (R36) y T3 tiene que ver si `con.res` lleva nombres de persona
(§4.6). Lo que se anote en `progress/explore_F-013.md` va **sin identificadores
y sin nombres de cliente**; sin `-MostrarNombres`, la salida ya sale
enmascarada y se puede pegar tal cual. Con `-MostrarIdentificadores` el 23
imprime los ID del sitio y de la biblioteca **solo** para cargarlos en Key
Vault con `cargar_secretos_postventa.ps1 -Solo`.

### 8 · Para el líder: lo que ha quedado desfasado en la spec (no se ha tocado)

Desde que se escribió la spec se cerraron y desplegaron F-031, F-033 y F-034, y
el 2026-09-23 `desplegar_backend.ps1` pasó a dejar **abiertas por defecto** las
dos ventanas de escritura. Repaso con fichero y línea, **sin arreglar nada**:

1. **El corte, con las ventanas abiertas por defecto (lo más serio).**
   `design.md:487-496` (§7.3, pasos 4–6) y `tasks.md:192-205` (corte, pasos 4,
   5 y 5 bis) dan por hecho que, tras desplegar con
   `$EstructuraArchivo = "posventa"`, `ARCHIVO_HABILITADO` está cerrada y se
   abre «solo para el parte autorizado» (R33, `requirements.md:471`; R42,
   `:477`). Hoy `desplegar_backend.ps1:179-189` y `:489-496` la dejan
   **abierta**, y el comentario dice que Posventa ya usa el servicio en real:
   el primer archivado en la biblioteca de Posventa sería **el de cualquier
   usuario**, no el autorizado, y con `SHAREPOINT_CREAR_CARPETAS` encendido por
   omisión (D-4) podría **crear carpetas** antes de R42. El runbook tiene que
   decir cómo: `-VentanasCerradas` (cierra también la del ERP, que Posventa usa),
   cerrar solo la de archivo con `22_ventana_archivo.ps1` justo después, o
   desplegar primero con `SHAREPOINT_CREAR_CARPETAS=false`. Decisión del humano.
2. **Línea citada vieja.** `design.md:116` apunta a
   `infra/desplegar_backend.ps1:430`; `SHAREPOINT_CARPETA_BASE=Postventa` está
   hoy en **`:497`**.
3. **El orden del paso de archivo.** `design.md:370-378` (§5, tabla): la fila 3
   dice «L1 … **inerte** hoy; F-033», y ya no lo es; y falta el paso **1 bis**
   de F-031 (cotejo de códigos declarados). El orden real, en
   `application/pipelines/paso_archivo.py:222-248` y `:273-294`, es: puerta →
   cotejo → nombrado desde lo guardado → L1 → traza previa → carpeta → buscar →
   subir → traza final. El resolutor tiene que ir **después de L1** (si no, un
   parte ya archivado llamaría a Sigrid y listaría carpetas, contra lo que T15
   comprueba para R25) y **antes de la traza previa** (R22).
4. **De dónde salen los códigos.** `design.md:524-532` (§8.2) dice que F-013 usa
   `codigo_obra` y `numero_incidencia` «tal y como llegan al paso
   (`ctx.extraccion`)». Desde F-031 el paso los toma de `codigos_guardados(ctx)`
   (`paso_archivo.py:276`), y `tests/test_f031_alcance_cerrado.py:540-571`
   (R29, **se comprueba siempre**, sin git) **prohíbe** cualquier acceso a
   `.extraccion` en `paso_archivo.py`. El resolutor tiene que recibir los
   códigos **guardados**. El riesgo residual de §8.2 («un cuerpo que mienta en
   los dos») lo cerró F-031, y la recomendación de orden de `:534-538` ya se
   cumplió. El título `design.md:501` («F-033 (L1 inerte)») también se ha
   quedado viejo (la nota de `:510-514` lo matiza, el título no).
5. **Los tests que T10 tiene que mantener en verde.** `tasks.md:85-89` nombra
   `test_f006_*` y `test_f019_*`. Faltan los de F-031, F-033 y F-034, que fijan
   `paso_archivo.py`: F-031 R29 (arriba); F-033
   `NOMBRES_NUEVOS_Y_DONDE_VIVEN` (`tests/test_f033_alcance_cerrado.py:294-302`:
   `drive_id_vigente` solo puede vivir en `paso_archivo.py` y `archivar.py`; si
   el resolutor lo necesitara en `destino_archivo.py`, rompe); y F-034 R26
   (`tests/test_f034_alcance_cerrado.py:638`, compara `paso_archivo.py` con la
   base de **su** rama; debería saltarse fuera de ella, pero conviene
   comprobarlo al primer cambio del bloque 2).
6. **T15 y la precondición del bloque 5 ya se cumplen.** `tasks.md:121-126`
   («rebasar sobre `dev` con F-033… si F-033 no está mergeada, `blocked`») y
   `tasks.md:14-15`: F-033 está en `dev` y la rama sale de `dev` (`fadb678`).
   El rebase es trivial; T15 se puede hacer cuando toque sin esperar a nada.
7. **H-3 de F-034, sin sitio en la spec.** `progress/current.md:104-109`:
   `exigir_parte_archivado` (`application/pipelines/puerta_de_estado.py:185`)
   mira el **estado** de la traza pero no su **biblioteca**; un parte archivado
   en IT pasa la puerta del gráfico y del cierre igual que uno de Posventa. Con
   §9 bis (lo de IT se olvida) seguramente es lo querido, pero la spec de F-013
   no lo dice en ningún sitio. Decisión del humano, o una línea en §9 bis.
8. **Añadidos al 23 que la spec no nombra** (`design.md:439-464`, §7.1):
   `-MostrarNombres`, `-DesdeKeyVault`, `-CarpetaObra`, `-MaxCarpetasObra` y los
   tres parámetros de tramos/base. Y el **sin BOM** de §4 frente a
   `tasks.md:26-27` y `design.md:701`. Si el líder los acepta, conviene reflejarlos
   en §7.1 y §11 antes del bloque 6 (T17 documenta los dos scripts).

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de T1 | `test_f013_scripts_infra.py`: **44 passed** en 0,29 s (RED: 40 failed, 4 passed) |
| Suite del proyecto (`bash harness/init.sh`) | **3.283 passed, 35 skipped** en **110,48 s** (api); front en verde (caché); arnés 62 passed en 6,17 s |
| Cobertura de las líneas cambiadas | **N/A**: `PUERTA COBERTURA: N/A (F-013 no cambia líneas Python de producción frente a dev)`. T1 solo añade PowerShell y un test |
| Mutación (arnés) | `python -m harness.mutacion --feature F-013` (informe al scratchpad, para no adelantar el de T20): **0 ficheros, 0 líneas de producción, 0 mutantes**. El arnés solo muta `.py` de producción; la campaña de la feature es T20 |
| Mutación (a mano, PowerShell) | **5 mutantes inyectados, 5 muertos, 0 supervivientes** (§5) |
| Sintaxis PowerShell 5.1 | `Parser::ParseFile`: 0 errores en los dos |

---

## Bloque 1 · T5–T7 · Configuración y dominio puro (2026-09-24)

**Alcance del encargo: solo el Bloque 1.** No incluye nada del Bloque 2 (puertos,
resolutor, paso). Sin DDL, sin escrituras contra ningún sistema,
`harness/features.json` sin tocar. Ningún test toca la red.

Commits: `77c62dd` (T5), `4d86c99` (T6, en rojo, con la traza en el mensaje),
`cd00118` (estilo de T5: ruff), `a941acf` (T7), `0783c54` (T7: cierre de los
supervivientes de la mutación, §5), más el de este informe.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/config/settings.py` | Cinco campos: `sharepoint_estructura` (`"por_obra"`), `sharepoint_carpeta_incidencias` (`"PARTES INCIDENCIAS"`), `sharepoint_carpeta_firmados` (`"PARTES FIRMADOS"`), `sharepoint_carpeta_firmados_alternativa` (`"PARTES FIRMADO"`) y `sharepoint_crear_carpetas` (`True`). **Ninguno** llamado `sharepoint_nombre_unidad`. Descripción de `sharepoint_carpeta_base` actualizada (vacía = raíz, solo en `posventa`) y una nota fechada en el comentario de F-006 que decía que F-013 sería «cambiar tres variables» |
| `services/postventa-api/infrastructure/sharepoint/fabrica.py` | `_problemas_de_estructura`: una estrategia que no sea **exactamente** `por_obra`/`posventa` (R3) y una base vacía —o de solo blancos o barras— en `por_obra` (R17) → `ConfiguracionSharePointIncompleta`. Va dentro de la puerta 3 (configuración), **antes** de construir el adaptador, y en el mismo mensaje que las variables que falten. El orden entorno → interruptor → configuración no cambia |
| `services/postventa-api/domain/models/destino_posventa.py` (nuevo) | El dominio de `design.md` §2.1 y §4 (lista abajo). Solo biblioteca estándar y `nombrado.py` |
| `services/postventa-api/domain/models/errores.py` | `DestinoNoResuelto(motivo, detalle, candidatas=())`, con `candidatas` convertida en tupla; un párrafo en la docstring del módulo (familia 409) |
| `services/postventa-api/tests/test_f013_fabricas.py` (nuevo) | 37 tests: R1, R3, R17, R49 |
| `services/postventa-api/tests/test_f013_destino_dominio.py` (nuevo) | 246 tests: las tablas de `design.md` §4.1, §4.2, §4.3, §4.5, §4.6 y §4.7 enteras, fila a fila, más R9, R13/R14, R17, R18/R19, R35 (los cuatro obligatorios y los del recuadro), R36–R39, R44, R46 y R50 |
| `specs/F-013-archivo-posventa/tasks.md` | T5, T6 y T7 marcadas `[x]` |

**Lo que expone `destino_posventa.py`**: `EstructuraArchivo`, `MotivoDestino`
(los 22 códigos de R18, lista cerrada), `UbicacionReclamacion`, `UnidadDeObra`,
`PATRON_CODIGO_UNIDAD`, `clave_de_unidad`, `numero_de_obra`, `carpetas_de_obra`,
`parecidas_de_obra`, `carpeta_con_nombre`, `parecidas_de_tramo`,
`carpetas_de_unidad`, `parecidas_de_unidad`, `nombre_de_obra_nueva`,
`nombre_derivado_de_unidad`, `nombre_de_carpeta_admisible`,
`obras_del_mismo_numero`, `unidades_que_casan` y `unir_ruta`.

**Los controles de alcance de F-031, F-033 y F-034, sin tocarlos**: en verde
(28 passed; los 15 skipped son los controles del diff, que viven en las ramas de
esas features). El módulo nuevo no nombra ninguno de los identificadores
vigilados de `design.md` §2.3: R44 compara con `normalizar_codigo` y
`numero_de_obra`, nunca con `es_el_mismo_codigo`. Nada de este bloque ha chocado
con ellos.

### 2 · Decisiones de diseño (y lo que la spec no fijaba)

1. **`EstructuraArchivo` nace en T5**, sola, en `destino_posventa.py`: la
   fábrica la necesita para validar (R3), y la spec la coloca en ese módulo
   (§3.1). La lista de valores no se duplica en la fábrica. Por eso la fase RED
   de T6 es un `ImportError` del **resto** de nombres, no del módulo.
2. **La estrategia en `settings.py` es `str`, no el enum**: si fuera un tipo
   cerrado, un valor mal escrito tumbaría `/health` al leer los ajustes. Quien
   la valida es la fábrica, como con el resto de lo de SharePoint. Y la
   comparación es **exacta**: ni blancos ni mayúsculas se «arreglan»
   (`" posventa"` y `"POSVENTA"` → error). Falla cerrado.
3. **Dos funciones que la lista de §2.1 no nombra**, y que R36 y R38 necesitan
   en el dominio (T6 pide sus tests aquí): `nombre_de_obra_nueva(codigo,
   con_res)` —`<código normalizado> <con.res colapsado>`— y
   `nombre_de_carpeta_admisible`, que **delega** en `nombrado.nombre_admisible`
   (importada, no copiada: `design.md` §4.6). Sin `con.res`, el nombre de la
   obra acaba en blanco y R38 lo rechaza con `nombre_carpeta_imposible`, en vez
   de inventar un nombre.
4. **`parecidas_de_tramo` recibe también `alternativa`**. La firma de §4.5 es
   anterior a R49. Sin ella, la partición se rompería en la hoja:
   `PARTES FIRMADO` casaría **y** sería parecida. Solo sirve para excluir.
5. **`obra_ref` fuera del `repr` de `UnidadDeObra`** (`field(repr=False)`),
   con test: §3.3 y R23 dicen que no se loguea. Así, un `log.info("%s", fila)`
   descuidado no lo saca.
6. **Parecida de obra con código no numérico**: la spec dice «igualdad de
   token literal». Aquí es «las palabras del código aparecen seguidas entre las
   del nombre», sin mayúsculas ni tildes. Con un código de una palabra es
   exactamente la igualdad de token; con uno con guion (`AD-01`) es la
   generalización natural. Es generosa, como pide §4.5: su error cuesta un 409.
7. **Las secuencias de cifras de las reglas amplias se buscan tras NFKD**: una
   cifra de ancho completo (`６７７ MIRASIERRA`) no casa por la estricta (solo
   cifras ASCII, como exige §4.1), pero **sí** es parecida. Es más generoso que
   el `re.findall` literal de §4.5, nunca menos.
8. **Números de la unidad para la regla amplia**: si el `con.cod` cumple el
   patrón de R37 (solo el patrón, sin exigir que su obra sea la del parte), se
   toma su `<n>`; si no, los números de su clave, como antes. En los dos casos
   se añaden los del `con.res`.
9. **`numero_de_obra` normaliza** el código (`normalizar_codigo`, idempotente):
   `" 06 77 "` → 677, coherente con F-032 (un blanco no forma parte del código).
10. **Un código de obra vacío no casa con nada ni se parece a nada, y un tramo
    configurado vacío tampoco**: guardas explícitas, con test. El resolutor no
    debería llegar ahí (el nombrado falla antes), pero una clave vacía casaría
    con carpetas como `---`.
11. **Tramos: igualdad por `clave_de_unidad`**, tal cual dice §4.2. Un efecto
    que conviene saber: la puntuación también separa, así que
    `PARTES-INCIDENCIAS` **casa** con `PARTES INCIDENCIAS` (tienen la misma
    clave). Es la regla escrita y no se ha restringido; si el líder la quiere
    más estricta, es una enmienda.

### 3 · Fase RED (traza real)

**T5**. Comando exacto, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_fabricas.py -q -p no:cacheprovider --tb=line
```

Salida real (extracto; líneas `E` y de fallo agrupadas):

```
E   KeyError: 'sharepoint_estructura'
E   KeyError: 'sharepoint_carpeta_firmados_alternativa'
E   AttributeError: 'Ajustes' object has no attribute 'sharepoint_crear_carpetas'
E   AttributeError: 'Ajustes' object has no attribute 'sharepoint_carpeta_firmados'. Did you mean: 'sharepoint_carpeta_base'?
tests\test_f013_fabricas.py:190: Failed: DID NOT RAISE ConfiguracionSharePointIncompleta      (x6, R3)
tests\test_f013_fabricas.py:289: Failed: DID NOT RAISE ConfiguracionSharePointIncompleta      (x5, R17)
tests\test_f013_fabricas.py:340: AssertionError: assert 'SHAREPOINT_ESTRUCTURA' in 'faltan variables para archivar en SharePoint: SHAREPOINT_DRIVE_ID. Se dicen los nombres y nunca los valores: uno de ellos es una credencial'
FAILED tests/test_f013_fabricas.py::test_f013_r3_estrategia_desconocida_falla_antes_de_construir_el_adaptador[otra]
FAILED tests/test_f013_fabricas.py::test_f013_r17_base_vacia_en_por_obra_es_error_de_configuracion[]
FAILED tests/test_f013_fabricas.py::test_f013_r49_la_alternativa_por_omision_es_la_de_villa_02
[...]
27 failed, 10 passed in 0.29s
```

Los 10 que ya pasaban en RED son los **controles positivos** (las dos
estrategias y la base con nombre construyen; la puerta del entorno sigue yendo
antes; la variable retirada no existe), que ya eran ciertos antes del cambio.
GREEN: **37 passed**.

**T6**. Comando exacto:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_destino_dominio.py -q -p no:cacheprovider
```

Salida real, completa:

```
_____________ ERROR collecting tests/test_f013_destino_dominio.py _____________
ImportError while importing test module '...\tests\test_f013_destino_dominio.py'.
tests\test_f013_destino_dominio.py:31: in <module>
    from domain.models.destino_posventa import (
E   ImportError: cannot import name 'PATRON_CODIGO_UNIDAD' from 'domain.models.destino_posventa' (...\domain\models\destino_posventa.py)
=========================== short test summary info ===========================
ERROR tests/test_f013_destino_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.51s
```

Commiteado así (`4d86c99`, con la traza en el mensaje). GREEN tras T7:
**238 passed** (246 tras los tests que añadió la mutación, §5). Que las aserciones muerden —y no solo el import— lo demuestra
la campaña de mutación de §5.

### 4 · Verificación

| Comando (desde `services/postventa-api`) | Resultado |
|---|---|
| `pytest tests/test_f013_fabricas.py` | **37 passed** |
| `pytest tests/test_f013_destino_dominio.py` | **246 passed** |
| `pytest tests/test_f031_alcance_cerrado.py tests/test_f033_alcance_cerrado.py tests/test_f034_alcance_cerrado.py -rs` | **28 passed, 15 skipped** (controles del diff de sus ramas), sin tocarlos |
| `pytest tests/test_f006_fabrica.py tests/test_f025_sin_dry_run_previo.py tests/test_f005_ajustes.py` (los vecinos de la fábrica y de los ajustes) | en verde (93 passed junto con el de T5) |
| `python -m ruff check` sobre los seis ficheros tocados | All checks passed (el aviso global de 61 es deuda previa) |
| `bash harness/init.sh` (estado final, tras `0783c54`) | **ENTORNO LISTO**: api **3.566 passed, 35 skipped en 146,37 s**; PUERTA COBERTURA **100,0 % de 178 líneas cambiadas** (178/178, umbral 80 %, nivel `critico`). La pasada anterior, tras `a941acf`: 3.558 passed en 108,20 s, 182/182 |

### 5 · Mutación

La campaña formal de la feature es **T20** (bloque 7), y su informe,
`progress/mutacion_F-013.md`. Aquí se ha lanzado la del arnés sobre lo que
lleva la rama, **con el informe en el scratchpad** para no adelantar el de T20
(el mismo criterio que en T1). Alcance recalculado por la herramienta: rama
`fadb678..feature/F-013-archivo-posventa`, 4 ficheros de producción
(`settings.py`, `destino_posventa.py`, `errores.py`, `fabrica.py`).

**Primera pasada** (`python -m harness.mutacion --feature F-013`, 8 workers,
sobre `a941acf`): **56 mutantes, 47 muertos, 9 supervivientes**, 0 timeouts,
1.862,4 s. Análisis, uno a uno:

| # | Línea y mutación | Análisis | Qué se hizo |
|---|---|---|---|
| 1 | `destino_posventa.py:240` `len(recortado) > len(codigo)` → `>=` | **Equivalente**: se evalúa solo si `recortado != codigo` y empieza por `codigo`, así que ya es más largo. La guarda era redundante | Se quita la guarda (con un comentario de por qué el índice existe) |
| 2 | `:275` `range(len - largo + 1)` → `range(len + largo + 1)` | **Equivalente**: las ventanas de más dan cortes más cortos, que no pueden ser iguales a `buscadas` (no vacía) | `_contiene_seguidas` pasa a ser una búsqueda de texto con las palabras unidas por un blanco (las palabras no llevan blancos): sin aritmética |
| 3 | `:275` `… + 1` → `… + 2` | **Equivalente**, por lo mismo | Íd. |
| 4 | `:354` `endswith("S") and len > 1` → `or` | **Hueco real**: ningún test tenía una palabra de tramo **sin** `S` final (`FIRMADOS` e `INCIDENCIAS` acaban en `S`) | Test nuevo, `test_f013_r35_la_palabra_del_tramo_sin_su_s_final` (`ARCHIVO`: se usa entera) |
| 5 | `:354` `len > 1` → `>= 1` | **Hueco real** en la guarda del prefijo vacío (palabra que es solo `S`) | Íd. (`PARTES S`) |
| 6 | `:354` `len > 1` → `> 2` | **Hueco real**, una palabra de dos letras acabada en `S` | Íd. (`HOJA OS`) |
| 7 | `:355` `[:-1]` → `[:-2]` | **Hueco real**: se quita exactamente una `S` | Íd. (`CLASES` → `CLASE`, y `CLAS` no es parecida) |
| 8 | `:381` `not clave or not any(…)` → `and` | **Hueco real**: ningún test tenía una carpeta **sin número** que casara por la regla 1 o fuera sufijo del nombre. `not clave` era redundante (una clave vacía no tiene números) | Test nuevo `test_f013_r11_sin_numero_no_casa_aunque_sea_sufijo_del_nombre` y se quita `not clave` |
| 9 | `:386` `len(clave) <= len(nombre)` → `<` | **Hueco real**: ningún caso con la carpeta igual al `con.res` entero (el sufijo trivial de R39). La guarda de longitud era redundante (un corte más largo que el nombre da el nombre entero, distinto de la clave) | Tests nuevos `…_la_carpeta_con_el_nombre_entero_de_la_unidad_casa` y `…_una_carpeta_mas_larga_que_el_nombre_no_casa`, y se quita la guarda |

Las 4–7 se cierran además reescribiendo la línea como
`clave_buscada[-1].removesuffix("S") or clave_buscada[-1]`, sin enteros ni
comparaciones. **Comprobado a mano antes de simplificar**: cada superviviente
del 4 al 9, reinyectado en el fichero real (y el fichero restaurado byte a byte
después, `cmp`), lo mata al menos uno de los tests nuevos. El 6 sobrevivía a
la primera versión de esos tests y hubo que añadirle la fila `HOJA OS`.
Commit `0783c54`: sin cambio de comportamiento, 246 tests del dominio en verde.

**Segunda pasada** (misma orden, 8 workers, sobre `0783c54`, con el árbol
limpio): **43 mutantes, 43 muertos, 0 supervivientes, 0 timeouts**, 3.511,9 s.
Los 40 timeouts de la pasada paralela se repasaron en serie y los 40 salieron
muertos (el repaso mide el mutante y no la carga de la máquina). Informe
generado: en el scratchpad, `mutacion_F-013_bloque1_v2.md`; **no** se ha
escrito `progress/mutacion_F-013.md`, que es de T20.

### 6 · Qué queda fuera y qué falta

- **Fuera, a propósito (Bloque 2 en adelante)**: los puertos
  `ExploradorBibliotecaPort` y `UbicacionPort`, los dobles y el árbol medido
  como dato compartido (T8); el resolutor, que es quien convierte lo que
  devuelve este dominio en los 409 de `MotivoDestino`, y el caso de conjunto de
  las 15 unidades (T9); el paso (T10). Nada de este bloque se usa todavía
  desde producción: `destino_posventa.py` solo lo importa la fábrica (por
  `EstructuraArchivo`) y `SHAREPOINT_ESTRUCTURA` sigue valiendo `por_obra` por
  omisión, así que el comportamiento desplegable no cambia.
- **No se ha tocado** `.env.example` ni `local.settings.json.example` con las
  variables nuevas: la spec no lo pide en T5 y T17 es la tarea de
  documentación. Si el líder quiere que figuren, es una línea por variable.
- **Para el líder, sin bloquear**: la decisión 11 de §2 (`PARTES-INCIDENCIAS`
  casa por la clave de §4.2) y la 6 (parecida de un código no numérico con
  varias palabras). Las dos siguen lo escrito, o su generalización más
  directa; si se quieren de otra forma, es una enmienda con test.
- **Verificaciones MANUAL**: ninguna en este bloque.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests del bloque | `test_f013_fabricas.py` **37 passed** (RED: 27 failed, 10 passed); `test_f013_destino_dominio.py` **246 passed** (RED: `ImportError` en la recogida) |
| Controles de alcance de F-031, F-033 y F-034 | **28 passed, 15 skipped** (los del diff, fuera de sus ramas), sin tocarlos |
| Suite del proyecto (`bash harness/init.sh`, estado final) | api **3.566 passed, 35 skipped en 146,37 s**; front en verde (caché); arnés 62 passed en 5,54 s |
| Cobertura de las líneas cambiadas | **`PUERTA COBERTURA: 100.0% de 178 líneas cambiadas cubiertas (178/178, umbral 80%, nivel critico)`** |
| Mutación, primera pasada (8 workers) | 56 generados, 47 muertos, **9 supervivientes**, 0 timeouts, 1.862,4 s; los 9 analizados arriba |
| Mutación, segunda pasada (8 workers) | **43 generados, 43 muertos, 0 supervivientes**, 0 timeouts (40 repasados en serie, todos muertos), 3.511,9 s |
| Mutantes a mano | supervivientes 4–9 reinyectados contra los tests nuevos: todos mueren (el 6, tras añadir la fila `HOJA OS`) |
| ruff sobre los ficheros tocados | All checks passed |

---

## Bloque 2 · T8 y T9 hechas; **T10 BLOQUEADA** (2026-09-24)

**Alcance del encargo: solo el Bloque 2** (T8–T10). Sin DDL, sin escrituras
contra ningún sistema, `harness/features.json` sin tocar (lo pidió el líder
expresamente, así que la feature **no** se ha marcado `blocked` en el JSON:
lo decide el líder). Ningún test toca la red.

Commits: `8bfb964` (T8), `560d88f` (T9), `821b27d` (T9: superviviente de la mutación), más el de este informe.

### 0 · Por qué T10 está bloqueada (lo primero que hay que leer)

T10 pide añadir a `paso_archivo` el parámetro opcional `resolver_destino`
(`tasks.md` T10; `design.md` §2.2: «Parámetro opcional `resolver_destino`») y,
en la misma línea de verificación, que
`pytest tests -k "f006 or f019 or f031 or f032_alcance or f033 or f034"` siga en
verde **sin tocar** esos tests. Las dos cosas no pueden ser verdad a la vez:

`tests/test_f033_l1_desde_el_almacen.py:685`,
`test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar`, fija la firma
**entera** de `paso_archivo` con un `==` sobre el conjunto de parámetros, a
propósito (su docstring: *«lo que R21 exige es que **la firma entera** esté a
la vista, de modo que cualquier parámetro nuevo obligue a mirar si abre una
puerta»*). F-031 ya pasó por aquí el 2026-09-22 y **enmendó ese test** con un
recuadro fechado para añadir `codigos_declarados`.

**Comprobado, no supuesto.** Con el parámetro añadido de forma temporal
(`resolver_destino=None`, sin más cambios; el fichero se restauró byte a byte
y el árbol quedó limpio), comando:

```
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f033_l1_desde_el_almacen.py -q -p no:cacheprovider --tb=short
```

Salida real:

```
..........................................F.                             [100%]
================================== FAILURES ===================================
__________ test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar ___________
tests\test_f033_l1_desde_el_almacen.py:700: in test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar
    assert parametros == {
E   AssertionError: assert {'ahora', 'ar...vigente', ...} == {'ahora', 'ar...vigente', ...}
E
E     Extra items in the left set:
E     'resolver_destino'
E     Use -v to get more diff
=========================== short test summary info ===========================
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar
1 failed, 43 passed in 1.28s
```

No he improvisado ninguna salida (ni tocar el test de F-033, ni esconder el
resolutor en otro sitio para no cambiar la firma). **Opciones para el líder**:

- **(a) Recomendada.** Una tarea con nombre (p. ej. «T10 bis») que enmiende
  `test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar` añadiendo
  `resolver_destino` al conjunto, con recuadro fechado como el de F-031, y que
  enmiende la línea de verificación de T10 para decir que ese test **sí** se
  toca y por qué. El argumento de que no abre ninguna puerta está en la spec:
  en `posventa` L1 corta **antes** de resolver (R45, `design.md` §5 enmendado,
  fila 3), así que el resolutor no puede re-archivar un parte que consta
  archivado; solo elige la carpeta de uno que no lo está.
- (b) Sin cambiar la firma: una función aparte (`paso_archivo_posventa`) o
  inyectar el resolutor por otro camino. Es desviarse de `design.md` §2.2 y
  duplicar el orden del paso en dos sitios; no la recomiendo.

**Lo demás de T10 se ha revisado y no choca**: el control de F-031 R29 (el
paso no lee `ctx.extraccion`) y las tablas de nombres vigilados de F-031, F-033
y F-034 son compatibles con lo diseñado (el resolutor recibe dos cadenas y no
nombra ninguno de esos nombres; lo fija un test de T9), y
`test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza` se **salta** en esta
rama (`-rs`: los 7 controles del diff de F-034, SKIPPED por estar fuera de su
rama, igual que los 4 de F-031, los 4 de F-033 y los 5 de F-032).

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/domain/ports/biblioteca.py` (nuevo) | `ExploradorBibliotecaPort` (`runtime_checkable`) con **exactamente** `listar_carpetas(*, carpeta)` y `crear_subcarpeta(*, padre, nombre)` (R48, `design.md` §3.2). Docstrings con el contrato: solo carpetas, todas las páginas, `None` si no existe; un nivel, padre ausente = `ArchivoFallido`, «ya existe» = éxito |
| `services/postventa-api/domain/ports/ubicacion.py` (nuevo) | `UbicacionPort` (`runtime_checkable`) con `leer_ubicacion(*, codigo_reclamacion)` y `leer_unidades_del_numero(*, codigo_obra)` (`design.md` §3.3). Solo lecturas; los fallos suben (R41) |
| `services/postventa-api/application/pipelines/destino_archivo.py` (nuevo) | `resolver_destino_posventa`, `DestinoResuelto` y `TECHO_DE_FILAS_DE_SIGRID = 1000` (lista abajo) |
| `services/postventa-api/tests/utiles_destino.py` (nuevo) | `ExploradorFalso`, `UbicacionesFalsas`, el árbol medido de la 0677 y sus 15 unidades, y los montadores `arbol_0677`, `explorador_0677`, `ubicacion_0677`, `reclamacion_0677`, `ubicaciones_0677` |
| `services/postventa-api/tests/test_f013_puertos_y_dobles.py` (nuevo) | 42 tests: los dos puertos (métodos, firmas, palabra clave), los dos dobles y el árbol medido |
| `services/postventa-api/tests/test_f013_resolver_destino.py` (nuevo) | 134 tests del resolutor |
| `specs/F-013-archivo-posventa/tasks.md` | T8 y T9 marcadas `[x]`. T10, sin marcar |

**El resolutor, en el orden en que hace las cosas** (`design.md` §5 enmendado):

1. `leer_ubicacion(a_codigo_de_sigrid(numero_incidencia))` — R6 (la misma
   función que el cierre, importada: lo fija un test con `is`). Cero filas →
   `reclamacion_no_localizada`; varias → `reclamacion_ambigua`; una sin unidad
   (código **y** nombre vacíos) o sin obra → `reclamacion_sin_unidad` (R7).
2. R8 con `normalizar_codigo` a los dos lados → `obra_no_coincide`.
3. `leer_unidades_del_numero(codigo_obra normalizado)` — R44: primero el techo
   (≥ 1.000 filas → `unidades_sin_verificar`), después `obras_del_mismo_numero`
   ≠ 1 → `obra_numero_no_unico`. Se queda con las filas de **esa** obra.
4. Los cuatro niveles con un mismo recorrido (`_Camino.bajar`): lista **una
   vez**; >1 que casan → `<nivel>_ambigua`; 1 → baja; 0 y parecidas →
   `<nivel>_parecida`; 0 y 0 con crear apagado → `sin_carpeta_<nivel>`; 0 y 0
   con crear encendido → **anota**: compone (`nombre_de_obra_nueva`, el literal
   del tramo, `nombre_derivado_de_unidad` → `None` es
   `unidad_sin_nombre_derivable`), comprueba R38 (`nombre_carpeta_imposible`)
   y R46 (`nombre_no_casaria`, con la **misma** regla estricta del nivel), y
   desde ahí los niveles de debajo se anotan **sin listar**.
5. R50 en cuanto la unidad está elegida o anotada, y **antes** de listar
   dentro de ella → `unidad_carpeta_compartida`.
6. Devuelve `DestinoResuelto(destino=DestinoArchivo(carpeta, nombre_fichero),
   carpetas_por_crear=((padre, nombre), …))`. **No escribe** ni registra nada.

### 2 · Decisiones de diseño (y lo que la spec no fijaba)

1. **Un `None` de `listar_carpetas` es `ArchivoFallido`** (hueco de la spec:
   §5 no dice qué hacer). El resolutor solo lista la base y carpetas que el
   listado anterior acaba de dar, así que `None` es una base mal configurada o
   una carpeta borrada/renombrada entre dos llamadas. No es un nivel que
   falte: la base no se crea nunca (R15 habla de cuatro niveles), y crear en
   una carpeta que acaba de desaparecer sería crear a ciegas. Falla cerrado,
   sin subir ni crear, y el borde lo traducirá como cualquier `ArchivoFallido`
   (502). Dos tests lo fijan. **Para el líder**: si lo quiere como 409 con
   motivo propio, es una enmienda (la lista de R18 es cerrada).
2. **R7 «sin unidad»**: código **y** nombre de la unidad vacíos o en blanco;
   basta uno de los dos para que cuelgue de una unidad. Con solo el `con.cod`,
   R7 no para y lo que pasa después es lo que dice §4.3 (la regla 1 no casa
   `VILLA 05` con `0677.03VILLA 5.`; la carpeta lleva su número y es
   **parecida** → 409). Test con nombre.
3. **R35 antes que R16**: con crear apagado y una parecida, el motivo es
   `<nivel>_parecida` (dice lo que hay), no `sin_carpeta_<nivel>`. Es el orden
   del algoritmo de §5; hay un test por nivel.
4. **R44: techo antes que obras**, y «ninguna obra» es también
   `obra_numero_no_unico` (R44: «más de una obra, o ninguna»). Con 1.000 filas
   y dos obras sale `unidades_sin_verificar`: con la lista posiblemente
   cortada, «dos obras» tampoco se puede afirmar.
5. **R50 solo con las filas de la obra** de R44: las que el `LIKE` deja pasar
   de más (`1677`) no cuentan. Test con una `1677` que tiene su propia villa 5.
6. **La segunda lectura recibe el código normalizado** (`0677`, no ` 0677 `).
   El adaptador (T12) compone los patrones con `numero_de_obra`, que normaliza
   igual, así que es por claridad del registro de llamadas.
7. **Candidatas**: en R38 y R46, el nombre compuesto (es la carpeta
   implicada); en R50, la carpeta de unidad; en R7, R8, R16, R37 y R44,
   ninguna. Nunca un identificador (R23).
8. **El texto del 409 dice qué tiene que hacer «una persona»** en todos los
   motivos (R19) y **nunca** lleva el `con.res` de la unidad ni la referencia
   de obra (R23). Un test lo recorre sobre ocho motivos.
9. **Ni un log en el resolutor**: lo que haya que contar (R40, R47) lo cuenta
   el paso, y así el `con.res` de la unidad no puede salir de aquí.
10. **El nombre de la obra nueva usa el código del parte** (el guardado,
    normalizado; R36). Tras R8 es el mismo que el de Sigrid: el mutante que usa
    el de Sigrid es **equivalente** (§5).
11. **R46 en la obra es inalcanzable**: `<código> <con.res>` siempre empieza
    por el código y un blanco, y sin `con.res` R38 para antes. Se comprueba
    igual —el recorrido es el mismo para los cuatro niveles, y así lo dice
    R46—; en tramos sí es alcanzable (un tramo configurado sin palabras,
    `---`, es admisible pero no casaría: test). T20 lo tratará como mutante
    equivalente si aparece.
12. **Dobles**: los dos anotan cada llamada en `llamadas` y en un `registro`
    compartido con cadenas `explorador.listar_carpetas:<ruta>`,
    `ubicaciones.leer_ubicacion:<código>`… (el patrón de F-019). Los tests del
    resolutor comparan el registro **entero** en cada puerta, así que mover
    una comprobación un paso más tarde respecto de cualquier colaborador pone
    un test en rojo (§5, mutantes P1–P5). `_resolver` comprueba en **cada**
    test, también cuando se para, que el explorador no recibió ninguna
    `crear_subcarpeta`.
13. **Un solo árbol medido.** El de `utiles_destino.py` no sustituye a las
    constantes de `test_f013_destino_dominio.py` (T6 no se ha tocado): un test
    exige que sean **iguales** carácter a carácter, y el caso de conjunto usa
    la `TABLA_4_6` de T6 importada, así que la última columna de §4.6 vive en
    un solo sitio.
14. **El árbol de prueba se poda**: al quitar una carpeta de un listado, lo que
    colgaba de ella deja de existir (como en la biblioteca real). Lo enseñó el
    test de R39: sin podar, `VILLA 05` «ya existía» dentro de un
    `PARTES INCIDENCIAS` huérfano.

### 3 · Fase RED (traza real)

**T8**. Comando exacto, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_puertos_y_dobles.py -q -p no:cacheprovider
```

Salida real (extracto final):

```
tests\test_f013_puertos_y_dobles.py:30: in <module>
    from domain.ports.biblioteca import ExploradorBibliotecaPort
E   ModuleNotFoundError: No module named 'domain.ports.biblioteca'
=========================== short test summary info ===========================
ERROR tests/test_f013_puertos_y_dobles.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.57s
```

GREEN: **42 passed**. Que las aserciones muerden —y no solo el import— lo
demuestran los mutantes a mano de §5 (T8: 6 de 6 muertos).

**T9**. Comando exacto:

```
.venv/Scripts/python.exe -m pytest tests/test_f013_resolver_destino.py -q -p no:cacheprovider
```

Salida real (extracto final):

```
tests\test_f013_resolver_destino.py:37: in <module>
    from application.pipelines import destino_archivo
E   ImportError: cannot import name 'destino_archivo' from 'application.pipelines' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\application\pipelines\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f013_resolver_destino.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.85s
```

GREEN: primera pasada **125 passed, 1 failed** (el de R39 «desde
incidencias», por el árbol de prueba sin podar, decisión 14; el fallo era del
dato de prueba, no del resolutor); tras podar, **126 passed**; con los 7 tests
de «crear apagado + parecida» que añadí al buscar mutantes (decisión 3),
**133 passed**.

### 4 · Verificación

| Comando (desde `services/postventa-api` salvo el último) | Resultado |
|---|---|
| `pytest tests/test_f013_puertos_y_dobles.py` | **42 passed** |
| `pytest tests/test_f013_resolver_destino.py` | **134 passed** (133 + el del superviviente de la mutación, §5) |
| `pytest tests -k f013` (verificación de T8, sin regresiones) | **504 passed** |
| `pytest tests/test_f031_alcance_cerrado.py tests/test_f032_alcance_cerrado.py tests/test_f033_alcance_cerrado.py tests/test_f034_alcance_cerrado.py -rs` | **36 passed, 20 skipped** (todos los skipped son controles del diff de sus ramas), sin tocarlos |
| `python -m ruff check` sobre los seis ficheros nuevos | All checks passed |
| `bash harness/init.sh` (estado final, tras `821b27d`) | **ENTORNO LISTO**: api **3.742 passed, 35 skipped en 165,78 s**; PUERTA COBERTURA **100,0 % de 304 líneas cambiadas** (304/304, umbral 80 %, nivel `critico`). La pasada anterior, tras `560d88f` y con la campaña de mutación corriendo a la vez: 3.741 passed en 275,47 s |

### 5 · Mutación

**A mano** (script en el scratchpad que inyecta un cambio, lanza el test y
restaura el fichero byte a byte; comprobado al final de cada tanda):

- **Dobles (T8)**, contra `test_f013_puertos_y_dobles.py`: **6 de 6 muertos**
  (crear intermedias; «ya existe» no es éxito; listar no anota en el registro;
  carpeta ausente devuelve vacío; la segunda lectura no falla; no anota lo
  creado).
- **Resolutor (T9)**, contra `test_f013_resolver_destino.py`: **26 mutantes,
  23 muertos, 3 equivalentes**. Los cinco de **orden** (el punto 7 del
  reviewer), uno por colaborador:

  | # | Puerta movida | Resultado |
  |---|---|---|
  | P1 | R8 después de la segunda lectura de Sigrid | **muere** |
  | P2 | R44 después de construir el recorrido (sin listar) | sobrevive — **equivalente**: construir `_Camino` no llama a nadie |
  | P3 | R44 después de listar la raíz y elegir la obra | **muere** |
  | P4 | R50 después de listar dentro de la unidad | **muere** |
  | P5 | la segunda lectura antes que la primera | **muere** |

  Y los de lógica, M1–M21: bajo un nivel nuevo sí se lista; techo con `>`;
  sin R46; sin R38; crea la alternativa; sin obra no para; unidad a medias
  para; R8 sin normalizar; segunda lectura sin normalizar; R50 con filas de
  otras obras; R50 admite cero; sin forma ERP; `None` como vacío; crea con
  crear apagado; ignora parecidas; R44 admite ninguna; ambigua solo con tres;
  base sin `unir_ruta`; **el resolutor escribe** — **todos muertos**. Los dos
  equivalentes restantes: M19 (la carpeta final desde `camino.ruta` en vez de
  `unir_ruta(base, …)`: son el mismo valor por construcción) y M20 (la obra
  nueva con el código de Sigrid en vez del del parte: tras R8 son iguales
  normalizados, y `nombre_de_obra_nueva` normaliza).

**Del arnés** (`python -m harness.mutacion --feature F-013 --workers 8`,
informe en el scratchpad para no adelantar el de T20):
alcance recalculado por la herramienta, 7 ficheros de producción de la rama
(`destino_archivo.py`, `destino_posventa.py`, los dos puertos, `errores.py`,
`settings.py`, `fabrica.py`; 1.271 líneas). **68 mutantes, 66 muertos, 2
supervivientes, 0 timeouts** en 6.334,4 s (60 timeouts de la pasada paralela
—la suite corría a la vez que `init.sh`— repasados en serie: los 60, muertos).
Análisis de los dos:

| # | Línea y mutación | Análisis | Qué se hizo |
|---|---|---|---|
| 1 | `destino_archivo.py:89` `@dataclass(frozen=True)` → `frozen=False` en `DestinoResuelto` | **Hueco real**: ningún test comprobaba que el resultado no se pudiera reescribir entre resolver y crear (entre medias hay una traza previa y varias llamadas; lo que se comprobó —R38, R46, R50— dejaría de proteger nada) | Test nuevo `test_f013_t9_el_destino_resuelto_no_se_puede_reescribir`; reinyectado el mutante, **muere** (1 failed, 133 passed). Commit `821b27d` |
| 2 | `destino_archivo.py:102` `@dataclass(frozen=True)` → `frozen=False` en `_Nivel` | **Equivalente**: `_Nivel` es privado, sus cuatro instancias se construyen en línea en la llamada a `bajar` y nadie les asigna nada; `frozen` no tiene efecto observable | Nada; se deja `frozen=True` por coherencia con el resto de dataclasses del módulo |

Informe generado: en el scratchpad, `mutacion_F-013_bloque2.md`; **no** se ha
escrito `progress/mutacion_F-013.md`, que es de T20.

### 6 · Qué queda fuera y qué falta

- **T10, bloqueada** (§0). Sin ella, nada de este bloque se usa desde
  producción: el resolutor existe y está probado, pero ni el paso ni el borde
  lo llaman, y `SHAREPOINT_ESTRUCTURA` sigue en `por_obra` por omisión. El
  comportamiento desplegable no cambia.
- **Bloque 3** (T11 adaptador de Graph, T12 adaptador de Sigrid) no depende de
  T10 y se podría encargar en paralelo a la decisión del líder; T13 (el borde)
  sí necesita T10.
- **Fuera, a propósito**: logs de R40/R47 y la traza `error` con el motivo
  (R18), que son del paso (T10); el 409 del borde (T13).
- **Verificaciones MANUAL**: ninguna en este bloque.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests del bloque | `test_f013_puertos_y_dobles.py` **42 passed** (RED: `ModuleNotFoundError` en la recogida); `test_f013_resolver_destino.py` **134 passed** (RED: `ImportError` en la recogida) |
| `pytest -k f013` | **504 passed** en 4,62 s |
| Controles de alcance de F-031, F-032, F-033 y F-034 | **36 passed, 20 skipped** (los del diff, fuera de sus ramas), sin tocarlos |
| Suite del proyecto (`bash harness/init.sh`, estado final) | api **3.742 passed, 35 skipped en 165,78 s**; front en verde (caché); arnés 62 passed en 6,68 s |
| Cobertura de las líneas cambiadas | **`PUERTA COBERTURA: 100.0% de 304 líneas cambiadas cubiertas (304/304, umbral 80%, nivel critico)`** |
| Mutación a mano | T8: **6/6 muertos**; T9: **26 generados, 23 muertos, 3 equivalentes** (P2, M19, M20), 0 huecos |
| Mutación del arnés (8 workers) | **68 generados, 66 muertos, 2 supervivientes** (1 hueco real cerrado con test, 1 equivalente), 0 timeouts tras repasar 60 en serie, 6.334,4 s |
| Conflicto de T10 | `test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar`: **1 failed, 43 passed** con `resolver_destino` añadido a la firma (§0) |

## Bloque 2 (cierre) · T10 bis y T10 (2026-09-24)

**Alcance del encargo: solo T10 bis y T10**, con la opción (a) del humano
(enmienda de `tasks.md` en `309f445`). Sin DDL, sin escrituras contra ningún
sistema, `harness/features.json` sin tocar, sin push. Ningún test toca la red.

Commits: `c6ec311` (RED de T10), `e279907` (T10 + T10 bis juntos: la firma
nueva y la enmienda del test de F-033 en el mismo commit), `668145c`
(refuerzo de un test tras la mutación a mano), más el de este informe y
`tasks.md`.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/application/pipelines/paso_archivo.py` | Parámetro `resolver_destino` (opcional, por palabra clave, `None` por omisión). Sin él, el paso hace lo de F-006 (R2). Con él, el orden de `design.md` §5 enmendado (abajo). Nuevos: `AVISO_CARPETA_CREADA` (en `__all__`), el alias `ResolverDestino` y los privados `_sin_resolver`, `_resolver`, `_dejar_rastro_del_intento_pendiente` y `_crear_las_que_faltan`. `_subir` pierde `asegurar_carpeta`, que sube al cuerpo del paso (en `posventa` lo sustituyen las creaciones). Recuadro «Enmienda del 2026-09-24 (F-013)» en el docstring del módulo, y pasos 2, 3 bis y 5 en el de la función |
| `services/postventa-api/tests/test_f033_l1_desde_el_almacen.py` | **T10 bis**: `test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar` gana `"resolver_destino"` en el conjunto exacto (el `==` se mantiene) y un recuadro fechado 2026-09-24 (F-013) tras el de F-031. `git diff`: **10 inserciones, 0 borrados**, esas dos cosas y nada más |
| `services/postventa-api/tests/test_f013_paso_archivo_posventa.py` (nuevo) | 46 tests del paso con el resolutor (R4, R5, R15, R18, R20–R22, R40, R41, R45, R47, R48 y la composición) |
| `services/postventa-api/tests/test_f013_por_obra_intacto.py` (nuevo) | 19 tests de R2 con sus dos mitades: 5 sin `git` y 14 del diff (incluido el control de T10 bis) |
| `specs/F-013-archivo-posventa/tasks.md` | T10 bis y T10 marcadas `[x]`, con nota de commits |
| `progress/current.md` | Entrada de la sesión |

**El paso con `resolver_destino`, en su orden** (el orden es el requisito):

1. Si el `archivador` no es `ExploradorBibliotecaPort` → `TypeError` **antes
   de nada** (decisión 1).
2. Puerta de estado; cotejo de los declarados (F-031, 1 bis).
3. Nombre con `nombre_de_archivo` desde `codigos_guardados(ctx)` (R5). La
   carpeta aún no se conoce.
4. L1 desde el almacén. Si corta, compara con un `DestinoArchivo` cuya carpeta
   es **la de la propia traza** (`_sin_resolver`): deciden el nombre y la
   biblioteca, no la carpeta (R45). `_en_otro_destino`, intacta.
5. `_resolver`: llama al resolutor con `codigo_obra`, `numero_incidencia` (los
   guardados, dos cadenas) y `nombre_fichero`; nunca con `ctx`. Si levanta
   `DestinoNoResuelto`: log de R47 si la traza guardada de **este** parte
   estaba `pendiente` → traza `error` con el **código** del motivo y sin
   carpeta (R18) → `_registrar_si_no_se_aplico` (F-033 R19) → se relanza.
   Cualquier otro fallo (Sigrid, R41; `ArchivoFallido` del listado) sube **tal
   cual y sin traza**.
6. Aviso del intento anterior (F-033 R20) contra la carpeta **resuelta**.
7. Traza previa `pendiente`; `SIN_CAMBIOS` → la de la otra petición, sin crear
   ni subir.
8. `crear_subcarpeta` por cada `(padre, nombre)` de `carpetas_por_crear`, en
   orden y un nivel por llamada, con aviso `AVISO_CARPETA_CREADA` y log
   `F-013 carpeta creada: <ruta>` (WARNING) por carpeta (R40). Nunca
   `asegurar_carpeta` (R15). Un fallo aquí es `ArchivoFallido` como hoy:
   traza `error` con la carpeta resuelta, sin subir; el reintento vuelve a
   resolver y crea solo lo que falta (R39, con test).
9. `buscar`, `subir` (reemplazo), traza final: sin cambios.

### 2 · Decisiones de diseño (y lo que la spec no fijaba)

1. **Quién ejecuta `crear_subcarpeta`** (hueco de la spec). T10 bis fija la
   firma a los parámetros de antes **más `resolver_destino` y ninguno más**,
   así que el paso no puede recibir un explorador aparte. `design.md` §3.2:
   *«El adaptador de Graph implementa `ArchivoPort` **y** este puerto; la
   fábrica devuelve la misma instancia y el borde la pasa por los dos
   lados»*. El paso crea con **el mismo `archivador`**. Si llega un resolutor
   con un archivador que no es `ExploradorBibliotecaPort`
   (`runtime_checkable`), `TypeError` **antes de la puerta**: es un error de
   composición del borde, no del parte, y no hace ni una lectura. Anotado en
   `progress/current.md`. **Para T13**: el borde tiene que pasar la misma
   instancia como `archivador` y como `explorador` del `partial`.
2. **La traza `error` de R18 lleva `carpeta=None`** (la carpeta no se ha
   resuelto; la columna admite nulos, `05_archivos.sql`) y `motivo` como
   `str` plano del código (`str(MotivoDestino)`), sin el texto legible, que es
   para una persona y va en el 409 (T13).
3. **Los fallos del resolutor que no son `DestinoNoResuelto`** (Sigrid caída,
   R41; `None` del listado → `ArchivoFallido`, decisión 1 del bloque 2) suben
   **sin escribir traza**: aún no hay `pendiente` que cerrar, y una `error`
   con un motivo inventado diría menos que el 503/502 del borde. La tabla de
   §5 solo pide traza para `DestinoNoResuelto`.
4. **R47 se dispara con un `pendiente` de este `hash`**, sin comparar rutas
   (la de hoy no se conoce): deja carpeta, nombre, `hash` y el código del
   motivo; nunca el `drive_id`.
5. **R40 con nivel WARNING** en el logger del paso: es la línea que el runbook
   busca en el log (paso 8 del corte); con INFO se perdería según el nivel
   del host. El aviso nombra «la biblioteca de Posventa» y la ruta; ningún
   identificador.
6. **R45 con una traza sin carpeta** (`carpeta=None`): `_sin_resolver` da
   `None` a los dos lados y la carpeta tampoco decide. Test con nombre.
7. **En `por_obra`, L1 sigue comparando la carpeta** (F-033 R14): lo que
   relaja R45 es solo de `posventa`. Test en `test_f013_por_obra_intacto.py`.
8. **Los controles del diff son tests**:
   `test_f013_t10_bis_de_los_tests_de_f033_solo_cambia_el_de_la_firma`
   compara con la base de la rama (`git merge-base dev HEAD`) cada función de
   `test_f033_l1_desde_el_almacen.py` con `ast.dump`: solo puede cambiar la de
   la firma, y su conjunto solo gana `resolver_destino`. Otro exige que
   ningún `test_f006_*`, `test_f019_*`, `test_f031_*`, `test_f032_*` ni
   `test_f034_*` aparezca en el diff, y de F-033 solo ese fichero. Y otro, que
   once piezas de F-019/F-033 de `paso_archivo.py` (`_en_otro_destino`,
   `_avisar_del_intento_anterior`, `_dejar_constancia_previa`…) sean las
   mismas sentencia a sentencia. Fuera de la rama, o ya mergeada, se saltan
   (patrón de F-032).

### 3 · Fase RED (traza real)

Comando exacto, desde `services/postventa-api`, con los dos ficheros nuevos
escritos y `paso_archivo.py` sin tocar (commit `c6ec311`):

```
.venv/Scripts/python.exe -m pytest tests/test_f013_paso_archivo_posventa.py tests/test_f013_por_obra_intacto.py -q -p no:cacheprovider --tb=short
```

Salida real de los tres casos centrales (orden de creaciones de R15, lo
archivado en IT de R45 y el control de T10 bis):

```
__ test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden __
tests\test_f013_paso_archivo_posventa.py:439: in test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden
    ctx = m.archivar()
          ^^^^^^^^^^^^
tests\test_f013_paso_archivo_posventa.py:196: in archivar
    return paso.paso_archivo(
E   TypeError: paso_archivo() got an unexpected keyword argument 'resolver_destino'
_ test_f013_r45_un_parte_archivado_en_it_no_llama_ni_a_sigrid_ni_a_la_biblioteca _
tests\test_f013_paso_archivo_posventa.py:873: in test_f013_r45_un_parte_archivado_en_it_no_llama_ni_a_sigrid_ni_a_la_biblioteca
    ctx = m.archivar(drive_id_vigente=DRIVE_POSVENTA)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f013_paso_archivo_posventa.py:196: in archivar
    return paso.paso_archivo(
E   TypeError: paso_archivo() got an unexpected keyword argument 'resolver_destino'
______ test_f013_t10_bis_de_los_tests_de_f033_solo_cambia_el_de_la_firma ______
tests\test_f013_por_obra_intacto.py:267: in test_f013_t10_bis_de_los_tests_de_f033_solo_cambia_el_de_la_firma
    assert ganados == {"resolver_destino"}
E   AssertionError: assert set() == {'resolver_destino'}
```

Resumen de los dos ficheros: **46 failed, 18 passed** (los 18 son la mitad de
R2 que ya se cumple hoy —el paso sin resolutor— y la composición de los
dobles). GREEN con el código: **63 passed, 1 failed** (el control de T10 bis,
que exige la enmienda del test de F-033); con T10 bis, **64 passed**; con el
refuerzo de §5, **65 passed** (46 + 19).

### 4 · Verificación

| Comando (desde `services/postventa-api`) | Resultado |
|---|---|
| `pytest tests/test_f033_l1_desde_el_almacen.py` (verificación de T10 bis) | en verde con el parámetro añadido; junto con los dos ficheros nuevos, **109 passed** |
| `git diff 309f445 -- tests/test_f033_l1_desde_el_almacen.py` | 10 inserciones: el recuadro y `"resolver_destino",`; nada más |
| `pytest tests/test_f013_paso_archivo_posventa.py` / `tests/test_f013_por_obra_intacto.py` | **46 passed** / **19 passed** (los 14 del diff se **ejecutan** en esta rama) |
| `pytest tests -k "f006 or f019 or f031 or f032_alcance or f033 or f034" -rs` (verificación de T10) | **750 passed, 20 skipped**. Los 20 SKIPPED son los controles del diff de otras ramas: 4 de F-031, 5 de F-032, 4 de F-033 y **7 de F-034**, entre ellos `test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza` («este control vive en feature/F-034-… mientras no esté mergeada»). Ninguno falla |
| `pytest tests -k f013` | **569 passed** |
| `python -m ruff check` sobre los cuatro ficheros tocados | All checks passed |
| `bash harness/init.sh` | ver «Evidencias» |

### 5 · Mutación

**A mano, de orden** (punto 7 del reviewer). Script en el scratchpad
(`mutantes_orden_t10.py`): copia desechable del servicio, sustitución exacta
en el `paso_archivo.py` de la copia, suite de los cuatro ficheros del paso
(`test_f013_paso_archivo_posventa.py`, `test_f013_por_obra_intacto.py`,
`test_f033_l1_desde_el_almacen.py`, `test_f006_paso_archivo.py`) y
restaurar. Base sin mutar y restaurada: 124 passed, 14 skipped (los del
diff, sin `git` en la copia). Comprobado al final: **árbol real intacto**.
Los tests comparan el registro compartido **entero** —repositorio,
archivador, explorador, ubicaciones y el log del paso, con un handler que
apunta cada línea—.

| # | Puerta movida (una por colaborador que precede) | Resultado | Test que lo caza |
|---|---|---|---|
| O0 | comprobación de composición después de la puerta | **muere** (tras el refuerzo) | `…archivador_que_no_crea_carpetas_no_se_toca_nada` |
| O1 | resolver antes de la puerta de estado | **muere** | `test_f013_r22_un_parte_no_aprobado_…` |
| O2 | resolver antes del cotejo (1 bis) | **muere** | `test_f013_r22_un_cuerpo_que_no_cuadra_…` |
| O3 | resolver antes del corte de L1 | **muere** | `test_f013_r45_un_parte_archivado_en_it_…` |
| O4 | aviso del intento anterior antes de resolver | **muere** | `test_f013_r22_el_aviso_…_compara_con_la_carpeta_resuelta` |
| O5 | traza previa (y aviso) antes de resolver | **muere** | `test_f013_r4_…_con_el_orden_entero` |
| O6 | crear carpetas antes de la traza previa | **muere** | `test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_…` |
| O7 | crear carpetas después de subir | **muere** | ídem |
| O8 | creaciones en orden inverso | **muere** | ídem |
| O9 | log de R47 después de la traza `error` | **muere** | `test_f013_r47_…_antes_de_la_traza_error` |
| O10 | aviso y log de R40 antes de `crear_subcarpeta` | **muere** | `test_f013_r15_…` |
| O11 | `DestinoNoResuelto` sin escribir la traza `error` | **muere** | `test_f013_r18_sin_destino_queda_la_traza_error_…` |

**12 de 12 muertos.** O0 **sobrevivía** en la primera pasada: el caso del
`TypeError` usaba dobles que no apuntan `consultar_situacion`, así que mover la
comprobación detrás de la puerta no se veía. **Hueco real**, cerrado en
`668145c` con un repositorio que apunta también la lectura (y un control de
que la apunta); reinyectado, muere.

**Del arnés** (`python -m harness.mutacion --feature F-013 --timeout 900 --workers 6`,
lanzada **después** de `init.sh` y sin nada más corriendo; informe en el
scratchpad, `mutacion_F-013_bloque2_cierre.md`, para no adelantar el de T20).
La herramienta **no** admite limitar el alcance a unos ficheros (lo calcula
del diff de la rama: 8 ficheros, 1.495 líneas); sí admite subir el timeout,
y se subió de 120 s a **900 s** por mutante con **6 workers** en vez de 8, por
lo del bloque 2 (60 timeouts con `init.sh` a la vez). Resultado: **73
mutantes, 72 muertos, 1 superviviente, 0 timeouts** en 2.216,7 s. De
`paso_archivo.py` generó **5** (los operadores de la herramienta son
comparaciones, lógicos, `not`, booleanos y enteros: no mueve sentencias, por
eso el orden se cubre a mano arriba): la comprobación de composición
(`and`→`or`, quitar el `not`) y las dos condiciones de R47 (`!=`→`==`,
`or`→`and` ×2): **los 5 muertos**.

| # | Línea y mutación | Análisis | Qué se hizo |
|---|---|---|---|
| 1 | `destino_archivo.py:102` `@dataclass(frozen=True)` → `frozen=False` en `_Nivel` | **Equivalente**, el mismo del bloque 2 (§5 de «Bloque 2», fila 2): `_Nivel` es privado, sus cuatro instancias se construyen en línea en la llamada a `bajar` y nadie les asigna nada | Nada; se deja `frozen=True` por coherencia. Pendiente de la aceptación del humano (nivel `critico`: cada superviviente, test o justificación aceptada) |

### 6 · Qué queda fuera y qué falta

- **Fuera, a propósito**: el borde (T13: `archivar.py` compone el `partial`
  con `explorador` = **el mismo** adaptador que el archivador, decisión 1; y
  `DestinoNoResuelto` → 409 en `function_app.py`), los adaptadores (T11, T12)
  y R25 desde el endpoint (T15). Hasta T13 nadie llama al paso con
  `resolver_destino`: el comportamiento desplegable **no cambia** (R2).
- **Siguiente**: Bloque 3 (T11 Graph, T12 Sigrid) y del 4 al 7.
- **Verificaciones MANUAL**: ninguna en este bloque.
- `progress/mutacion_F-013.md` no se ha escrito: es de T20.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de T10 | `test_f013_paso_archivo_posventa.py` **46 passed**; `test_f013_por_obra_intacto.py` **19 passed** (RED: **46 failed, 18 passed**, `TypeError: paso_archivo() got an unexpected keyword argument 'resolver_destino'`) |
| Test de T10 bis | `test_f033_l1_desde_el_almacen.py` en verde (con los dos nuevos, **109 passed**); diff de 10 inserciones |
| Controles de alcance (`-k "f006 or f019 or f031 or f032_alcance or f033 or f034" -rs`) | **750 passed, 20 skipped** (los del diff de otras ramas, `test_f034_r26_…` incluido), sin tocarlos salvo T10 bis |
| `pytest -k f013` | **569 passed** |
| Suite del proyecto (`bash harness/init.sh`, tras `668145c`) | api **3.807 passed, 35 skipped en 202,32 s**; front en verde (caché); arnés 62 passed en 10,29 s; **ENTORNO LISTO** |
| Cobertura de las líneas cambiadas | **`PUERTA COBERTURA: 100.0% de 347 líneas cambiadas cubiertas (347/347, umbral 80%, nivel critico)`** |
| Mutación a mano (orden) | **12 generados, 12 muertos** (1 hueco real, O0, cerrado con test en `668145c`) |
| Mutación del arnés (6 workers, timeout 900 s) | **73 generados, 72 muertos, 1 superviviente** (equivalente, analizado arriba), **0 timeouts**, 2.216,7 s; de `paso_archivo.py`, 5/5 muertos |

## Bloque 3 · T11 y T12 (2026-09-24)

**Alcance del encargo: solo T11 y T12** (los adaptadores). Nada de T13 en
adelante: ni el borde, ni `archivar.py`, ni `function_app.py`. Sin DDL, sin
escrituras contra ningún sistema, `harness/features.json` sin tocar, sin push.
Ningún test toca la red: dobles de transporte de `tests/utiles_sharepoint.py`
y `tests/utiles_sigrid.py`, con la guardia de red de `conftest.py` por debajo.

Commits: `7b7d0d1` (RED de T11), `d6ab81a` (T11), `7a3468b` (RED de T12),
`66327f7` (T12), `4da38a3` (dos tests tras la mutación del arnés), más el
de este informe.

### 1 · Qué cambió

| Fichero | Qué |
|---|---|
| `services/postventa-api/infrastructure/sharepoint/graph.py` | **T11.** `listar_carpetas` y `crear_subcarpeta` en `AdaptadorSharePointGraph`, que así cumple `ExploradorBibliotecaPort` **y** `ArchivoPort` con la misma instancia. Nuevos: `CONSULTA_DE_LISTADO`, `_pedir_pagina`, `_url_de_hijos` y los privados de módulo `_listado_fallido`, `_cuerpo_de_pagina`, `_carpetas_de`, `_pagina_siguiente`. Recuadro «Enmienda del 2026-09-24 (F-013 T11)» en el docstring del módulo. Las tres operaciones de F-006 y `_crear_carpeta`, **sin tocar** |
| `services/postventa-api/infrastructure/sigrid/consultas_ubicacion.py` (nuevo) | **T12**, puro: `SQL_UBICACION`, `SQL_UNIDADES_DEL_NUMERO`, `SQL_UNIDADES_DEL_CODIGO` (carácter a carácter de `design.md` §6.2 enmendado), `select_ubicacion`, `select_unidades_del_numero` (patrones desde `numero_de_obra`), `fila_a_ubicacion`, `fila_a_unidad` |
| `services/postventa-api/infrastructure/sigrid/ubicacion.py` (nuevo) | **T12**: `AdaptadorUbicacionSigridApi` (las dos lecturas de `UbicacionPort`), `exigir_entorno_con_ubicacion`, `RUTA_LECTURA = "/api/sql/read"`, `MAX_FILAS_UBICACION` (10) y `MAX_FILAS_UNIDADES` (1.000) |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | **T12**: `construir_ubicaciones(ajustes)` (entorno → configuración; **sin** `CIERRE_HABILITADO`) y recuadro fechado en el docstring del módulo |
| `services/postventa-api/domain/models/errores.py` | **T12**: `UbicacionNoDisponible(motivo)` (decisión 3, abajo) |
| `services/postventa-api/tests/test_f013_adaptador_graph_listado.py` (nuevo) | 43 tests de T11 |
| `services/postventa-api/tests/test_f013_ubicacion_sigrid.py` (nuevo) | 112 tests de T12 |
| `specs/F-013-archivo-posventa/tasks.md` | T11 y T12 marcadas `[x]` |
| `progress/current.md` | Entrada de la sesión |

**T11, lo que hace cada método:**

- `listar_carpetas(carpeta)`: `GET …/root/children` (raíz) o
  `…/root:/<ruta codificada>:/children` con `?$select=name,folder&$top=200`;
  sigue el `@odata.nextLink` **tal cual** hasta que no lo haya (R12); se queda
  con los elementos que son objeto, llevan la faceta `folder` y un `name` de
  texto, con el nombre tal y como existe (el doble blanco de `677  MIRASIERRA`
  incluido). `404` de la **primera** página → `None`; una tupla vacía si la
  carpeta existe sin subcarpetas (VILLA 04). Reintentos y errores con
  `_con_reintentos` de F-006. Una línea de log por listado:
  `F-013 carpetas listadas: carpeta=<ruta o (raíz)> carpetas=N paginas=N segundos=…`.
- `crear_subcarpeta(padre, nombre)`: `_crear_carpeta` de F-006 **tal cual**:
  un `POST` en el padre, `conflictBehavior=fail`, `409` tolerado (R39), y un
  padre ausente es el `404` de Graph → `ArchivoFallido` (R15). Ni `GET` previo
  ni tramos.

**T12, las dos lecturas:**

- `leer_ubicacion(codigo_reclamacion)`: `SQL_UBICACION` con
  `(SIGRID_TIP_RECLAMACION, código)`, `max_rows` 10; devuelve **todas** las
  filas mapeadas (0, 1 o varias: decide el dominio, R7).
- `leer_unidades_del_numero(codigo_obra)`: con número,
  `SQL_UNIDADES_DEL_NUMERO` y `('%<n>', '%[^0]%<n>')` —`('%677',
  '%[^0]%677')` para la 0677—; sin número, `SQL_UNIDADES_DEL_CODIGO` con el
  código normalizado. `max_rows` 1.000, el mismo número que
  `TECHO_DE_FILAS_DE_SIGRID` del resolutor (lo fija un test).
- Solo `POST <base>/api/sql/read`, con la clave en `x-functions-key`. Del
  cliente del cierre se **importan** `construir_cliente_http`, `ErrorDeSigrid`,
  `es_transitorio`, `CORRECTOS`, `ENTORNOS_CON_CIERRE` y `MAX_FILAS_LECTURA`;
  nada del adaptador del cierre, de `escrituras.py`, de `graficos.py` ni de
  `consultas.py` (un test lo fija con `ast`). Ni `ubicacion.py` ni
  `consultas_ubicacion.py` contienen `sql/write`, `concepto-grafico` ni
  `/api/sigrid`.
- Log: `F-013 ubicación leída en Sigrid: incidencia=… filas=N segundos=…` y
  `F-013 unidades leídas en Sigrid: obra=… filas=N segundos=…`. **Nunca**
  `obra_ref` ni el `con.res` de la unidad (test con un nombre inventado de
  persona dentro).

### 2 · Decisiones de diseño (y lo que la spec no fijaba)

1. **El adaptador de Graph es los dos puertos, comprobado sin nombrarlo.** Los
   tests de T11 construyen el adaptador con el ayudante `adaptador()` de
   `test_f006_adaptador_graph.py`, **importado**: ese fichero es uno de los dos
   autorizados por `test_f006_arquitectura.py` (R21) y siempre inyecta el
   cliente falso. Así ningún test de F-006 se toca (lo exige el control de
   diff de `test_f013_por_obra_intacto.py`) y el guardián no necesita otra
   excepción. Que la **fábrica** devuelve esa clase se fija con
   `fabrica_sharepoint.AdaptadorSharePointGraph is graph.AdaptadorSharePointGraph`
   e `issubclass(…, ExploradorBibliotecaPort)` / `ArchivoPort`, sin construir
   el adaptador real fuera de los ficheros autorizados. `construir_archivador`
   **no** se ha tocado: sigue anotada como `-> ArchivoPort`; **para T13**,
   el borde pasa esa misma instancia como `archivador` y como `explorador`
   (decisión 1 del cierre del bloque 2).
2. **El `nextLink` solo se sigue si empieza por `https://graph.microsoft.com/v1.0/`**
   (no lo pedía la spec). El token viaja en la cabecera de cada página; seguir
   un enlace a otro host se lo mandaría a un tercero. Si no apunta a Graph, o
   no es texto, o es vacío → `ArchivoFallido` sin pedirlo y sin decir adónde
   apuntaba. Tres tests.
3. **`UbicacionNoDisponible`, un error nuevo en `domain/models/errores.py`**
   (hueco de la spec; `design.md` §2.2 solo lista `DestinoNoResuelto` para ese
   fichero). R41 pide **503** cuando la lectura falla por red, tiempo o
   configuración, y §6.2 dice «503 (`ConfiguracionSigridIncompleta`/transitorio)»
   sin nombrar el tipo del fallo en ejecución. Los existentes no sirven:
   `CierreFallido` es del cierre y el borde de archivar no lo mapea (sería un
   500; en `/api/cerrar` es 502); `ConfiguracionSigridIncompleta` mentiría
   («falta configuración») ante un `503` de la pasarela; `ArchivoFallido` es
   502. **Para T13**: `function_app.py` tiene que mapear
   `UbicacionNoDisponible` **y** `ConfiguracionSigridIncompleta` a 503 en
   `/api/archivar` (hoy ninguno de los dos está en ese `except`). Los tests del
   resolutor y del paso (bloque 2) usaban `TimeoutError` como fallo de red; con
   el adaptador real, lo que sube es `UbicacionNoDisponible`, y el paso lo deja
   subir igual («cualquier otro fallo sube tal cual y sin traza»).
4. **La puerta del entorno de la ubicación levanta `ArchivoDeshabilitado`**,
   no `CierreDeshabilitado` (hueco de la spec: §6.2 dice «entorno `dev`/`pro`
   (la lista del cierre, importada, no copiada)» sin el tipo). La **lista** es
   `ENTORNOS_CON_CIERRE`, importada (test con `is`); el **error** es el de
   archivar, porque el de cierre diría que se ha intentado escribir en el ERP,
   y porque el borde de archivar ya traduce `ArchivoDeshabilitado` a 503.
   Está en la fábrica **y** en el constructor, como en los otros adaptadores.
5. **Una respuesta con `truncated: true` y menos filas de las pedidas no se
   devuelve** (`UbicacionNoDisponible`, no lo pedía la spec). El resolutor
   solo reconoce una lista cortada si llega a 1.000 (R44); si la pasarela
   tuviera un techo menor que el pedido (`MAX_ALLOWED_ROWS` es configurable,
   `sigrid_api.md` §4.1), llegaría cortada con, por ejemplo, 500 filas y el
   resolutor no vería la segunda obra. Con 1.000 filas cortadas se devuelven
   las 1.000, y el resolutor responde `unidades_sin_verificar` (test de punta a
   punta). La primera lectura con 10 filas cortadas se devuelve: son «varias»
   → `reclamacion_ambigua`.
6. **La primera lectura pide 10 filas** (`MAX_FILAS_LECTURA` del cierre,
   importado): basta con distinguir 0, 1 o varias, y cada fila de más es el
   nombre de una unidad que viaja sin necesidad.
7. **`obra_ref` es obligatorio**: una fila de unidades sin `obride` (o en
   blanco) es `ValueError` en el mapeo y `UbicacionNoDisponible` en el
   adaptador. Con el `JOIN` de §6.2 no puede venir nulo, pero si viniera, dos
   filas sin él contarían como una sola obra y esconderían la segunda (R44).
8. **Una fila tiene que ser lista o tupla de cuatro**: una cadena de cuatro
   letras se desempaquetaría en cuatro «columnas». El mensaje del error no
   lleva la fila (puede traer el nombre de la unidad o la referencia de obra).
9. **Los códigos se mapean a texto con `str()` y los nulos se quedan en
   `None`**; no se recortan: normaliza el dominio.
10. **Se registran el código de la incidencia, el de la obra, el número de
    filas y los segundos** de cada lectura: el tiempo de la segunda está
    **[NO MEDIDO]** en `design.md` §6.2 y lo mide el primer archivado real.

### 3 · Fase RED (traza real)

**T11.** Comando exacto, desde `services/postventa-api`, con el fichero de
tests escrito y `graph.py` sin tocar (commit `7b7d0d1`):

```
.venv/Scripts/python.exe -m pytest tests/test_f013_adaptador_graph_listado.py -q -p no:cacheprovider --tb=short
```

Salida real (extracto de los casos centrales):

```
___ test_f013_t11_el_adaptador_de_graph_es_archivador_y_explorador_a_la_vez ___
tests\test_f013_adaptador_graph_listado.py:117: in test_f013_t11_el_adaptador_de_graph_es_archivador_y_explorador_a_la_vez
    assert isinstance(adap, ExploradorBibliotecaPort)
E   assert False
E    +  where False = isinstance(<infrastructure.sharepoint.graph.AdaptadorSharePointGraph object at 0x0000012FA24D9AF0>, ExploradorBibliotecaPort)
_______________ test_f013_r12_sigue_el_next_link_hasta_agotarlo _______________
tests\test_f013_adaptador_graph_listado.py:206: in test_f013_r12_sigue_el_next_link_hasta_agotarlo
    listado = adap.listar_carpetas(carpeta="")
              ^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AdaptadorSharePointGraph' object has no attribute 'listar_carpetas'. Did you mean: '_crear_carpeta'?
_ test_f013_r15_con_el_padre_ausente_es_archivo_fallido_sin_crear_intermedias _
tests\test_f013_adaptador_graph_listado.py:379: in test_f013_r15_con_el_padre_ausente_es_archivo_fallido_sin_crear_intermedias
    adap.crear_subcarpeta(padre=f"{INCIDENCIAS}/VILLA 08", nombre="PARTES FIRMADOS")
    ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'AdaptadorSharePointGraph' object has no attribute 'crear_subcarpeta'. Did you mean: '_crear_carpeta'?
...
39 failed in 3.08s
```

GREEN: **39 passed**; con tres tests más de forma de la respuesta (no JSON,
cuerpo que no es objeto, `nextLink` vacío), **42 passed**; con el de la
duración del log (§5), **43 passed**.

**T12.** Comando exacto, con el fichero de tests escrito y sin ninguno de los
módulos (commit `7a3468b`):

```
.venv/Scripts/python.exe -m pytest tests/test_f013_ubicacion_sigrid.py -q -p no:cacheprovider --tb=short
```

Salida real:

```
tests\test_f013_ubicacion_sigrid.py:43: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'UbicacionNoDisponible' from 'domain.models.errores' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f013_ubicacion_sigrid.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.91s
```

GREEN: primera pasada **108 passed, 3 failed** (los tres del truncado por
debajo de lo pedido: el test buscaba «cortada» y el mensaje decía «ha
cortado»; se cambió el mensaje, no el test); después, **111 passed**; con
el de la duración de los logs (§5), **112 passed**. Que las
aserciones muerden —y no solo el import— lo demuestran los 21 mutantes a mano
de §5 (21 muertos).

### 4 · Verificación

| Comando (desde `services/postventa-api` salvo `init.sh`) | Resultado |
|---|---|
| Verificación de T11: `pytest tests/test_f013_adaptador_graph_listado.py tests/test_f006_adaptador_graph.py tests/test_f032_alcance_cerrado.py` (más `test_f006_arquitectura.py`, `test_f006_fabrica.py` y `test_f013_fabricas.py`) | **165 passed, 5 skipped** (los 5 del diff de F-032, fuera de su rama). `ArchivoPort` sigue con sus tres métodos |
| Verificación de T12: `pytest tests/test_f013_ubicacion_sigrid.py` y `pytest tests -k "f009 or f012"` | **111 passed**; **857 passed** |
| Controles: `pytest tests -k "f013 or arquitectura or alcance or f006 or f019 or f031 or f033 or f034 or logs_sin" -rs` | **1.533 passed, 20 skipped**: los 20 son los controles del diff de otras ramas (4 de F-031, 5 de F-032, 4 de F-033, 7 de F-034), sin tocar ninguno |
| `python -m ruff check` sobre los ficheros tocados | All checks passed |
| `bash harness/init.sh` (estado final, tras `4da38a3`) | **ENTORNO LISTO**: api **3.962 passed, 35 skipped en 291,73 s**; `PUERTA COBERTURA: 100.0% de 526 líneas cambiadas cubiertas (526/526, umbral 80%, nivel critico)`. La pasada anterior, tras `66327f7`: 3.960 passed en 274,44 s, la misma cobertura |

### 5 · Mutación

**A mano** (`mutantes_t11_t12.py` en el scratchpad: copia desechable del
servicio, sustitución exacta, suite del fichero de T11 o T12, y restaurar;
base y restaurada en verde, 42 y 111 passed). **21 generados, 21 muertos**:

| # | Mutante | Resultado |
|---|---|---|
| A1 | no sigue el `nextLink` | muere |
| A2 | `crear_subcarpeta` recorre tramos con `asegurar_carpeta` | muere |
| A3 | sigue un `nextLink` a cualquier host | muere |
| A4 | registra el `nextLink` | muere |
| A5 | un `404` en una página siguiente es `None` | muere |
| A6 | devuelve también ficheros | muere |
| A7 | página sin lista = vacía | muere |
| A8 | crear con `rename` en vez de `fail` | muere |
| B1 | la lectura va a la ruta de escritura | muere |
| B2 | truncado por debajo de lo pedido se acepta | muere |
| B3 | la segunda lectura pide 200 filas | muere |
| B4 | registra `obra_ref` | muere |
| B5 | un error de mapeo sube como `ValueError` | muere |
| B6 | no se reintenta ningún transitorio | muere |
| B7 | `obra_ref` sin convertir a texto | muere |
| B8 | los patrones con los ceros del código | muere |
| B9 | código no numérico sin normalizar | muere |
| B10 | la fábrica exige `CIERRE_HABILITADO` | muere |
| B11 | la fábrica sin la puerta del entorno | muere |
| B12 | el constructor sin la puerta del entorno | muere |
| B13 | tipo y código en orden inverso | muere |

**Del arnés**: `python -m harness.mutacion --feature F-013 --timeout 900 --workers 6`,
lanzada **después** de `init.sh` y sin nada más corriendo; informe en el
scratchpad (`mutacion_F-013_bloque3.md`), **no** en `progress/mutacion_F-013.md`,
que es de T20. La herramienta calcula el alcance del diff de la rama: 12
ficheros, 2.146 líneas. **105 mutantes, 101 muertos, 4 supervivientes, 0
timeouts** en 3.352,8 s. De este bloque generó 14 en `graph.py`, 8 en
`ubicacion.py` y 10 en `consultas_ubicacion.py` (en `fabrica.py` de Sigrid,
ninguno: no tiene operadores que mutar).

| # | Línea y mutación | Análisis | Qué se hizo |
|---|---|---|---|
| 1 | `graph.py:368` `time.monotonic() - arranque` → `+` (log de `listar_carpetas`) | **Hueco real**: ningún test fijaba la duración del log; la suma da un número de seis cifras que parece «va lentísimo» y no un error (el mismo hueco que F-006 cerró en `subir`) | Test `test_f013_r23_el_log_del_listado_dice_la_duracion_y_no_la_hora`, con un reloj falso que arranca en 10.000 s. Reinyectado: **muere** (1 failed, 42 passed). Commit `4da38a3` |
| 2 | `ubicacion.py:166` ídem (log de `leer_ubicacion`) | **Hueco real**, el mismo | Test `test_f013_r23_las_dos_lecturas_registran_la_duracion_y_no_la_hora`. Reinyectado: **muere** (1 failed, 111 passed). `4da38a3` |
| 3 | `ubicacion.py:181` ídem (log de `leer_unidades_del_numero`) | **Hueco real**, el mismo; esta duración es la que tiene que medir el tiempo **[NO MEDIDO]** de la segunda lectura | El mismo test. Reinyectado: **muere** (1 failed, 111 passed). `4da38a3` |
| 4 | `destino_archivo.py:102` `@dataclass(frozen=True)` → `frozen=False` en `_Nivel` | **Equivalente**, el mismo del bloque 2 y de su cierre: `_Nivel` es privado, sus cuatro instancias se construyen en línea en la llamada a `bajar` y nadie les asigna nada | Nada; sigue pendiente de la aceptación del humano (nivel `critico`) |

### 6 · Qué queda fuera y qué falta

- **Fuera, a propósito**: el borde (T13). Hasta T13 nadie construye el
  explorador ni el lector de la ubicación desde producción: el comportamiento
  desplegable **no cambia** (`SHAREPOINT_ESTRUCTURA` sigue en `por_obra` por
  omisión).
- **Para T13, tres cosas que salen de este bloque**: (a) la misma instancia
  de `construir_archivador` como `archivador` y como `explorador`; (b)
  `construir_ubicaciones(ajustes)` solo en `posventa`, y **después** de
  `construir_archivador` (así, en `test`, el error es el del archivo); (c)
  `UbicacionNoDisponible` y `ConfiguracionSigridIncompleta` → **503** en
  `/api/archivar` (decisión 3).
- **Para el líder**: las decisiones 3 (error nuevo) y 4 (tipo del error de la
  puerta) rellenan huecos de la spec; si prefiere otra cosa, es una enmienda
  pequeña y localizada (`ubicacion.py` y `errores.py`).
- **Verificaciones MANUAL**: ninguna en este bloque. El tiempo real de la
  segunda lectura sigue **[NO MEDIDO]**; lo dirá el log del primer archivado.
- `progress/mutacion_F-013.md` no se ha escrito: es de T20.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests del bloque | `test_f013_adaptador_graph_listado.py` **43 passed** (RED: **39 failed**, `AttributeError … 'listar_carpetas'` e `isinstance(…, ExploradorBibliotecaPort)` falso); `test_f013_ubicacion_sigrid.py` **112 passed** (RED: `ImportError … 'UbicacionNoDisponible'` en la recogida) |
| Controles de alcance y arquitectura | **1.533 passed, 20 skipped** (los del diff de otras ramas), sin tocar ningún test de F-006, F-009, F-012, F-031…F-034 |
| Suite del proyecto (`bash harness/init.sh`, estado final tras `4da38a3`) | api **3.962 passed, 35 skipped en 291,73 s**; front en verde (caché); arnés 62 passed en 8,88 s; **ENTORNO LISTO** |
| Cobertura de las líneas cambiadas | **`PUERTA COBERTURA: 100.0% de 526 líneas cambiadas cubiertas (526/526, umbral 80%, nivel critico)`** |
| Mutación a mano | **21 generados, 21 muertos** |
| Mutación del arnés (6 workers, timeout 900 s) | **105 generados, 101 muertos, 4 supervivientes**, 0 timeouts, 3.352,8 s: 3 huecos reales del bloque (la duración de los logs) cerrados con test y reinyectados (mueren), 1 equivalente ya conocido (`_Nivel`) |
