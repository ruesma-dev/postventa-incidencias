<!-- specs/F-006-sharepoint/requirements.md -->
# F-006 · Nombrado y archivo en SharePoint — Requisitos (EARS)

> Contrato de partida: la entrada `F-006` de `harness/features.json`
> (`description` + cinco criterios `acceptance`). Estos requisitos los
> desarrollan; no los amplían.
>
> Rigor declarado: **`critico`** — fase RED, cobertura de las líneas
> cambiadas, campaña de mutación con **cero supervivientes**, y verificaciones
> `MANUAL (humano)` con su comando exacto y su resultado real.
>
> **Ni un dato real.** Todos los códigos, nombres y rutas de este documento
> están **inventados** y van marcados como tales. `0677`, `RS26.08 - 0123` y
> `RS26.08/0123` son ejemplos fabricados, no partes de nadie. Los partes de
> verdad llevan DNI y observaciones manuscritas de clientes: eso no entra en
> el repositorio, ni en esta spec, ni en fixtures, ni en logs.

## Alcance

F-006 hace **dos cosas** con un parte que F-004 ya declaró **apto**:

1. **Nombrarlo** con la convención de Posventa (paso 5 del pipeline de
   `docs/ARCHITECTURE.md`).
2. **Archivarlo** en SharePoint, en la carpeta de su código de obra, sin
   duplicar (paso 6).

Fuera de alcance, explícitamente:

| Qué | De quién es |
|---|---|
| Decidir si el parte es apto y clasificar la firma | **F-004** |
| Crear el esquema, las tablas y el DDL de la traza de archivo | **F-005** (F-006 **escribe** en la tabla `archivos`, no la crea) |
| Enseñar el resultado y dejar reintentar a una persona | **F-007** |
| Cerrar la incidencia en Sigrid | **F-008 / F-009** |
| Subir el PDF a Sigrid como gráfico | **F-012** |
| **Desplegar** la Function App y darle identidad en Azure | **F-010** |
| Mudar el archivo a la biblioteca de Posventa | **F-013** |
| Reagrupar el parte de dos hojas | **F-014** |

## Vocabulario

- **Parte troceado**: el `ParteTroceado` de F-002
  (`domain/models/remesa.py`). Su campo **`hash`** es la identidad del parte
  en todo el proyecto.
- **Resultado de validación**: el `ResultadoValidacion` de F-004
  (`domain/models/validacion.py`), con su `Veredicto` y su `Destino`. **Apto**
  = `veredicto == APTO` y `destino == ARCHIVO_Y_CIERRE`.
- **Código de obra**: `0677` (inventado). Va impreso en el parte, en su propio
  campo, y **decide la carpeta**.
- **Código de incidencia**: `RS26.08/0123` (inventado). Lo emite Sigrid
  **entero** —serie + correlativo— y se escribe con **barra** en el ERP y en
  el papel. **No es** «obra + número»: es otra cosa distinta del código de
  obra (`docs/ARCHITECTURE.md`, semántica 2).
- **Nombre de archivo**: `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`.
  En el nombre, la barra del código de incidencia va como **guion**
  (semántica 5): la barra es un separador de ruta, no un adorno.
- **Carpeta destino**: `<carpeta base>/<código de obra>`, con la base en
  configuración.
- **Traza de archivo**: la `TrazaArchivo` de F-005
  (`domain/models/persistencia.py`): qué se subió, dónde, con qué estado.
- **Destino de dev**: biblioteca propia dentro del **sitio de IT**, el mismo
  donde vive la de albaranes. Es **configuración**, no una constante.
- **Doble de prueba**: objeto de test que cumple `ArchivoPort` o el cliente
  HTTP del adaptador. **Nunca** hay red y **nunca** hay subida real.

---

## 1 · El nombrado (el corazón de la feature)

**R1.** El sistema debe componer el nombre del fichero como
`<código de obra><SEP><código de incidencia normalizado> PARTE FIRMADO.pdf`,
donde `<SEP>` es exactamente ` - ` (espacio, guion normal `U+002D`, espacio).
Ejemplo **inventado**: obra `0677` e incidencia `RS26.08/0123` producen
`0677 - RS26.08 - 0123 PARTE FIRMADO.pdf`.

