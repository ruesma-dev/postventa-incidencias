<!-- progress/impl_utillaje_puesta_en_marcha.md -->
# F-012 · Utillaje de puesta en marcha del bloque 9

> **Veredicto: el encargo está hecho y en verde; `bash harness/init.sh` NO lo
> está, por un defecto que no es de este trabajo.** Los dos scripts nuevos, sus
> 31 tests y el censo pasan; la suite del api tiene **un** test en rojo,
> `test_f012_fabrica_grafico.py::test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan`,
> que falla por el contenido del `.env` local —fichero que este agente tiene
> **prohibido tocar**— y que ya fallaba antes de empezar. Diagnóstico completo y
> los dos remedios posibles, en la sección «Lo que bloquea el cierre».

Rama `feature/F-012-grafico-sigrid`. Ni un `git push`. Ningún estado de
`harness/features.json` tocado. **Nada ejecutado** contra Azure, Sigrid,
`sigrid-api`, el PostgreSQL compartido ni SharePoint —ni lecturas—.

---

## 1 · Qué cambió

| Fichero | Qué es |
|---|---|
| `infra/19_ventana_escritura.ps1` | **Nuevo.** Consulta, abre y cierra la ventana de escritura contra el ERP (`CIERRE_HABILITADO` de nuestra Function App). 365 líneas. |
| `infra/20_login_sigrid.ps1` | **Nuevo.** Comprueba, solo leyendo, si el login que la siembra derivaría de un correo existe en el maestro de usuarios del ERP. 224 líneas. |
| `services/postventa-api/tests/test_f012_scripts_infra.py` | **+31 tests** en una sección nueva al final, con el estilo de las que ya había. |
| `services/postventa-api/tests/test_f010_scripts_infra.py` | Los dos scripts entran en el censo `scripts_entregados()`, que es donde vive el barrido de R1, R7 y R8. |

Los dos ficheros `.ps1` son **ASCII puro, CRLF, sin BOM**, empiezan por su ruta
relativa y no escriben ni un nombre de recurso literal.

### De dónde salen: eran fragmentos sueltos dentro de un documento

- **La ventana de escritura** se abría y se cerraba con dos líneas de `az`
  copiadas a mano desde `progress/guion_bloque9_F-012.md` —paso 3 de T25, pasos
  1 y 2 de T32—, **con el grupo de recursos y el nombre de la Function App
  tecleados dentro del propio Markdown**. Un comando copiado de un documento no
  tiene precondiciones, ni veredicto, ni código de salida, y no se entera de si
  lo que pidió ha ocurrido. Y es la operación más delicada del bloque: la que
  decide si el ERP de producción admite escrituras de este servicio.
- **La comprobación del login** no estaba escrita en ninguna parte. Se sabía
  que hacía falta —el alta manual de `07_alta_usuario_sigrid.ps1` existe
  justamente para los casos que no cumplen la convención— pero saber *de
  antemano* si una persona la cumple exigía abrir Sigrid.

---

## 2 · Decisiones de diseño

### `19_ventana_escritura.ps1`

1. **El modo por omisión solo lee.** Sin parámetros, `-Estado`: dice cómo está
   y sale. Un script que abriera la ventana de escritura contra el ERP por no
   llevar argumentos sería una trampa. Lo fija
   `test_f012_ventana_por_omision_solo_lee`, comparando posiciones en el propio
   texto: la salida del modo `estado` va **antes** de la primera invocación de
   la función que escribe.
2. **`-Abrir` avisa ANTES de pedir la palabra.** La App Setting es **una sola**
   para el gráfico y para el cierre (`design.md` D-B, §0.2 del guion), así que
   abrirla habilita **las dos** escrituras contra el ERP. Es deliberado, pero no
   puede ser una sorpresa para quien la abre «solo para probar el gráfico». El
   orden aviso → confirmación → escritura está fijado por posiciones en
   `test_f012_ventana_abrir_avisa_y_exige_confirmacion_tecleada`. La palabra
   tecleada es `ABRIR`, igual que `CARGAR` y `DESPLEGAR` en los dos scripts que
   ya la piden.
3. **`-Cerrar` no pide confirmación**, y eso también es una decisión: cerrar
   siempre es seguro y el paso 1 de T32 se ejecuta **salga bien o mal** el
   bloque. Una palabra que teclear en ese camino solo puede conseguir que
   alguien se la salte y deje la ventana abierta.