**R2.** CUANDO el código de incidencia trae la **barra** (`/`) con la que lo
escriben Sigrid y el papel, el sistema debe sustituirla por ` - ` en el nombre
del fichero. La barra **nunca** llega al nombre: es un separador de ruta y
partiría el fichero en dos carpetas.

**R3.** CUANDO cualquiera de los códigos trae un guion que **no** es el normal
—guion largo `–` (`U+2013`), raya `—` (`U+2014`), guion sin salto `‑`
(`U+2011`) o signo menos `−` (`U+2212`)—, el sistema debe normalizarlo a guion
normal (`U+002D`) antes de componer el nombre.

**R4.** El sistema debe conservar **literalmente** los ceros a la izquierda del
código de obra: `0677` se archiva como `0677` y **nunca** como `677`. El
código de obra no se convierte a número en ningún punto del recorrido, ni para
comparar, ni para ordenar, ni para componer la carpeta.

**R5.** El sistema debe conservar el sufijo ` PARTE FIRMADO` y la extensión
`.pdf` **tal cual**, en mayúsculas y sin acortar: es el sufijo que ya usa
Posventa y lo que distingue el parte conformado de cualquier otro documento de
la misma incidencia.

**R6.** SI falta el código de obra o el código de incidencia —ausente, vacío o
solo espacios—, ENTONCES el sistema debe levantar `NombradoImposible`, **no
subir nada** y **nunca** inventar, deducir ni completar el dato que falta
(`docs/ARCHITECTURE.md`, semántica 5).

**R7.** SI el nombre compuesto contiene, después de normalizar, algún carácter
que SharePoint no admite en un nombre de fichero (`" * : < > ? / \ |`), o
empieza o acaba en espacio, o acaba en punto, ENTONCES el sistema debe
levantar `NombradoImposible` **sin sanearlo en silencio**: un nombre mutilado
se archiva igual de mal que uno equivocado, y nadie se entera.

**R8.** El sistema debe **eliminar** los espacios que flanquean a un separador
del código —la barra `/` y el guion `-`—, colapsar a uno los espacios
redundantes que no tocan un separador y recortar los de los extremos, de forma
que dos lecturas del mismo parte que solo difieran en espacios produzcan **el
mismo** nombre y **el mismo** código para el ERP.

> **Enmienda del 2026-09-15 · el ejemplo de R8 describía el defecto, no la
> garantía; la garantía no se recorta, se cumple por primera vez.**
>
> R8 decía, literal: *«El sistema debe colapsar los espacios redundantes de los
> códigos (`0677  -  RS26.08` → `0677 - RS26.08`) y recortar los de los
> extremos, de forma que dos lecturas del mismo parte que solo difieran en
> espacios produzcan **el mismo** nombre.»*
>
> **Lo que cambia es una cosa y solo una**: los espacios que rodean a un
> separador ya no se colapsan a uno, **se eliminan**. `RS26.08   -    0123`
> normaliza ahora a `RS26.08-0123` y no a `RS26.08 - 0123`.
>
> **Qué la invalidó.** La premisa original era que colapsar bastaba para que
> dos lecturas del mismo parte produjeran el mismo nombre. No bastaba, y se vio
> en real: `RS26.09- 0149` —guion pegado por un lado y suelto por el otro—
> producía un nombre de fichero **distinto** del canónico, y el código que
> viajaba al ERP conservaba los espacios. Sigrid busca la reclamación por
> **igualdad exacta**, así que el parte se archivaba bien y el cierre fallaba:
> medio circuito en verde tapando la mitad rota. Lo que R8 prometía no se
> estaba cumpliendo; ahora sí.
>
> **Quién y cuándo.** Lo decidió el **responsable del proyecto el 2026-09-15**,
> al ver fallar el circuito en real, y quedó recogido como **asunto 2** de
> F-028 (sus R44 a R49 y R55). El arreglo vive en un solo sitio,
> `domain/models/nombrado.py::normalizar_codigo`, del que dependen las dos
> conversiones del código —el nombre del fichero y el formato del ERP—, y por
> eso se corrige ahí y no en las puntas: dos criterios del mismo concepto
> divergen siempre.
>
> **Lo que no cambia.** Los ceros a la izquierda se conservan (R4), el sufijo y
> la extensión van literales (R5), un nombre imposible sigue siendo un error
> ruidoso (R7) y el código de **obra** no se parte por sus guiones: `06-77` es
> una obra, no dos. El test que fija R8 —
> `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`— cambió de
> expectativa ese mismo día y lleva esta enmienda citada en su docstring.

**R9.** El nombrado debe ser **dominio puro**: una función sin reloj, sin
azar, sin red y sin configuración, que dadas las mismas dos cadenas devuelva
siempre el mismo nombre.

---

## 2 · La carpeta destino

**R10.** El sistema debe componer la carpeta destino como
`<carpeta base>/<código de obra>`, con la carpeta base leída de configuración.
El código de obra entra en la ruta con sus ceros (R4).

**R11.** CUANDO la carpeta del código de obra no existe en la biblioteca, el
sistema debe crearla antes de subir el fichero.

**R12.** MIENTRAS la carpeta ya exista, el sistema debe reutilizarla: no crea
una segunda, no falla y no renombra la que hay. Pedir la carpeta dos veces
seguidas deja **una** carpeta.

---

## 3 · Idempotencia: reprocesar no duplica

**R13.** El sistema debe identificar «el mismo parte» por el **`hash` del
parte troceado** que produce F-002 y que F-005 usa como clave primaria. F-006
**no define ningún criterio propio** de deduplicación.

**R14.** MIENTRAS exista una traza de archivo en estado `archivado` para ese
`hash_parte`, el sistema no debe volver a subir el fichero: devuelve el
destino ya archivado, con un aviso que lo diga, y **no** llama al proveedor.

**R15.** CUANDO el sistema sube un fichero, debe pedir explícitamente que se
**reemplace** el homónimo de esa carpeta, nunca que se renombre. Subir dos
veces el mismo parte debe dejar en la carpeta **un solo elemento** y **ningún**
nombre con sufijo de desambiguación (`... (1).pdf`).

**R16.** CUANDO en la carpeta ya existe un fichero con ese nombre pero de un
parte distinto (otro `hash`), el sistema debe reemplazarlo y **dejar aviso** de
que lo hizo: el archivo de Posventa se queda con la última versión, y quien
revise tiene que poder enterarse de que hubo una anterior.

---

## 4 · Solo se archiva lo apto

**R17.** SI el resultado de validación de un parte no es apto —`veredicto`
distinto de `APTO` o `destino` distinto de `ARCHIVO_Y_CIERRE`—, ENTONCES el
sistema debe levantar `ParteNoApto` y **no subir absolutamente nada**, ni
crear la carpeta.

**R18.** SI no se aporta resultado de validación, ENTONCES el sistema debe
levantar `ParteNoApto`: archivar «por si acaso» un parte del que no consta que
haya pasado la validación es exactamente lo que prohíbe `CHECKPOINTS.md` C3.

---

## 5 · Ninguna subida real desde local ni desde los tests

> Esta sección **es** la regla dura de `CLAUDE.md` («PROHIBIDO subir nada al
> SharePoint de Posventa desde local») escrita como requisitos verificables.
> No se cumple por costumbre: se cumple porque el código lo impide.

**R19.** SI `ENTORNO` no es `dev` ni `pro`, ENTONCES construir el adaptador
real de SharePoint debe fallar con `ArchivoDeshabilitado`, **y el fallo debe
producirse en el propio constructor del adaptador**, no solo en la fábrica:
componer las piezas de otra manera no puede ser la vía para saltárselo.

**R20.** MIENTRAS `ARCHIVO_HABILITADO` no esté puesto a verdadero, el sistema
no debe construir el adaptador real. Su valor por defecto es **falso**: el
comportamiento por omisión es **no subir**.

**R21.** El sistema no debe abrir ninguna conexión de red durante la suite, y
ningún test debe construir el adaptador real de SharePoint. La guardia de red
de F-003 (`tests/conftest.py`) se reutiliza **sin tocarla**.

**R22.** El dominio y la aplicación no deben importar `msal`, `requests`,
`httpx` ni nada de `infrastructure`. El **único** paquete del servicio que
conoce Microsoft Graph debe ser `infrastructure/sharepoint/`.

---

## 6 · Traza, errores y datos personales