4. **Escribir y releer van en la MISMA función**, `Fijar-Ventana`. Separarlas
   permitiría un camino que escribe y da por bueno lo que pidió. Lo que se
   imprime es lo que el entorno dice, y si no coincide con lo pedido el script
   sale con código propio (`9`).
5. **El script dice explícitamente que su verde no es el veredicto del borde.**
   La Function tarda unos segundos en reiniciarse y hasta entonces puede seguir
   sirviendo con el valor anterior. La comprobación que vale es que
   `/api/adjuntar` responda 503 con la ventana cerrada (pasos 2 y 4 de T25, paso
   3 de T32), y **eso no se hace desde aquí**.
6. **«Desconocido» no es un aprobado.** Si la lectura del valor falla, el script
   sale con `6` en vez de suponer que está cerrada. Es la misma regla que ya
   aplica `verificar_despliegue.ps1` con `ARCHIVO_HABILITADO`.
7. **Ni un nombre de recurso.** `00_vars_postventa.ps1` por punto; el único
   literal propio es el nombre de la App Setting, en una constante arriba.
8. **El identificador de suscripción se lee para saber que hay sesión y se
   descarta acto seguido** (`$suscripcion = $null`): no se imprime, no se
   escribe, no aparece en ningún mensaje (R8).

### `20_login_sigrid.ps1`

1. **No inventa SQL.** Usa la consulta del servicio,
   `SELECT COUNT(*) FROM dbo.usu WHERE cod = ?`, y el test la **importa** de
   `infrastructure.sigrid.consultas.SQL_USUARIO` y la exige literal. Si allí
   cambiara y aquí no, el script daría un veredicto sobre una pregunta que el
   servicio ya no hace. Va parametrizada con `?`.
2. **Deriva el candidato igual que el dominio**: recorta, pasa a minúsculas y
   toma lo anterior a la **primera** arroba —traducción literal de
   `derivar_login_candidato` de `domain/models/cierre.py`, incluido el caso
   `@algo` (sin nada delante), que devuelve cadena vacía en las dos partes—.
3. **Veredicto de tres casos, no de dos.** Existe una vez → la siembra
   funcionará; no existe → alta manual con `07_alta_usuario_sigrid.ps1`, y el
   mensaje dice que **reintentar no lo arregla**; existe varias → ambigüedad,
   y no se elige por nuestra cuenta, porque la fila de auditoría del cierre
   queda firmada con ese login.
4. **No escribe nada**, y está comprobado a nivel de texto: ni verbos de
   escritura contra Sigrid o PostgreSQL, ni `psycopg`, ni `appsettings set`, ni
   `Out-File`/`Set-Content`.
5. **Hereda `-Login` para el caso que motiva el script.** La convención no se
   cumple siempre y hay un caso conocido: una persona de Posventa cuyo login del
   ERP es más corto que el prefijo de su correo. Sin `-Login` no habría forma de
   comprobar precisamente eso.
6. **El recuento se lee por posición**, no con `Get-SigridValor`: la consulta
   devuelve una única columna sin nombre y ponerle un alias sería cambiar la
   consulta del servicio.

### Una desviación, y por qué

El encargo pedía «cargando `00_vars_postventa.ps1` por punto» como parte del
estilo obligatorio. **`20_login_sigrid.ps1` no lo carga**, y es deliberado: no
toca ningún recurso de Azure de este proyecto —habla con la pasarela del ERP,
que es de otro dueño—, así que ese fichero solo le aportaría variables sin usar.
Su fuente única es `08_lectura_sigrid_comun.ps1`, exactamente como los scripts
09 a 17, que tampoco lo cargan. Está justificado dentro de la propia cabecera
del script, en el párrafo «POR QUE ESTE NO CARGA `00_vars_postventa.ps1`».
`19_ventana_escritura.ps1` **sí** lo carga, porque sí nombra recursos nuestros.

---

## 3 · Fase RED (nivel `critico`)

Los 31 tests se escribieron **antes** que los dos scripts. Comando exacto y
salida real del fallo:

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f012_scripts_infra.py -q
......................................................FFFFFFFFFFFFFFFFFF [ 84%]
FFFFFFFFFFFFF                                                            [100%]
================================== FAILURES ===================================
____ test_f012_utillaje_los_dos_scripts_existen[19_ventana_escritura.ps1] _____