**R23.** CUANDO la subida termina bien, el sistema debe guardar la traza de
archivo con estado `archivado`, el nombre del fichero, la carpeta, el
identificador de la biblioteca, el del elemento, su URL y la fecha UTC.

**R24.** SI la subida falla, ENTONCES el sistema debe guardar la traza en
estado `error` con su motivo, **no** dejar el parte marcado como archivado, y
permitir reintentar sin efectos raros (R14 solo corta si el estado es
`archivado`).

**R25.** CUANDO el proveedor devuelve un error transitorio (tiempo agotado,
corte de conexión, `408`, `429`, `5xx`), el sistema debe reintentar con espera
exponencial hasta el máximo configurado. SI el error no es transitorio (`400`,
`401`, `403`, `404`), ENTONCES no debe reintentar.

**R26.** El sistema no debe volcar **nunca** en un mensaje de error, en un log
ni en la respuesta HTTP: los bytes del parte, el DNI, las observaciones
manuscritas, el token de acceso ni el secreto de cliente. Lo que sí se
registra: `hash_parte`, nombre del fichero, carpeta, estado, tamaño en bytes,
intento y duración.

---

## 7 · Configuración (y por qué F-013 sale casi gratis)

**R27.** El sitio, la biblioteca y la carpeta base del destino deben ser
**configuración** leída del entorno. Cambiarlos no debe tocar el dominio, la
aplicación ni el pipeline: eso es lo que hace posible F-013 sin rehacer nada.

**R28.** SI falta una variable obligatoria del destino o de la credencial,
ENTONCES el sistema debe levantar `ConfiguracionSharePointIncompleta`
nombrando **la variable** que falta y **jamás su valor**.

**R29.** El repositorio no debe contener ningún valor de esa configuración:
`.env.example` y `local.settings.json.example` llevan **placeholders**, y ni
la spec ni `docs/INTEGRACION.md` traen identificadores de sitio, de
biblioteca, de tenant ni de suscripción.

---

## 8 · El borde HTTP

**R30.** CUANDO llega `POST /api/archivar` con el PDF de un parte apto y sus
datos, el sistema debe responder **200** con `hash_parte`, `nombre_fichero`,
`carpeta`, `estado`, `web_url` y `avisos`, y **nada más**: ni el contenido del
PDF, ni ningún campo manuscrito, ni la configuración del destino.

**R31.** SI la petición no trae fichero o el cuerpo no cumple el contrato,
ENTONCES el sistema debe responder **400**. SI el parte no es apto, **409**.
SI el archivo está deshabilitado por entorno o configuración, **503**. SI el
proveedor no responde de forma utilizable, **502**. En los cuatro casos, **sin
haber subido nada**.

---

## 9 · El documento del ecosistema

**R32.** DONDE este proyecto pase a consumir SharePoint —un recurso del
ecosistema que hoy no consume—, el sistema debe declararlo en
`docs/INTEGRACION.md` (la fuente de verdad que crea F-005): qué sitio y qué
biblioteca por **nombre de variable**, con qué identidad, con qué permisos,
qué volumen se espera y qué se rompe si alguien lo cambia. Copiar ese
documento a `azure-apps/postventa_incidencias.md` es **`MANUAL (humano)`**: es
otro repositorio git y ningún agente commitea en un repositorio ajeno.

---

## Trazabilidad requisito → test