script = WindowsPath('C:/Users/pgris/PycharmProjects/postventa-incidencias/infra/19_ventana_escritura.ps1')

    @pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
    def test_f012_utillaje_los_dos_scripts_existen(script):
        """Sin ellos, las dos operaciones se hacen copiando de un Markdown."""
>       assert script.is_file()
E       AssertionError: assert False
E        +  where False = is_file()
E        +    where is_file = WindowsPath('.../infra/19_ventana_escritura.ps1').is_file

tests\test_f012_scripts_infra.py:569: AssertionError
...
_ test_f012_utillaje_cada_script_empieza_por_su_ruta_relativa[20_login_sigrid.ps1] _
...
E       FileNotFoundError: [Errno 2] No such file or directory:
        'C:\\...\\infra\\20_login_sigrid.ps1'
...
=========================== short test summary info ===========================
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_los_dos_scripts_existen[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_los_dos_scripts_existen[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_empieza_por_su_ruta_relativa[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_empieza_por_su_ruta_relativa[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_es_ascii_puro_y_sin_bom[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_es_ascii_puro_y_sin_bom[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_va_en_crlf[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_va_en_crlf[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_tiene_ayuda_con_parametros_y_ejemplos[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_script_tiene_ayuda_con_parametros_y_ejemplos[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_causa_de_fallo_tiene_su_codigo_y_ninguno_se_repite[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_cada_causa_de_fallo_tiene_su_codigo_y_ninguno_se_repite[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_ningun_script_trae_un_valor[19_ventana_escritura.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_ningun_script_trae_un_valor[20_login_sigrid.ps1]
FAILED tests/test_f012_scripts_infra.py::test_f012_utillaje_los_dos_entran_en_el_censo_de_los_scripts_de_infra
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_el_nombre_de_la_app_setting_va_en_una_constante
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_los_nombres_de_recurso_salen_del_fichero_de_variables
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_por_omision_solo_lee
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_el_estado_se_dice_en_palabras
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_abrir_avisa_y_exige_confirmacion_tecleada
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_cerrar_no_pide_confirmacion
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_despues_de_escribir_se_relee_el_valor
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_no_toca_ninguna_otra_app_setting
FAILED tests/test_f012_scripts_infra.py::test_f012_ventana_los_tres_modos_son_excluyentes
FAILED tests/test_f012_scripts_infra.py::test_f012_login_la_consulta_es_exactamente_la_del_servicio
FAILED tests/test_f012_scripts_infra.py::test_f012_login_el_candidato_se_deriva_igual_que_en_el_dominio
FAILED tests/test_f012_scripts_infra.py::test_f012_login_acepta_tambien_un_login_directo
FAILED tests/test_f012_scripts_infra.py::test_f012_login_la_cabecera_dice_que_la_convencion_no_siempre_se_cumple
FAILED tests/test_f012_scripts_infra.py::test_f012_login_el_veredicto_distingue_los_tres_casos
FAILED tests/test_f012_scripts_infra.py::test_f012_login_no_escribe_absolutamente_nada
FAILED tests/test_f012_scripts_infra.py::test_f012_login_la_consulta_va_parametrizada_y_por_el_comun
31 failed, 54 passed in 5.88s
```

Y después de escribir los dos scripts, el mismo comando ampliado al censo:

```
$ cd services/postventa-api && ./.venv/Scripts/python.exe -m pytest tests/test_f012_scripts_infra.py tests/test_f010_scripts_infra.py -q
........................................................................ [ 30%]
........................................................................ [ 60%]
.....s.................................................................s [ 90%]
s......................                                                  [100%]
236 passed, 3 skipped in 1.92s
```

**Tres tests hubo que corregirlos, y ninguna corrección relajó lo que
comprueban** —quedan anotadas aquí porque un test retocado después de ver el
código es exactamente lo que la fase RED existe para vigilar—:

1. `..._despues_de_escribir_se_relee_el_valor` buscaba el literal
   `appsettings set`; los argumentos de `az` van como **array**
   (`"appsettings", "set"`), que es el patrón de `Valor-De-Az` de
   `14_paso0_sigrid.ps1`. Se ajustó la cadena buscada; la comprobación —que la
   relectura va **después** de la escritura, dentro de la misma función— es la
   misma.
2. `..._no_toca_ninguna_otra_app_setting` pasó de un `findall` sobre
   `--settings ...` a capturar el argumento entre comillas. Quedó **más
   estricto**: ahora exige que el único `--settings` sea exactamente
   `$APP_SETTING_VENTANA=$Valor`, no solo que tenga un `=`.
3. `..._la_cabecera_dice_que_la_convencion_no_siempre_se_cumple` normaliza los
   espacios antes de buscar la frase, porque la cabecera va justificada a 79
   columnas y la frase se parte en dos líneas.

---

## 4 · Verificación

Nada se ejecutó contra Azure, Sigrid, `sigrid-api`, el PostgreSQL compartido ni
SharePoint. Ni una lectura.

### Análisis sintáctico de los dos `.ps1` (salida real)

```
PS> foreach ($nombre in @("19_ventana_escritura.ps1", "20_login_sigrid.ps1")) {
        $ruta = Join-Path $raiz $nombre
        $errores = $null; $tokens = $null
        $null = [System.Management.Automation.Language.Parser]::ParseFile($ruta, [ref]$tokens, [ref]$errores)
        Write-Output ("=== {0} : {1} token(s), {2} error(es) de sintaxis" -f $nombre, $tokens.Count, $errores.Count)
        foreach ($e in $errores) { Write-Output ("    linea {0}: {1}" -f $e.Extent.StartLineNumber, $e.Message) }
    }

=== 19_ventana_escritura.ps1 : 1143 token(s), 0 error(es) de sintaxis
=== 20_login_sigrid.ps1 : 540 token(s), 0 error(es) de sintaxis
```

### Codificación y finales de línea (salida real)

```
19_ventana_escritura.ps1 crlf 365 lf sueltos 0 bom False
20_login_sigrid.ps1 crlf 224 lf sueltos 0 bom False
```

### `ruff`

```
$ python -m ruff check .
Found 58 errors.
$ python -m ruff check services/postventa-api/tests/test_f012_scripts_infra.py services/postventa-api/tests/test_f010_scripts_infra.py
All checks passed!
```

58 avisos: **exactamente la deuda previa**, ni uno nuevo.

---

## 5 · Lo que bloquea el cierre (no es de este trabajo)

`bash harness/init.sh` termina en rojo por **un** test:

```
FAILED tests/test_f012_fabrica_grafico.py::test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan
E   AssertionError: assert 'SIGRID_API_BASE_URL' in 'faltan variables para hablar
    con sigrid-api: SIGRID_BASE_DATOS. Se dicen los nombres y nunca los valores:
    una de ellas es una credencial'
```

**Causa, medida.** El ayudante del propio fichero promete algo que no cumple:

```python
def _ajustes(**entorno: str) -> Ajustes:
    """Unos ajustes construidos a mano, sin tocar el `.env` de nadie."""
    return Ajustes(**entorno)
```

`Ajustes` es `pydantic-settings`, así que **todo lo que no se le pase por
argumento lo lee del `.env` local**. El `.env` de este puesto —modificado hoy a
las 18:23, antes de que empezara este encargo, presumiblemente preparando el
bloque 9— ya define `SIGRID_API_BASE_URL` y `SIGRID_API_KEY` (nombres; los
valores no se han mirado ni se miran). Con eso, la fábrica solo echa en falta
`SIGRID_BASE_DATOS` y el test, que exige que se nombren **las tres**, falla.

Comprobado sin tocar `.env`, ejecutando la fábrica de las dos maneras:

```
 Ajustes(...)             -> faltan variables para hablar con sigrid-api: SIGRID_BASE_DATOS
 Ajustes(_env_file=None)  -> faltan variables para hablar con sigrid-api: SIGRID_API_BASE_URL, SIGRID_API_KEY, SIGRID_BASE_DATOS
```

**No lo causa este encargo.** El test falla ejecutando **solo su fichero**, que
no importa nada de lo que se ha tocado aquí, y con la suite del api completa
todo lo demás pasa:

```
$ ./.venv/Scripts/python.exe -m pytest -q --deselect tests/test_f012_fabrica_grafico.py::test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan
2095 passed, 13 skipped, 1 deselected in 88.42s (0:01:28)
```

El primer `init.sh` de la sesión salió en verde **porque no llegó a ejecutar la
suite del api**: la sirvió de la caché («árbol sin cambios desde el último
verde»), de una sesión anterior en la que el `.env` todavía no traía esas dos
variables.

**Por qué no lo he arreglado yo.** Es un defecto de la suite de F-012 —una
feature ya revisada, con campaña de mutación cerrada y sus 5 supervivientes
aceptados por escrito—, está fuera de este encargo, y tiene **dos** remedios
válidos que no son míos:

- **(a)** Hacer que el ayudante cumpla lo que dice su docstring:
  `return Ajustes(_env_file=None, **entorno)`. Es una línea, restaura el
  principio que declara el propio `conftest.py` («que ningún test dependa de lo
  que haya en el `.env` de quien la ejecuta») y deja los tres nombres en el
  mensaje. Comprobado arriba que funciona.
- **(b)** Que el humano quite esas variables de su `.env`. Este agente tiene
  **prohibido** tocar ese fichero, así que no es una opción que pueda ejercer.

Hay además un hallazgo que conviene no perder: **la caché de `init.sh` puede
tapar un rojo que depende del entorno**, y este verde llevaba tapado desde que
el `.env` cambió.

---

## 6 · Verificaciones MANUAL pendientes

Los dos scripts **no se han ejecutado**: hacerlo tocaría Azure o el ERP de
producción, y este encargo lo excluye expresamente. Lo que queda por comprobar
con el entorno delante, cuando se ejecute el bloque 9:

- [ ] `19_ventana_escritura.ps1` sin parámetros imprime el estado real y sale
      `0` sin escribir.
- [ ] `19_ventana_escritura.ps1 -Abrir` muestra el aviso, exige teclear `ABRIR`,
      y al releer dice «abierta». Sustituye al paso 3 de T25.
- [ ] `19_ventana_escritura.ps1 -Cerrar` cierra sin preguntar y al releer dice
      «cerrada». Sustituye a los pasos 1 y 2 de T32.
- [ ] Que el veredicto del **borde** sigue haciéndose aparte: `/api/adjuntar`
      responde 503 con la ventana cerrada (paso 3 de T32).
- [ ] `20_login_sigrid.ps1 -Correo ...` sobre las dos personas de Posventa, una
      de las cuales **no** cumple la convención: se espera «existe una vez» en
      un caso y «no existe» en el otro, con el segundo remitiendo a
      `07_alta_usuario_sigrid.ps1`.

Y una tarea documental que este encargo no incluía y que alguien debería
decidir: **el guion `progress/guion_bloque9_F-012.md` sigue teniendo las líneas
de `az` copiadas a mano** en el paso 3 de T25 y en los pasos 1 y 2 de T32, con
los nombres de recurso dentro. Mientras no se sustituyan por la llamada al
script 19, conviven las dos vías y la del documento es la que se queda vieja.

---

## 7 · Evidencias

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados · suite del api** | **2 095 pasan, 13 saltados, 1 deseleccionado**; con ese incluido, **1 en rojo por el `.env`** (§5) | `pytest -q --deselect ...` |
| **Tests ejecutados · suite raíz del arnés** | **62 pasan** | `bash harness/init.sh` |
| **Tests nuevos de este encargo** | **31**, todos en verde (18 parametrizados sobre los dos scripts + 13 propios) | `pytest tests/test_f012_scripts_infra.py` |
| **Cobertura de las líneas cambiadas** | **99,0 %** (1 068 / 1 079, umbral 80 %, nivel `critico`) | línea `PUERTA COBERTURA` del `init.sh` **con la suite entera**. El `init.sh` en rojo imprime 94,8 % (1 023 / 1 079) porque aborta al primer fallo y deja código sin ejercitar; el denominador es el mismo. |
| **Mutantes generados y supervivientes** | **No aplica a este encargo, y no se ha relanzado la campaña.** Lo entregado es **PowerShell y tests**: `harness/alcance.py` solo mide `.py`, y no se ha añadido ni modificado una sola línea de código de producción en Python. La campaña vigente de F-012 sigue siendo `progress/mutacion_F-012.md`, con sus 5 supervivientes ya aceptados por el humano el 2026-09-06. | — |
| **Tiempo de ejecución de la suite** | **88,42 s** (api) · **10,96 s** (raíz) · **1,92 s** (los dos ficheros de tests de scripts) | salida de la propia suite |
| **Análisis sintáctico PowerShell** | **0 errores** en los dos (1 143 y 540 tokens) | `Parser::ParseFile`, §4 |
| **`ruff`** | **58 avisos**, la deuda previa exacta; **0** en los ficheros tocados | `python -m ruff check .` |