| Req | Test (nombre trazable) |
|---|---|
| R1 | `test_f006_r1_el_nombre_sigue_la_convencion_de_posventa` |
| R2 | `test_f006_r2_la_barra_del_numero_de_incidencia_pasa_a_guion` |
| R3 | `test_f006_r3_los_guiones_no_normales_se_normalizan` |
| R4 | `test_f006_r4_los_ceros_a_la_izquierda_del_codigo_de_obra_se_conservan`, `test_f006_r4_la_carpeta_conserva_los_ceros` |
| R5 | `test_f006_r5_el_sufijo_y_la_extension_van_literales` |
| R6 | `test_f006_r6_sin_codigo_de_obra_no_se_nombra`, `test_f006_r6_sin_numero_de_incidencia_no_se_nombra`, `test_f006_r6_el_nombrado_imposible_no_sube_nada` |
| R7 | `test_f006_r7_un_caracter_prohibido_no_se_sanea_en_silencio` |
| R8 | `test_f006_r8_los_espacios_redundantes_colapsan`, `test_f006_r8_los_espacios_interiores_se_colapsan_a_uno`. **Premisa enmendada el 2026-09-15**: ver el recuadro bajo R8 |
| R9 | `test_f006_r9_el_nombrado_es_puro_y_deterministico` |
| R10 | `test_f006_r10_la_carpeta_es_base_mas_codigo_de_obra` |
| R11 | `test_f006_r11_la_carpeta_se_crea_si_no_existe` |
| R12 | `test_f006_r12_pedir_la_carpeta_dos_veces_deja_una_sola` |
| R13 | `test_f006_r13_la_identidad_del_parte_es_el_hash_de_f002` |
| R14 | `test_f006_r14_con_traza_archivada_no_se_vuelve_a_subir` |
| R15 | `test_f006_r15_subir_dos_veces_deja_un_solo_elemento`, `test_f006_r15_nunca_se_pide_renombrar` |
| R16 | `test_f006_r16_mismo_nombre_otro_hash_reemplaza_con_aviso` |
| R17 | `test_f006_r17_un_parte_no_apto_no_se_archiva`, `test_f006_r17_un_parte_no_apto_no_crea_carpeta` |
| R18 | `test_f006_r18_sin_validacion_no_se_archiva` |
| R19 | `test_f006_r19_en_entorno_local_la_fabrica_no_construye_el_adaptador`, `test_f006_r19_el_constructor_del_adaptador_tambien_muerde` |
| R20 | `test_f006_r20_por_defecto_el_archivo_esta_deshabilitado` |
| R21 | `test_f006_r21_la_suite_no_puede_abrir_conexiones`, `test_f006_r21_ningun_test_construye_el_adaptador_real` |
| R22 | `test_f006_r22_dominio_y_aplicacion_no_conocen_graph`, `test_f006_r22_solo_infrastructure_sharepoint_importa_graph` |
| R23 | `test_f006_r23_la_traza_de_exito_lleva_todo_lo_declarado` |
| R24 | `test_f006_r24_un_fallo_deja_traza_de_error_y_permite_reintentar` |
| R25 | `test_f006_r25_un_error_transitorio_se_reintenta`, `test_f006_r25_un_error_no_transitorio_no_se_reintenta` |
| R26 | `test_f006_r26_el_error_no_lleva_contenido_ni_datos_personales`, `test_f006_r26_el_log_no_lleva_la_credencial` |
| R27 | `test_f006_r27_el_destino_sale_de_configuracion` |
| R28 | `test_f006_r28_configuracion_incompleta_falla_nombrando_la_variable` |
| R29 | `test_f006_r29_los_ejemplos_de_entorno_no_traen_valores` |
| R30 | `test_f006_r30_archivar_devuelve_200_con_el_contrato` |
| R31 | `test_f006_r31_sin_fichero_responde_400`, `test_f006_r31_parte_no_apto_responde_409`, `test_f006_r31_archivo_deshabilitado_responde_503`, `test_f006_r31_fallo_del_proveedor_responde_502` |
| R32 | `test_f006_r32_integracion_declara_el_consumo_de_sharepoint` |

Todos los tests usan **dobles construidos en el propio test**: un `ArchivoPort`
falso y un cliente HTTP falso que **imita el comportamiento de una biblioteca
de SharePoint** (ver `design.md` §6). Ninguno depende de `muestras/`, ninguno
abre red, ninguno sube nada, y ningún ejemplo —ni aquí ni en los tests— lleva
datos personales reales.

**Verificaciones `MANUAL (humano)`**: que una subida real funcione contra la
biblioteca de dev **no lo puede demostrar la suite**, y **no puede hacerse
desde local**. Van como tareas manuales con su comando exacto en `tasks.md`
(**T17**, **T18** y **T19**), ejecutadas por el humano desde el entorno
desplegado y sobre el destino de dev.

**T18 está DIFERIDA a F-010** por decisión del humano del **2026-08-19**
(**D3**, opción (a); ver `design.md` §10): F-006 se cierra con esa
verificación **declarada y pendiente**, y se ejecuta cuando F-010 despliegue
el entorno. Ese cierre necesita la **autorización expresa del humano ante
`CHECKPOINTS.md` C5**, y es el caso que motiva **F-017**.
