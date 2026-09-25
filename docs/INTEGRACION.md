<!-- docs/INTEGRACION.md -->
# Integración con el ecosistema · postventa-incidencias

> **Origen**: este repositorio. **Fecha**: 2026-09-24. **Última feature que
> lo tocó**: F-013, antes de su corte (nació con F-005).
>
> Este documento es la **fuente de verdad** de lo que `postventa-incidencias`
> consume del ecosistema de Ruesma y de lo que expone a los demás. Se copia a
> `azure-apps/postventa_incidencias.md` (regla 1 del `README.md` de
> `azure-apps/`), y **el dueño del documento es este proyecto**: si cambia lo
> que consumimos, se actualiza aquí en el mismo trabajo, no después.
>
> **Ni un valor de conexión.** Aquí van nombres de recurso y nombres de
> variable de entorno; ni hosts, ni usuarios, ni contraseñas, ni IDs de
> suscripción, tenant u objeto, ni direcciones internas. Lo vigila
> `services/postventa-api/tests/test_f005_integracion_sin_secretos.py`, que
> falla si alguno entra.

## 1 · Qué consumimos hoy

| Recurso | Compartido con | Qué hacemos | Desde |
|---|---|---|---|
| PostgreSQL `psql-albaranes-rs9k2` | `albaranes`, `partes`, `datamart-seg-anual` | Base propia `postventa`: estado de remesas, partes, validaciones, archivo, cierres y el **histórico de estado** de cada parte (F-028) | **F-005** |
| `sigrid-api` | todo el ecosistema | Lectura de la reclamación **y DOS ESCRITURAS en el ERP de producción**: el **parte adjunto como gráfico** —`POST /api/sigrid/concepto-grafico`, tres filas en dos bases— y el **cierre** —`con.est` al estado de cierre y su fila de auditoría en `dbo.log`—. Solo desde el entorno desplegado y con el interruptor encendido | F-008 / **F-009** / **F-012** |
| SharePoint (Graph) | IT | Archivo de los PDF validados | F-006 |
| Gemini | — | Extracción multimodal y clasificación de firma | F-003 |
| Entra ID | todo el ecosistema | Autenticación del front y de la tarjeta del portal | F-010 |

**Lo nuevo de F-005 es la primera fila**, y es la única que mete a este
proyecto como **cuarto inquilino** de un servidor que ya usaban otros tres.

**Lo nuevo de F-009 es la segunda**, y hay que decirlo con todas las letras:
hasta ahora este proyecto **solo leía** de Sigrid. Desde F-009 **escribe en el
ERP del que depende toda la empresa**. Qué escribe, con qué puertas y qué se
rompe si alguien cambia la configuración de escritura de la pasarela está en
**§3 bis**.

**Y lo nuevo de F-012 es la segunda escritura**, que además es la primera que
toca **dos bases** —la de negocio y la documental— y la primera que
**transporta el PDF del parte**, con el DNI manuscrito del cliente dentro,
hasta Sigrid. Va por el endpoint de dominio de la pasarela y **exige
precondiciones de configuración que son de su dueño**, no nuestras: §3 bis y
§6.

> **Enmienda del 2026-09-24 (F-013) · dos filas de esta tabla cambian el día
> del corte, no antes.** La de SharePoint dice, literal, que compartimos el
> recurso con «IT» para el «Archivo de los PDF validados». Es verdad **hasta
> el corte de F-013** (`docs/DESPLIEGUE.md` §9): desde ese día el archivo va a
> la biblioteca «Documentos compartidos» del **sitio de Posventa** —decisión
> del humano del 2026-09-18, H1— con la estructura que ya usa Posventa, y
> **ahí sí escribimos en algo que es suyo**. Y la de `sigrid-api` gana **dos
> lecturas por cada parte que se archiva**, por `sql/read`. Ni un recurso de
> Azure nuevo, ni una tabla, ni una columna. El detalle, en §3 («Con F-013»).

## 2 · La base de datos: qué pedimos y qué no tocamos

```
Servidor  psql-albaranes-rs9k2      COMPARTIDO — no tocamos nada suyo
   └── Base  postventa              propia; la crea el humano, una vez
         └── Esquema  postventa     propio; lo crea el DDL de la aplicación
               ├── remesas                 una subida de partes
               ├── partes                  la unidad de trabajo, PK = hash del PDF
               ├── validaciones            la cola de revisión humana
               ├── archivos                traza de lo subido a SharePoint
               ├── cierres                 traza del cierre en Sigrid
               ├── preferencias_usuario    auto-cierre por usuario
               ├── usuarios_sigrid         el login del ERP de quien confirma
               ├── graficos                traza del parte adjunto en Sigrid
               ├── aprobaciones            CONGELADA desde F-028: ya no se escribe
               └── historico_estado        append-only: cada cambio de estado de un parte
```

Las diez van en el orden en que las crea el DDL (`01_esquema.sql` …
`11_historico_estado.sql`). Las tres penúltimas se listan **desde F-026**
(2026-09-12): `aprobaciones` es suya, y `usuarios_sigrid` (F-009) y `graficos`
(F-012) llevaban existiendo desde sus features sin figurar en este árbol —un
inventario incompleto es peor que no tenerlo, así que se corrigen al pasar. La
última, `historico_estado`, la añade **F-028** (2026-09-16), y es la misma
feature que congela `aprobaciones`.

**`aprobaciones` es la tabla nueva de F-026** y merece una línea aparte, porque
es la única del esquema que registra **una decisión humana que contradice a la
máquina**: que una persona dio por bueno un parte que la validación mandó a
revisión. Guarda el `oid` opaco de quien aprobó, el destino del que se rescató
el parte, los **códigos** de los motivos aprobados y una **huella** (`sha256`)
del veredicto sobre el que se decidió; **ni una copia del texto manuscrito** y
ningún binario. Cuando el veredicto cambia, la aprobación se **revoca** en la
misma operación que guarda la validación nueva: la fila no se borra nunca, se
marca. El detalle está en `specs/F-026-aprobacion-humana/design.md` §10.

> **Corrige lo que este párrafo dijo hasta el 2026-09-16 (F-028).** Sus dos
> últimas frases —«cuando el veredicto cambia, la aprobación se **revoca** en la
> misma operación que guarda la validación nueva: la fila no se borra nunca, se
> marca»— describían el **mecanismo vivo** de la decisión humana, y ya no lo es.
> **`postventa.aprobaciones` está CONGELADA**: sigue declarada en el DDL, sigue
> creándose en cada arranque y sigue consultable, pero **nadie escribe en ella**
> —ni un `INSERT`, ni un `UPDATE`, ni la revocación— desde F-028. El párrafo no
> se borra porque es lo que explica las filas que ya tiene dentro, escritas
> entre el 2026-09-12 y el 2026-09-16, que siguen siendo la prueba de aquellas
> decisiones y que **siguen consultándose** para auditar lo anterior a esa
> fecha.
>
> No se migró, y fue deliberado: su clave primaria es `hash_parte`, volverla
> append-only sería cambiarle la clave en una base **compartida y ya desplegada
> con datos reales**, y eso es una migración de verdad, no un `ADD COLUMN`. Se
> congela, se **siembra una vez** en la tabla nueva y se deja de escribir.

**`historico_estado` es la tabla nueva de F-028** (2026-09-16) y es la primera
del esquema cuya clave **no** es el `hash_parte`: es **append-only** y acumula
**todos** los cambios de estado de un parte, en orden —de qué estado a cuál,
quién lo decidió, cuándo y por qué—. Las diez anteriores se escriben con
`INSERT ... ON CONFLICT (hash_parte) DO UPDATE` porque de cada una solo
interesa el último valor; aquí interesan todos, que es justo lo que
`aprobaciones` no podía dar: un ciclo aprobar → rechazar → aprobar dejaba
**una** fila y borraba el rechazo por el camino, y después nadie podía
responder a quién lo rechazó y por qué.

Guarda el `oid` opaco de quien decide —**`NULL` cuando lo decidió la máquina**,
que no se sustituye por un autor inventado—, el **motivo** en texto libre de
quien revisa (tope de 500 caracteres en el borde) y la misma **huella**
(`sha256`) del veredicto sobre el que se decidió; **ni una copia del texto
manuscrito** y ningún binario, como en las demás. Es **constancia, nunca
criterio**: el estado de un parte **no se guarda, se deriva** del veredicto, de
la última decisión humana y de la traza de cierre, así que si mañana faltara
una fila el estado seguiría siendo el correcto y lo único perdido sería una
línea del relato. El detalle está en `specs/F-028-estado-del-parte/design.md`.

**La semilla es lo único que cruza las dos tablas, y ocurre una vez.** El DDL
de `11_historico_estado.sql` copia al histórico las aprobaciones **vigentes**
de F-026; es idempotente —`NOT EXISTS` por parte— y se ejecuta con el resto del
DDL al arrancar, antes de atender ninguna petición. Sin ella, el día del
despliegue todo parte aprobado a mano se habría quedado sin su decisión humana.
Las aprobaciones **ya revocadas no se siembran**: su efecto hoy es «no hay
aprobación», y resucitarlas como última decisión humana volvería a abrirles la
puerta del circuito que escribe en el ERP de producción.

**Base propia y esquema nominado, las dos cosas.** La base propia es cómo
aísla el ecosistema (`albaranes`, `partes`, `sigrid_dm`: un servidor, varias
bases). El esquema nominado —en vez del `public` que usan los demás— es
cinturón sobre tirantes: el `search_path` de nuestras sesiones es solo
`postventa`, **sin `public`**, así que una sentencia sin cualificar no puede
aterrizar donde no debe ni por descuido ni por copiar y pegar.

### Lo que este proyecto NO hace, y consta por escrito

| No hacemos | Por qué |
|---|---|
| `CREATE DATABASE` desde la aplicación | Crear bases al arrancar un servicio, en un servidor de producción ajeno, es justo lo que prohíbe `CLAUDE.md`. La base y el rol los crea el humano con `infra/crear_base_postventa.ps1`, una vez |
| `CREATE ROLE`, `GRANT`, `ALTER SYSTEM`, `CREATE EXTENSION` | Son cambios a nivel de servidor y afectan a los otros tres proyectos. Están en la lista negra del validador de DDL, que se ejecuta **antes de abrir la conexión** |
| Tocar el esquema `public` de ninguna base | Es donde trabajan `albaranes` y `partes` |
| Guardar los bytes de los PDF | El disco es compartido, solo crece y ya se llenó una vez (ver §5). Los PDF van a SharePoint; en la base quedan metadatos y hash |
| Guardar JSON crudo de la extracción | Duplicaría datos personales y engordaría el disco de todos |

El DDL se aplica **idempotente al arranque** (`CREATE ... IF NOT EXISTS`,
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`), es
el mismo patrón que ya usan `albaranes` y `partes`, y va protegido por un
`pg_advisory_lock` para que dos instancias arrancando a la vez no choquen. Un
DBA que mire `pg_stat_activity` nos verá con un `application_name` propio del
servicio y del entorno.

## 3 · SharePoint: dónde se archivan los partes

**Lo nuevo de F-006.** Con esta feature el proyecto pasa a consumir un segundo
recurso compartido: **SharePoint del tenant**, a través de **Microsoft Graph**.
Los dueños de `albaranes` y de `partes` —que ya archivan en ese mismo sitio—
tienen derecho a saber que hay otro inquilino y otra aplicación con permiso de
escritura sobre él.

> **Enmienda del 2026-09-24 (F-013) · el archivo se muda a la biblioteca de
> Posventa, y lo de abajo deja de describir el destino el día del corte.**
> Nada de esta sección se borra: es lo que está desplegado **hasta el corte**
> (`docs/DESPLIEGUE.md` §9) y lo que explica dónde están los 133 partes de IT.
> Pero cinco frases suyas dejan de ser ciertas ese día, y se citan tal cual:
>
> - el sitio, «El de **IT**, el mismo donde vive la biblioteca de albaranes»,
>   y la biblioteca, «**Propia de este proyecto**, no la de nadie más»;
> - la carpeta, «`SHAREPOINT_CARPETA_BASE`, y debajo **una carpeta por código
>   de obra**»;
> - el volumen, «Una subida por parte, sin listados de carpeta: se pide el
>   fichero por su nombre exacto, nunca el contenido entero de la carpeta de
>   una obra.»;
> - y la mudanza, que «es la feature **F-013**, y sale casi gratis porque la
>   ruta es configuración y no código».
>
> **Qué las invalidó, y quién.** El humano decidió el 2026-09-18 el destino
> —el sitio de **Posventa**, biblioteca «Documentos compartidos» (H1)— y la
> estructura —**la que ya usa Posventa**, `<cod> <OBRA> / PARTES INCIDENCIAS
> / <UNIDAD> / PARTES FIRMADOS` (H2)—, con la base en la raíz (D-1) y permiso
> para **crear toda la ruta que falte** (D-4). El 2026-09-24, con la medición
> de la obra piloto delante, cerró cómo se casan y cómo se crean las carpetas
> (parada T4, `specs/F-013-archivo-posventa/requirements.md` §0 ter). La ruta
> dejó de ser «configuración y nada más»: las carpetas de obra y de unidad
> **las crea Posventa a mano** y no salen de ningún dato que tengamos, así
> que hay que **encontrarlas** —listando— y, solo si no hay ninguna ni
> parecida, crearlas. Por eso F-013 no salió casi gratis. Lo que manda desde
> el corte está en las subsecciones **«Con F-013»**, al final de esta sección.

### Qué escribimos y dónde

| Qué | Valor |
|---|---|
| Sitio | El de **IT**, el mismo donde vive la biblioteca de albaranes. Por variable: `SHAREPOINT_SITE_ID` |
| Biblioteca | **Propia de este proyecto**, no la de nadie más. Por variable: `SHAREPOINT_DRIVE_ID` |
| Carpeta raíz | `SHAREPOINT_CARPETA_BASE`, y debajo **una carpeta por código de obra** |
| Qué se sube | El PDF de **un parte ya validado**, y nada más. Ni la remesa entera, ni ficheros intermedios, ni JSON |
| Cómo se llama | `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf` |
| Con qué identidad | **App-only** (client credentials) del app registration del proyecto |
| Con qué cliente | `httpx`, igual que `partes`. Decisión del humano del 2026-08-20 |

**Mientras estemos en dev es una biblioteca propia dentro del sitio de IT.** Al
pasar a producción el archivo se muda a la biblioteca de Posventa: es la
feature **F-013**, y sale casi gratis porque la ruta es configuración y no
código.

### Volumen esperado

Minúsculo, y por el mismo motivo que en §2: una remesa real ronda los **22
partes**, y un parte escaneado es del orden de cientos de kilobytes. El
crecimiento anual se cuenta en cientos de megabytes, no en terabytes. Una
subida por parte, sin listados de carpeta: se pide el fichero por su nombre
exacto, nunca el contenido entero de la carpeta de una obra.

> **Enmienda del 2026-09-24 (F-013) · deja de ser cierto.** Con `posventa` hay **hasta
> cuatro listados de carpetas** por parte, y alguna creación: ver «Con F-013 ·
> ahora sí hay listados de carpeta», más abajo.

### Permisos: qué necesitamos y qué tenemos hoy

Lo que la aplicación **necesita** es escribir en **una** biblioteca:
`Sites.Selected`, con esa biblioteca asignada explícitamente.

Lo que la aplicación **tiene hoy**, verificado el 2026-08-20, es más que eso:
además de `Sites.Selected`, dos permisos de aplicación que alcanzan a **todos
los sitios del tenant** y que vuelven irrelevante al primero. No es un fallo:
es lo que pasa al configurar `Sites.Selected`, que exige el paso extra de
asignar la biblioteca concreta por Graph, mientras que los amplios funcionan a
la primera.

**El humano decidió el 2026-08-20 arrancar así y recortar después**, para no
mezclar un cambio de configuración del tenant con una implementación. El
recorte es la feature **F-018 · Mínimo privilegio en Graph**, lo ejecuta el
humano en Azure —un agente no toca permisos del tenant— y **hasta que ocurra,
esta aplicación puede escribir en sitios de SharePoint que no son el suyo**.
Quien administre el tenant merece saberlo por escrito, y por eso está aquí.

### La puerta que impide subir desde un puesto de trabajo

`CLAUDE.md` prohíbe subir al SharePoint de Posventa desde local. Eso **no
depende de la disciplina de nadie**: el código lo impide con tres cierres
independientes.

1. `ENTORNO` tiene que ser `dev` o `pro`. Se comprueba en la fábrica **y en el
   constructor del adaptador**, así que componer las piezas a mano tampoco
   sirve.
2. `ARCHIVO_HABILITADO` tiene que estar encendido, y está **apagado por
   defecto en el código** (`config/settings.py`, `default=False`): un
   despliegue a medio configurar no sube nada.
3. La suite de tests no puede abrir conexiones de red, y ningún test construye
   un adaptador capaz de llegar a Graph.

La única subida real permitida se hace **desde el entorno desplegado**.

> **Desde el 2026-09-23, el cierre 2 sigue siendo cierto para el código, pero
> ya no para el despliegue.** El humano decidió ese día que
> `desplegar_backend.ps1` publique **las dos** ventanas de escritura
> **abiertas** (*«quiero que por defecto publique abierto, no cerrado»*; *«Las
> dos»*): Posventa ya usa el servicio en real y cada despliegue les cerraba el
> archivo y el cierre. El script fija `ARCHIVO_HABILITADO=true` y
> `CIERRE_HABILITADO=true` salvo con `-VentanasCerradas`, que las cierra las
> dos. En un puesto de trabajo nada cambia: el defecto del código sigue
> apagado y el cierre 1 lo impide por su cuenta. En el entorno desplegado, lo
> que decide quién sube es la plataforma —Easy Auth en el host desnudo y la
> sesión del grupo de Posventa en el front, `docs/DESPLIEGUE.md` §5 bis—, no
> la ventana. El riesgo aceptado, en `docs/DESPLIEGUE.md` §4 bis.

### Qué se rompe si alguien toca algo

| Si alguien... | Nos pasa esto | Aviso |
|---|---|---|
| Mueve, renombra o borra **la biblioteca** de dev | Dejamos de archivar: cada parte apto acaba con traza en estado `error`. No se pierde nada, el parte se reintenta, pero no avanza ni un cierre | Es nuestra: nadie más debería tocarla |
| Revoca el **permiso** de la aplicación sobre el sitio | Igual que lo anterior, y con un `403` que **no se reintenta**: la aplicación no insiste contra un permiso denegado | Coordinar con IT antes |
| Cambia la carpeta raíz sin avisar | Los partes nuevos se archivan en otro sitio y los viejos se quedan donde estaban. El archivo de Posventa queda partido en dos | Es cambiar `SHAREPOINT_CARPETA_BASE`: hay que decirlo |
| Rota el secreto de la aplicación sin actualizarlo | Dejamos de archivar con un `401`, tampoco reintentable | El secreto vive en Key Vault, nunca en el repositorio |
| Borra a mano un parte ya archivado | No lo detectamos: la traza sigue diciendo `archivado` y no se vuelve a subir | Reprocesar el parte no basta; hay que borrar su traza |

Y al revés, lo que **nosotros** podemos romperles: mientras los permisos sigan
siendo los amplios de hoy, esta aplicación **podría** escribir en cualquier
sitio del tenant. No lo hace, solo toca su biblioteca, pero la única garantía
real es el recorte de **F-018**.

### Con F-013 · sitio, biblioteca y estructura (desde el corte)

**Estado a 2026-09-24**: F-013 está implementada en su rama y **no
desplegada**. Hasta el corte (`docs/DESPLIEGUE.md` §9) todo lo de arriba sigue
igual, con `SHAREPOINT_ESTRUCTURA=por_obra`. El corte pone
`SHAREPOINT_ESTRUCTURA=posventa`, y desde ese momento:

| Qué | Con `posventa` |
|---|---|
| Sitio | El de **Posventa**. Por variable, `SHAREPOINT_SITE_ID`, que se carga en el Key Vault en el corte; ni un identificador en el repositorio |
| Biblioteca | «Documentos compartidos», la de por defecto del sitio: **la de Posventa, sincronizada por OneDrive en sus equipos**. Por variable, `SHAREPOINT_DRIVE_ID` |
| Carpeta base | La **raíz de la biblioteca** (D-1): `SHAREPOINT_CARPETA_BASE` vacía |
| Ruta | `<carpeta de obra>/PARTES INCIDENCIAS/<carpeta de unidad>/PARTES FIRMADOS/<fichero>` |
| Nombre del fichero | El de siempre, `<cod obra> - <cod incidencia> PARTE FIRMADO.pdf`, sin cambios |

**Cada carpeta se encuentra, no se compone.** Ni Sigrid ni el papel dan el
nombre de las carpetas de Posventa; como mucho dan con qué casarlas:

- **Obra**: casa por su número. La primera palabra del nombre, solo cifras,
  tiene que valer lo mismo que el código de la obra como entero; el resto del
  nombre no cuenta. La carpeta real de la obra piloto es `677  MIRASIERRA`
  —sin el cero y con dos blancos— y casa con la `0677`; `06770 X` no.
- **`PARTES INCIDENCIAS`**: por su nombre, sin mayúsculas, tildes ni blancos
  de más.
- **Unidad**: la de **Sigrid** para esa reclamación —nunca la que imprime el
  papel, que es lectura de IA—, casada por su clave: `VILLA 05` casa con
  «Viviendas Bloque Villa 5»; `VILLA 15` no.
- **Hoja**: `PARTES FIRMADOS` o, como **única** forma alternativa,
  `PARTES FIRMADO` (`SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA`: la hoja de
  VILLA 02 se llama así). Con las dos en la misma unidad, 409.

**Cuándo se crea una carpeta, y con qué nombre.** Solo cuando en un nivel **no
hay ninguna que case ni ninguna parecida** —otra grafía del mismo número de
obra, del mismo número de unidad o de la palabra del tramo—: una parecida
bloquea con 409, porque crear al lado partiría el archivo de Posventa en dos,
a la vista en todos sus equipos. Los nombres: la obra, `<código> <nombre de la
obra en Sigrid>`; los dos tramos, su literal; la unidad, **`VILLA NN`**,
derivado del código de la unidad en Sigrid (`0677.03VILLA 13.` → `VILLA 13`),
y si el código no tiene esa forma, 409: no se inventa. Una carpeta cada vez,
dentro de un padre que existe, y **después** de dejar la traza `pendiente`.
Cada una sale en los `avisos` de la respuesta y en el log como
`F-013 carpeta creada: <ruta>`. `SHAREPOINT_CREAR_CARPETAS=false` es el freno:
no se crea nada, y una carpeta que falta es 409 `sin_carpeta_<nivel>`.

En la obra piloto, la 0677: se usan las siete carpetas `VILLA 01` …
`VILLA 07`; en `VILLA 04`, que no tiene subcarpetas y guarda 142 partes
sueltos, se crea `PARTES FIRMADOS` y **los sueltos no se tocan**; y se crean
`VILLA 08` … `VILLA 15` según lleguen sus partes.

> **Enmienda del 2026-09-25 (F-049) · las villas se crean con tres
> cifras.** Esta sección decía, literal, que la unidad se deriva del código
> de Sigrid *«(`0677.03VILLA 13.` → `VILLA 13`)»*, y que en la 0677 se crean
> *«`VILLA 08` … `VILLA 15` según lleguen sus partes.»* **Qué lo invalidó**:
> en el paso 2 del corte (2026-09-25), el script 23 mostró que Posventa ha
> reorganizado las carpetas de unidad de la 0677 a `VILLA 001` …
> `VILLA 007`, `VILLA 012` y `VILLA 013`; y el humano decidió ese día que el
> sistema cree **siempre con tres cifras**, en todas las obras (F-049). Desde
> hoy: `0677.03VILLA 13.` → `VILLA 013`; `VILLA 008`; con 1.000 o más, tal
> cual (`VILLA 1000`). En la 0677 se usan las nueve carpetas que ya existen y
> se crean `VILLA 008` … `VILLA 011`, `VILLA 014` y `VILLA 015` según lleguen
> sus partes. **El casado no cambia**: compara números, y `VILLA 001`,
> `VILLA 01` y «Viviendas Bloque Villa 1» son la misma villa; si en una obra
> conviven `VILLA 01` y `VILLA 001`, esa unidad da 409 `unidad_ambigua` hasta
> que Posventa deje una.

**El sistema no borra, no mueve y no renombra nunca** una carpeta ni un
fichero de Posventa: el puerto que lista y crea tiene **dos** operaciones y
ninguna más. Tampoco lista ni nombra los ficheros que Posventa sube a mano:
con su nomenclatura (`RS26.08 – 0123 PARTE FIRMADO`, sin obra) no coincide la
nuestra, así que en una carpeta donde ya subieran un parte a mano convivirán
dos ficheros del mismo parte. No se deduplica por contenido.

### Con F-013 · ahora sí hay listados de carpeta

Encontrar las carpetas exige listarlas: **hasta cuatro listados** por parte
—raíz, obra, `PARTES INCIDENCIAS` y unidad—, un `GET` de los hijos con
`$select=name,folder`, **solo carpetas**, nunca los ficheros (sus nombres
pueden llevar el de un cliente), y siguiendo **todas** las páginas. El enlace
a la página siguiente (`@odata.nextLink`) **solo se sigue si apunta a Graph**
(`https://graph.microsoft.com/v1.0/`): lleva dentro el identificador de la
biblioteca y el token viaja con cada página, así que un enlace a otro sitio es
`ArchivoFallido` —502— sin pedirlo, y el enlace no se registra nunca. Debajo de
una carpeta que se va a crear no se lista: no puede tener nada.

Crear es un `POST` por nivel con `conflictBehavior=fail`; un `409` de Graph
cuenta como «ya existe», así que dos partes a la vez crean **una** carpeta.
Volumen: una remesa de 22 partes son del orden de 130 llamadas, casi todas
lecturas. Sin caché entre partes: una caché escondería la carpeta que
Posventa acaba de crear.

**Permisos**: con los amplios de hoy, la aplicación escribirá en el sitio de
Posventa sin que nadie le conceda nada. Al recortar a `Sites.Selected`
(**F-018**) habrá que conceder **el sitio de Posventa** con escritura.

### Con F-013 · archivar depende de `sigrid-api`: dos lecturas por parte

Con `posventa`, `/api/archivar` necesita saber **en Sigrid** de qué obra y de
qué unidad es la reclamación. Son **dos lecturas** por
`POST /api/sql/read`, parametrizadas, y **ninguna escritura**:

1. **La ubicación de la reclamación**: reclamación → unidad de posventa → obra
   (`rcp` → `upv` → `obr`; las tres son «propiedades de `con`»), con el código
   y el nombre de la obra y de la unidad. Hasta 10 filas: ninguna es
   `reclamacion_no_localizada`; varias, `reclamacion_ambigua`; sin unidad o sin
   obra, `reclamacion_sin_unidad`. Si la obra de Sigrid no es la del parte,
   `obra_no_coincide`: dos fuentes independientes tienen que decir la misma
   obra.
2. **Las unidades de posventa de las obras con el mismo número** (para la 0677,
   `LIKE '%677'` y `NOT LIKE '%[^0]%677'`; después el dominio vuelve a filtrar
   por número). Hasta 1.000 filas, el techo de la pasarela: si llegan 1.000,
   la lista puede venir cortada y es `unidades_sin_verificar`. Dos obras de
   Sigrid con el mismo número irían a la misma carpeta de Posventa, y eso es
   `obra_numero_no_unico`; una carpeta de unidad que casaría con dos unidades
   de la obra, `unidad_carpeta_compartida`.

Se lee **sin `CIERRE_HABILITADO`**: con la ventana del ERP cerrada se sigue
pudiendo archivar. Sí hace falta el resto de la configuración de Sigrid
(`SIGRID_API_BASE_URL`, `SIGRID_API_KEY`, `SIGRID_BASE_DATOS`,
`SIGRID_TIP_RECLAMACION`) y `ENTORNO` en `dev` o `pro`. Fuera de esos dos
entornos la lectura se niega con `ArchivoDeshabilitado` —el 503 de «archivar
deshabilitado»—, no con el error del cierre, porque no se ha intentado
escribir en el ERP. Si la pasarela no responde, tarda o devuelve algo que no
sirve, es `UbicacionNoDisponible`: **503**, y no se sube ni se crea nada. **No**
se recurre a la unidad del papel (D-7). Una respuesta marcada como cortada con
**menos** filas de las pedidas también es 503: el techo de la pasarela es
configurable, y una lista cortada por debajo escondería la segunda obra.

Ni la referencia de la obra en el ERP ni el nombre de la unidad salen en un
log, en una respuesta ni en la base; sí los códigos, el número de filas y los
segundos de cada lectura. El tiempo de la segunda lectura contra el ERP real
está **sin medir**: lo dirá el log del primer archivado,
`F-013 unidades leídas en Sigrid: obra=… filas=… segundos=…`.

### Con F-013 · el destino no resuelto: 409 con motivo

Cuando una carpeta del camino no se puede decidir sin una persona, **no se
sube nada ni se crea ninguna carpeta**: `/api/archivar` responde **409** con
`error` —qué tiene que hacer una persona—, `motivo` —un código— y `candidatas`
—nombres de carpeta, nunca un identificador—, y la traza del parte queda en
`error` con el código. En cuanto alguien arregla la carpeta, el siguiente
archivado lo sube, sin tocar la base. Los códigos:

| Motivo | Qué pasa | Qué hace una persona |
|---|---|---|
| `reclamacion_no_localizada` | Sigrid no tiene esa reclamación | Revisar el número de incidencia del parte |
| `reclamacion_ambigua` | Sigrid devuelve varias | Mirarlo en Sigrid |
| `reclamacion_sin_unidad` | No cuelga de ninguna unidad de posventa, o la unidad de ninguna obra | Asignarla en Sigrid |
| `obra_no_coincide` | La obra de Sigrid no es la del parte | Revisar el código de obra guardado |
| `obra_numero_no_unico` | Más de una obra de Sigrid (o ninguna) con ese número | Decidirlo con Posventa: el sistema no elige |
| `unidades_sin_verificar` | La lista de unidades llegó al techo de 1.000 filas | Avisarnos: no se puede comprobar |
| `obra_ambigua`, `incidencias_ambigua`, `unidad_ambigua`, `firmados_ambigua` | Casa más de una carpeta en ese nivel | Dejar una, renombrando la otra |
| `obra_parecida`, `incidencias_parecida`, `unidad_parecida`, `firmados_parecida` | No casa ninguna y hay alguna parecida | Renombrar la buena, o crear la correcta |
| `sin_carpeta_obra`, `sin_carpeta_incidencias`, `sin_carpeta_unidad`, `sin_carpeta_firmados` | Falta ese nivel y crear está apagado | Crearla a mano, o volver a encender crear |
| `nombre_carpeta_imposible` | El nombre que habría que crear lleva algo que SharePoint no admite | Corregir el dato en Sigrid, o crear la carpeta a mano |
| `unidad_sin_nombre_derivable` | Hay que crear la unidad y su código de Sigrid no tiene la forma `<obra>.<grupo>VILLA <n>.` | Crear la carpeta a mano |
| `nombre_no_casaria` | La carpeta que se crearía no se volvería a encontrar en el siguiente archivado | Crear la carpeta a mano |
| `unidad_carpeta_compartida` | Esa carpeta de unidad casaría con dos unidades de Sigrid, o con ninguna | Renombrar para distinguirlas |

### Con F-013 · lo que se queda en IT

> **Enmienda del 2026-09-24 (F-013), que recoge las del 2026-09-18 y del
> 2026-09-22.** La premisa original, H4 del 2026-09-18: *«Lo ya archivado en
> IT se queda en IT, sin migración, y se documenta que sigue allí»*. El
> humano la enmendó en dos frases: el 2026-09-18, *«lo que esta en IT eran
> pruebas, se puede olvidar»*, y el 2026-09-22, *«los partes en IT se pueden
> olvidar, pero no borrar»*.
>
> Queda así: los **133** partes archivados hasta el corte —medidos el
> 2026-09-18 con `infra/25_mediciones_despliegue.ps1`, todos `archivado` y
> todos en la biblioteca de IT— siguen allí: **no se migran, no se borran y
> no se les retira la traza** (`postventa.archivos` los sigue diciendo
> `archivado`, con su biblioteca). Como la capa L1 de F-033 corta por `hash` y
> estado, **nunca se volverán a subir**, y por eso el archivo de Posventa **no
> los contiene ni los contendrá**: tendrá lo que se archive a partir del
> corte. Y a propósito **no se documenta cómo localizarlos**: eran pruebas.
>
> Un matiz que se deja así a sabiendas (H-3 de F-034): la puerta de archivo
> del gráfico y del cierre (`exigir_parte_archivado`) mira el **estado** de la
> traza y **no su biblioteca**, así que uno de esos partes **sí** puede
> adjuntarse y cerrarse en Sigrid. Es coherente con «olvidar sin borrar»: el
> parte está archivado, aunque no en Posventa.

### Deshacer una carpeta creada por error (R43)

**El sistema no borra, no mueve ni renombra** carpetas ni ficheros, en ningún
caso. Si una carpeta que creó no le sirve a Posventa —el nombre no les vale, o
apareció al lado de la suya—, **lo hace una persona**, en este orden:

1. **Parar**: `infra/22_ventana_archivo.ps1 -Cerrar`, sin redesplegar, si
   puede seguir llegando algo a esa carpeta; o, si basta con dejar de crear,
   `$CrearCarpetasArchivo = "false"` y redesplegar (`docs/DESPLIEGUE.md` §9).
2. **Saber qué hay dentro** con la consulta de abajo, de solo lectura sobre
   `postventa.archivos`: los partes que el sistema archivó en esa carpeta y en
   lo que cuelga de ella. La ruta se escribe como sale en el aviso de
   «carpeta creada», sin barra inicial.
3. **Mover** cada PDF a la carpeta buena, **dentro de la misma biblioteca**.
   El `item_id` y el enlace de la traza siguen al fichero; la columna
   `carpeta` se queda con la ruta vieja, y no se persigue.
4. **Borrar o renombrar** la sobrante. El borrado va a la **papelera del
   sitio** y se propaga a los OneDrive sincronizados de Posventa. Si la buena
   no existía y el nombre creado solo es feo, lo sencillo es **renombrarla**:
   el siguiente archivado la encuentra si sigue empezando por el número de la
   obra (obra) o casando con la unidad (unidad); si no, da 409 `…_parecida`,
   que es el aviso correcto.
5. Si lo que no servía era el nombre, se enmienda la regla (R36 o R37 de
   F-013) **antes** de volver a abrir.

La consulta, con la cuenta de lectura y sin copiar a ningún fichero ni el
`drive_id` ni el `item_id`:

```sql
SELECT a.hash_parte, a.nombre_fichero, a.carpeta, a.estado, a.archivado_at_utc
FROM postventa.archivos AS a
WHERE a.carpeta = '<ruta de la carpeta>'
   OR starts_with(a.carpeta, '<ruta de la carpeta>/')
ORDER BY a.archivado_at_utc;
```

### Con F-013 · qué se rompe si alguien toca algo

| Si alguien... | Nos pasa esto | Aviso |
|---|---|---|
| Posventa **renombra la carpeta de obra** | Si el nombre sigue empezando por el número de la obra y un blanco, nada: se sigue encontrando. Si no (`MIRASIERRA 677`), 409 `obra_parecida` en cada parte de esa obra | Lo ya archivado sigue en su sitio: la traza guarda el `item_id` y el enlace, que siguen al fichero; su columna `carpeta` se queda con el nombre viejo |
| Posventa renombra una carpeta de unidad o una hoja | Si sigue casando, nada; si no, 409 `unidad_parecida` o `firmados_parecida` | — |
| Posventa crea una segunda carpeta que empieza por el mismo número de obra (`0677 MIRASIERRA FASE 2`) | 409 `obra_ambigua` en toda la obra: el sistema no elige | Hablarlo antes con nosotros |
| Posventa borra una carpeta que había creado el sistema | El siguiente parte de esa unidad la vuelve a crear, si no hay ninguna parecida | Para que no vuelva: el procedimiento de arriba |
| Alguien tiene abierto en su OneDrive el PDF que se va a reemplazar | Graph responde `423 Locked`: `ArchivoFallido`, **502**, y **no se reintenta solo** | Lo reintenta una persona |
| La pasarela `sigrid-api` cae o no responde | Con `posventa`, **503** en cada parte que haya que archivar, sin subir ni crear nada. Lo que ya consta archivado responde bien: L1 corta antes de leer Sigrid | Con `por_obra`, nada de esto |
| Nuestra Function queda con `sigrid-api` sin configurar | Con `posventa`, **503** en todo archivado, e **incluso un parte ya archivado responde 503**: el lector de Sigrid se construye en el borde, antes del paso, y falla antes de que L1 devuelva la traza. **Decisión del líder del 2026-09-24: se deja así**, fallando cerrado —no se sube ni se lee nada—, y se documenta aquí | La configuración de Sigrid ya la necesita el cierre |
| Alguien deja `SHAREPOINT_ESTRUCTURA` mal escrita | **503**: la fábrica la rechaza antes de pedir el token, y el borde también si el archivador le llegara ya construido | Solo valen `por_obra` y `posventa`, exactos |
| Se despliega con la base vacía y **el vacío no llega** a la App Setting | La base vuelve a su defecto del código, `Postventa`, que no existe en la raíz de Posventa: **502** sin subir ni crear nada | El paso 6 del runbook lo comprueba |
| Alguien cambia `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` | Esa forma deja de contar como hoja; donde esté sola, pasa a ser parecida: 409 | Es la hoja de VILLA 02 |
| Se recorta a `Sites.Selected` (F-018) sin conceder el sitio de Posventa | `403`, no reintentable: dejamos de archivar | Conceder el sitio de Posventa con escritura |

## 3 bis · Sigrid: qué escribimos en el ERP de producción (F-009)

**Hasta F-009 este proyecto solo leía de Sigrid.** Ahora escribe, y esta
sección existe para que quien administre la pasarela o el ERP sepa exactamente
qué y con qué límites. El acceso es, como para todo el ecosistema, **a través
de `sigrid-api`**: nadie se conecta al SQL Server por su cuenta.

### Qué escribimos, exactamente

Dos sentencias, en **un solo batch transaccional** de `POST /api/sql/write`,
con `max_affected_rows = 2`:

1. **El estado de la reclamación** (`dbo.con.est`), al estado de cierre. Ese
   estado se resuelve **en ejecución** consultando `dbo.conest` por su
   **código**; el número no está escrito en ninguna parte de nuestro código y
   un test lo comprueba barriendo el árbol. El `WHERE` lleva el identificador
   de la reclamación, su tipo **y el estado de origen que se leyó en el
   dry-run**: si alguien la movió entretanto, no se aplica nada.
2. **Una fila de auditoría** en `dbo.log`, que es lo que el propio ERP escribe
   al cerrar un parte y lo que un `UPDATE` a secas se dejaría por el camino.
   Sus campos se copian de la reclamación dentro del propio SQL, y su
   identificador se reserva dentro de la misma sentencia, con bloqueo: la
   tabla no tiene IDENTITY y la pasarela no protege esa reserva.

**Nada más.** Ni `con.tiemod`, ni la solución de la reclamación, ni ninguna
fecha: F-008 midió que el proceso del ERP tampoco los toca.

### Cómo se reconocen nuestros cierres, y cómo se revierten

La fila de `dbo.log` lleva un texto propio, **`Cerrar parte
(postventa-incidencias)`**. Eso hace dos cosas a la vez:

- **sigue apareciendo en los informes de Posventa**, que filtran por el prefijo
  `Cerrar parte`;
- y **distingue nuestros cierres de los manuales con un solo `LIKE`**, que es
  lo que hace reversible el piloto: los cierres se deshacen en el ERP, y si
  esto se tuerce se sabe exactamente qué revertir.

### Quién firma el cierre

El login de Sigrid de **la persona que confirma**, nunca un usuario técnico ni
un valor constante. Se resuelve contra la tabla propia
`postventa.usuarios_sigrid`, y si no hay correspondencia se deriva un candidato
del correo del usuario y **se verifica por lectura contra `dbo.usu`** antes de
escribir nada. Si el ERP no lo confirma, **no se cierra**.

### Las puertas, de fuera adentro

1. **El entorno.** Escribir solo se permite con `ENTORNO` en `dev` o `pro`.
2. **El interruptor.** `CIERRE_HABILITADO`, apagado por defecto **en el
   código**. Se comprueba en la fábrica **y en el constructor del adaptador**:
   componer las piezas a mano tampoco deja escribir. **Desde el 2026-09-23 el
   despliegue lo publica encendido** (salvo `-VentanasCerradas`): en el
   entorno desplegado esta puerta está abierta por decisión del humano, y
   **cualquier versión desplegada escribe en Sigrid de producción sin una
   puerta manual**; y mientras F-034 no esté desplegada, `/api/adjuntar` y
   `/api/cerrar` toman el número de incidencia del cuerpo de la petición.
   Riesgo aceptado, detallado en `docs/DESPLIEGUE.md` §4 bis.
   **Nota del 2026-09-23 (F-034): desde el despliegue de F-034**, los dos
   endpoints dejan de tomar del cuerpo el número de incidencia y el estado de
   archivo: deciden con lo **guardado** del parte y un cuerpo que no cuadre
   recibe 409 sin llegar al ERP. Hasta ese despliegue, la frase anterior
   sigue siendo cierta.
3. **El dry-run.** `POST /api/cerrar` lee y no escribe salvo que se le pida
   `commit` explícitamente.
4. **La confirmación.** Con `commit` hace falta además la confirmación del
   usuario o su preferencia de auto-cierre guardada.
5. **La guardia de red de la suite**, que impide que un test abra la conexión.

Y una que no es una puerta sino una decisión: **la escritura no se reintenta
nunca**. Un tiempo agotado no dice que el ERP no haya escrito; dice que no nos
hemos enterado. El reintento lo pide una persona.

### Volumen esperado

Dos sentencias por incidencia cerrada, y una lectura por dry-run. En el piloto
de Mirasierra eso son decenas de escrituras, no miles: muy por debajo de
cualquier límite de la pasarela.

### Qué escribimos como GRÁFICO, exactamente (F-012)

**Desde F-012 hay una segunda escritura, y va ANTES que el cierre.** El PDF del
parte firmado se adjunta a la reclamación como **gráfico** de Sigrid, con
`POST /api/sigrid/concepto-grafico` — el endpoint de dominio de la pasarela, que
es la **única** vía por la que se escribe en la base documental.

Son **tres filas en dos bases**, y las escribe la pasarela en **una
transacción**: el binario en la base documental, sus metadatos en la de negocio
—con el mismo `cod` y el mismo `emp`— y el enlace con la reclamación. Este
servicio **no compone ni una sentencia**: manda el fichero y ocho campos.

Lo que mandamos, y lo que no:

- `database`: la de **negocio**. **Nunca nombramos la documental**: la elige la
  pasarela desde su propia configuración.
- `conide` y `contip`: salen de **la reclamación leída** en el dry-run, no de
  una constante ni de la configuración.
- `gratipide`: `SIGRID_GRATIPIDE_PARTE` (35 = `PV002`, «POSTVENTA:Fotos
  Reparaciones»), que es la clase bajo la que Posventa tiene sus partes
  firmados.
- `nom`: **el mismo nombre con el que el parte está en SharePoint**. Un
  documento, un nombre, dos sitios.
- `res`: `PARTE FIRMADO`, que es lo que Posventa teclea.
- `usu`: el login de quien confirma, el mismo que firma el cierre.
- `contenido` y su `sha256`, que la pasarela **coteja** antes de escribir.
- **No mandamos** `cod`, `ide`, `vin`, `pos`, `emp` ni la base documental: todo
  eso lo decide la pasarela con constantes medidas contra el ERP.

**No escribimos ninguna fila en `dbo.log` por el gráfico**, y es deliberado: el
propio ERP tampoco lo hace al importar uno (0 filas con `tab='gra'` en 8,4
millones). Escribir una nos haría anómalos respecto a los 13.450 gráficos de
Posventa — el argumento inverso al del cierre, donde el ERP **sí** escribe.

**El orden es la garantía.** No hay atomicidad entre dos llamadas HTTP, así que
se sustituye por **orden más idempotencia**: primero el gráfico, después el
cierre, y el cierre **exige** que el gráfico conste adjuntado en nuestra traza.
Un fallo entre los dos deja la reclamación **abierta con su parte dentro**, que
es un estado inocuo y del que se sale reintentando.

**El reintento del gráfico es seguro**, al revés que el del cierre: el endpoint
es idempotente por tamaño y `sha256`, comprobado dos veces por la pasarela —al
leer y otra vez dentro de la transacción—. Por eso nuestros mensajes de error
lo dicen: quien los lea puede volver a intentarlo sin abrir Sigrid.

### Lo que F-009 NO exige, y lo que F-012 SÍ exige (RESUELTO)

**F-009 no exige ningún cambio en el repositorio `sigrid-api`.** Las dos
sentencias caben en `POST /api/sql/write` tal y como está desplegado: `UPDATE` e
`INSERT` están permitidos y la base de negocio está en la lista blanca de
escritura. Se comprobó leyendo la configuración de la Function App, sin ver
ningún valor.

**F-012 sí exigía algo de otro dueño, y el 2026-09-06 quedó RESUELTO.** Lo que
sigue se conserva porque explica de dónde viene la precondición que hoy
declaramos en §6; lo que hay que leer primero es la resolución, al final del
bloque.

Lo que se descubrió al comprobar lo anterior, y que quien cogiera esa feature
debía saber el primer día:

> Subir el parte a Sigrid como gráfico exige **escribir en dos bases**: los
> metadatos y el enlace van en la base de negocio, pero **el binario vive en la
> base documental**. Y la configuración desplegada de la pasarela tiene la base
> de negocio como **única** escribible: la documental queda fuera de
> `ALLOWED_WRITE_DATABASES` **a propósito** («escritura SOLO en negocio»).
>
> Consecuencia: F-012 **no se resuelve con un endpoint de dominio nuevo**. Hace
> falta además habilitar la escritura en la base documental, y eso es una
> decisión del **dueño de `sigrid-api`** que afecta a todo el ecosistema, no
> solo a este proyecto. Con la configuración de hoy, subir el PDF a Sigrid **no
> tiene por dónde hacerse**.
>
> Esto **no bloquea F-009**, que solo escribe en la base de negocio.

**Actualización del 2026-09-03: el endpoint ya está especificado, y la premisa
del párrafo anterior era peor de lo que parecía y mejor de lo que se creía.**
La base documental **no es una réplica de solo lectura**: es una base normal en
la **misma instancia** de SQL Server —una sola pareja host/puerto en la
configuración de la pasarela, solo cambia el nombre de la base— y **el propio
ERP le escribe** cada vez que Posventa importa un documento. Lo que hay es una
**política** de la pasarela, más un permiso que probablemente falte en el motor.

> La especificación del endpoint vive **en el repositorio que la implementará**,
> como manda la regla de propiedad del ecosistema:
> `sigrid-api/docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md`
> (rama `docs/propuesta-escritura-documental`, sin desplegar).
> Aquí no se duplica. El resumen de qué resuelve y qué deja abierto está en
> `progress/impl_spec_escritura_documental.md`.

**RESUELTO el 2026-09-06.** El dueño de `sigrid-api` implementó y desplegó el
endpoint (su F-004, mergeado en `dev`): `POST /api/sigrid/concepto-grafico`,
contrato en `azure-apps/sigrid_api.md` §8.8. Así que **F-012 no cruza ninguna
frontera**: consume un endpoint de dominio, exactamente como `remesas` o
`partes` consumen `sql/read`, y no pide ningún cambio en aquel repositorio.

Lo que sigue siendo suyo, y por eso es una **precondición** y no una
dependencia de código, son sus App Settings —`SIGRID_DOCUMENT_WRITE_ENABLED`,
`SIGRID_DOCUMENT_WRITE_DATABASE`, `SIGRID_DOCUMENT_ALLOWED_CONTIP`,
`SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` y `SIGRID_DOCUMENT_MAX_BYTES`—. Qué se
rompe si las cambia está en **§6**, y **no se tocan desde aquí**: se piden.

## 4 · Variables de entorno (nombres, nunca valores)

Los nombres son deliberadamente los que ya usa el ecosistema, para que quien
despliegue no tenga que aprender dos vocabularios.

| Variable | Obligatoria | Notas |
|---|---|---|
| `PG_HOST` | sí, para persistir | Sin ella la aplicación arranca igual: `/health` no necesita base |
| `PG_PORT` | no | Puerto estándar de PostgreSQL por defecto |
| `PG_DB` | no | Por defecto, la base propia del proyecto |
| `PG_USER` | sí, para persistir | Rol de aplicación, propio de este proyecto |
| `PG_PASSWORD` | sí, para persistir | **Secreto**. En Azure va por referencia a Key Vault; nunca en el repositorio, ni en `.env.example`, ni en un fichero de despliegue |
| `PG_SCHEMA` | no | Por defecto, el esquema propio |
| `PG_SSLMODE` | no | Por defecto exige TLS, como pide Azure Flexible Server |
| `PG_MAX_CONEXIONES` | no | Techo bajo a propósito (§5, conexiones) |
| `PG_STATEMENT_TIMEOUT_S` | no | Ninguna consulta nuestra se eterniza en un servidor ajeno |
| `PG_LOCK_TIMEOUT_S` | no | Ni espera indefinidamente por un bloqueo |
| `PG_IDLE_IN_TRANSACTION_TIMEOUT_S` | no | Ni deja una transacción abierta ocupando una conexión |


### Las de SharePoint (F-006)

| Variable | Obligatoria | Notas |
|---|---|---|
| `ARCHIVO_HABILITADO` | no | **Interruptor maestro, apagado por defecto en el código.** Sin encenderlo no se sube nada, pase lo que pase. **El despliegue lo publica encendido desde el 2026-09-23** (salvo `-VentanasCerradas`) |
| `SHAREPOINT_SITE_ID` | no | El sitio del destino. No lo usa el adaptador, que va directo a la biblioteca; lo usan el script de verificación y este documento |
| `SHAREPOINT_DRIVE_ID` | sí, para archivar | La biblioteca donde se archivan los partes |
| `SHAREPOINT_CARPETA_BASE` | no | Carpeta raíz; debajo, una por código de obra |
| `GRAPH_TENANT_ID` | sí, para archivar | Tenant contra el que se pide el token |
| `GRAPH_CLIENT_ID` | sí, para archivar | La aplicación con la que se archiva |
| `GRAPH_CLIENT_SECRET` | sí, para archivar | **Secreto**. En Azure va por referencia a Key Vault; en local, solo en el `.env`, que no se versiona. Jamás en un log ni en un mensaje de error |
| `GRAPH_TIMEOUT_S` | no | La Function corta a los 230 s: una llamada colgada no puede comérselos |
| `GRAPH_REINTENTOS` | no | Intentos ante errores transitorios. Un `403` o un `404` **no** se reintentan |

### Las de F-013 (el destino de Posventa)

| Variable | Obligatoria | Notas |
|---|---|---|
| `SHAREPOINT_ESTRUCTURA` | no | `por_obra` (por defecto; la carpeta de F-006) o `posventa` (la estructura de Posventa, §3 «Con F-013»). Cualquier otro valor, exacto, es un error de configuración: **503** antes de pedir el token. El despliegue la escribe desde `$EstructuraArchivo`, `por_obra` **hasta el corte** |
| `SHAREPOINT_CARPETA_INCIDENCIAS` | no | El literal del segundo tramo, `PARTES INCIDENCIAS` por defecto. Solo cuenta con `posventa` |
| `SHAREPOINT_CARPETA_FIRMADOS` | no | El literal de la hoja, `PARTES FIRMADOS` por defecto. Es el nombre con el que se **crea** |
| `SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA` | no | La **única** otra forma admitida de la hoja, `PARTES FIRMADO` por defecto (la de VILLA 02); vacía, ninguna. **Nunca se crea**. El despliegue no la escribe: vale su defecto |
| `SHAREPOINT_CREAR_CARPETAS` | no | Si se pueden crear los niveles que falten, **encendida** por defecto (D-4). `false` es el freno: una carpeta que falta es 409. El despliegue la escribe desde `$CrearCarpetasArchivo`, `true` |

No hay ninguna variable para elegir de dónde sale el nombre de una unidad
creada: es `VILLA NN`, con una regla fija (§3).

> **Enmienda del 2026-09-24 (F-013) a `SHAREPOINT_CARPETA_BASE`.** La tabla de
> F-006 dice de ella, literal, «Carpeta raíz; debajo, una por código de obra».
> Con `posventa`, **vacía es la raíz de la biblioteca** —D-1, decisión del
> humano del 2026-09-18— y debajo va la estructura de Posventa; con
> `por_obra`, vacía pasa a ser un **error de configuración**, porque dejaría
> las carpetas por código sueltas en la raíz. El despliegue la escribe desde
> `$CarpetaBaseArchivo`: `Postventa` hasta el corte, vacía después. Y las de
> Sigrid de la tabla siguiente pasan a ser obligatorias **también para
> archivar** con `posventa` (§3, «dos lecturas por parte»), salvo
> `CIERRE_HABILITADO`, que archivar no mira.

### Las de Sigrid (F-009 y F-012)

| Variable | Obligatoria | Notas |
|---|---|---|
| `CIERRE_HABILITADO` | no | **Interruptor maestro, apagado por defecto en el código; el despliegue lo publica encendido desde el 2026-09-23** (salvo `-VentanasCerradas`). Sin encenderlo no se escribe nada en el ERP, pase lo que pase. Cubre **las dos escrituras**, el gráfico y el cierre: el gráfico es la primera mitad del cierre y no hay `GRAFICO_HABILITADO`. Es una variable **aparte** de `ARCHIVO_HABILITADO` a propósito: se abren en momentos distintos, y poder archivar no puede implicar poder escribir en el ERP |
| `SIGRID_API_BASE_URL` | sí, para cerrar | La raíz de la pasarela, que es el **único** acceso al SQL Server de Sigrid en todo el ecosistema |
| `SIGRID_API_KEY` | sí, para cerrar | **Secreto**. En Azure va por referencia a Key Vault; en local, solo en el `.env`, que no se versiona. Jamás en un log, en una URL ni en un mensaje de error |
| `SIGRID_BASE_DATOS` | sí, para cerrar | La base de negocio del ERP, que es la única con escritura permitida en la pasarela |
| `SIGRID_TIMEOUT_S` | no | Segundos por llamada. El balanceador de la pasarela corta a los 230 s de todas formas |
| `SIGRID_REINTENTOS` | no | Intentos ante errores transitorios **de una lectura**. La escritura **no se reintenta nunca**, y eso no es configurable |
| `SIGRID_TIP_RECLAMACION` | no | El tipo de concepto de la reclamación de posventa. Es configuración de la instalación, medida contra el ERP |
| `SIGRID_ZONA_HORARIA` | no | El huso con el que se escribe la hora en la fila de auditoría. Sigrid registra **hora local**: escribir UTC dejaría nuestras filas desfasadas del resto |
| `SIGRID_GRATIPIDE_PARTE` | no | **F-012** · la clase de gráfico con la que se adjunta el parte (`auxgra.ide`). Configuración de la instalación, con valor por defecto medido. **Cambiarla aquí a secas no basta**: la pasarela mantiene su propia lista blanca de clases, así que es una decisión de dos dueños |
| `GRAFICO_MAX_BYTES` | no | **F-012** · el tope propio del PDF, comprobado **antes** de llamar a la pasarela. **No debe superar el suyo**: subirlo aquí solo compra un rechazo más tardío, con el fichero ya mandado por el proxy |

Ninguna de estas variables tiene valor en el repositorio: `.env.example` y
`local.settings.json.example` llevan placeholders, y hay un test que lo
comprueba.

`POSTVENTA_PG_TEST_DSN` es aparte: solo la usa la suite de base de datos
(`tests_bbdd/`) contra una base **efímera y local**, y su `conftest.py` aborta
si apunta a un host que no sea local. La suite normal del proyecto no abre ni
una conexión.

## 5 · Qué le hacemos al servidor compartido, en números

Los tres límites que importan, y por qué nos importan:

**Disco.** El servidor tiene 32 GB compartidos, el almacenamiento **solo
crece, nunca decrece**, y el punto de restauración es del **servidor entero**:
no se puede volver atrás nuestra base sin arrastrar las ajenas. El 2026-08-09
el disco llegó al 93,4 % y el servidor quedó en solo-lectura diez minutos por
el build de otro proyecto. Ese precedente es el motivo de que ni los PDF ni el
JSON crudo entren en la base.

**Nuestro volumen esperado es minúsculo.** Una remesa real ronda los 22
partes; una fila de parte son unos cientos de bytes de texto más sus
confianzas. Con el ritmo previsto de Posventa, el crecimiento anual se cuenta
en megabytes, no en gigabytes. Si alguna vez deja de ser así, lo primero que
crecerá es `partes` y el primer sitio donde mirar es esta sección.

**Conexiones.** El servidor es pequeño y las conexiones las comparten cuatro
proyectos. Una Function App que escale a N instancias podría comérselas, así
que el techo de conexiones está bajo por defecto y las sesiones llevan los
tres timeouts de §4. Nada nuestro debería quedar colgado en
`pg_stat_activity`.

**CPU y memoria.** No ejecutamos analítica ni `VACUUM FULL` ni cargas masivas:
son inserciones y actualizaciones de una fila, con índices por número de
incidencia, código de obra y remesa.

## 6 · Qué se rompe si alguien toca algo

| Si alguien... | Nos pasa esto | Aviso |
|---|---|---|
| Cambia parámetros del servidor, autenticación o almacenamiento | Nos afecta igual que a `albaranes` y `partes`; es un cambio de los cuatro, no de uno | Avisar a los cuatro proyectos |
| Llena el disco desde otro proyecto | El servidor pasa a solo-lectura y **dejamos de poder guardar partes**: la validación humana se queda sin cola nueva | Ya pasó el 2026-08-09 |
| Borra o renombra la base `postventa` o su esquema | El servicio no arranca la parte de persistencia | Nadie más debería tocarla: es nuestra |
| Restaura el servidor a un punto anterior | Perdemos las filas posteriores a ese punto, sin manera de aislarlo | Coordinar antes: el PITR es del servidor entero |
| Toca el esquema `public` | A nosotros, nada: no tenemos ni una tabla ahí, y un test contra base efímera lo comprueba | — |
| Quita `UPDATE` o `INSERT` de `ALLOWED_WRITE_PREFIXES` en `sigrid-api` | **Dejamos de poder cerrar incidencias.** El endpoint responde 502 y la incidencia se queda abierta con el parte ya archivado | Es del dueño de `sigrid-api`; avisar antes |
| Saca la base de negocio de `ALLOWED_WRITE_DATABASES` | Lo mismo, y además cortaría cualquier escritura del ecosistema | Es del dueño de `sigrid-api`; avisar antes |
| Apaga `SIGRID_DOCUMENT_WRITE_ENABLED` en `sigrid-api`, o deja vacía `SIGRID_DOCUMENT_WRITE_DATABASE` | **Dejamos de poder adjuntar el parte**, y por tanto de poder cerrar: `/api/adjuntar` responde **503** nombrando la precondición, y `/api/cerrar` responde 409 porque el gráfico no consta. **El ERP queda intacto** | Es del dueño de `sigrid-api`; avisar antes |
| Quita `708` de `SIGRID_DOCUMENT_ALLOWED_CONTIP` o `35` de `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` | Lo mismo, con **409** en vez de 503: la pasarela rechaza la petición y no escribe nada | Es del dueño de `sigrid-api`; avisar antes |
| Baja `SIGRID_DOCUMENT_MAX_BYTES` por debajo del tamaño de un parte | Los partes grandes dejan de poder adjuntarse, con **409** y sin escribir nada. Nuestro `GRAFICO_MAX_BYTES` no protege de esto: es un tope propio y más bajo, no el suyo | Es del dueño de `sigrid-api`; avisar antes |
| Rota la clave de función de `sigrid-api` sin actualizar nuestro Key Vault | 502 en cada cierre, en cada gráfico y en cada dry-run | Coordinar la rotación |
| Cambia el catálogo de estados `conest` del tipo de posventa | Si el código `CER` deja de existir o se duplica, **abortamos sin escribir nada** y lo decimos. No cerramos con un estado supuesto | Es del ERP; se detecta solo |
| Baja el techo de filas de `sql/read` en `sigrid-api` por debajo de 1.000 (**F-013**, desde el corte) | Con `posventa`, una lista de unidades cortada por debajo de lo que pedimos es **503** y no se archiva: cortada, escondería la segunda obra con el mismo número | Es del dueño de `sigrid-api`; avisar antes |

Y al revés, lo que **nosotros** podemos romperles: nada, mientras se cumplan
las reglas de §2. La única superficie compartida real es el **disco** y el
**cupo de conexiones**, y las dos están acotadas a propósito.

## 7 · Datos personales

La base guarda **datos personales de clientes**: DNI y observaciones
manuscritas del parte, además de la promoción y la unidad, que localizan una
vivienda. También el identificador opaco de Entra (`oid`) del empleado que
sube la remesa, confirma un cierre o **aprueba un parte que la validación había
rechazado** (F-026) —desde **F-028**, el de quien **cambia el estado** de un
parte, lo apruebe o lo rechace, en `postventa.historico_estado`—; nunca su
correo ni su nombre.

Ese último `oid` se guarda por una razón distinta de las otras dos y conviene
que se sepa: no es traza de un proceso, es **la firma de una decisión** que
contradice a la validación automática. Quien audite un archivo o un cierre
tiene derecho a saber si lo abrió el veredicto o lo abrió una persona, y
cuándo. Para eso basta un identificador opaco: **para saber que alguien
decidió no hace falta saber quién es**, y por eso ahí no entra ni el correo, ni
el nombre, ni el login del ERP.

Consecuencias para quien administre el servidor:

- El DNI vive en **una sola columna de una sola tabla**, nunca duplicado en
  otra ni en un blob; quien lo necesite hace `JOIN`.
- **Nunca** se escribe en logs, ni completo ni parcial.
- **Nunca** entra en el repositorio: los ejemplos de tests y specs son
  inventados y hay un test que barre el árbol buscando patrones de DNI y NIE.
- Una copia de la base, un volcado o una captura de pantalla del contenido de
  `partes` es un fichero con datos personales y se trata como tal.
- Desde **F-028** hay una **segunda superficie de texto libre**, y conviene
  saberlo: el `motivo` con el que una persona rechaza —o aprueba— un parte, en
  `postventa.historico_estado`. Lo escribe quien revisa, puede llevar dentro el
  nombre de un cliente, y por eso **no sale en ningún log ni en ninguna
  respuesta HTTP**: quien audite lo lee en la base.

El detalle columna a columna está en `specs/F-005-persistencia/design.md` §6.

## 8 · Qué exponemos nosotros

**Rellenada por F-010**, que es la feature que despliega el servicio. Hasta
entonces esta sección decía «hoy, nada»: el servicio solo corría en el puesto
de quien lo desarrollaba.

### Una aplicación de usuario, no una API para terceros

Lo que se expone es una **aplicación web para personas del grupo de Posventa**,
no un servicio que otro proyecto deba llamar. Ningún proyecto del ecosistema
consume esto, y nadie debería empezar a hacerlo sin hablarlo antes: el
contrato de los endpoints es interno y cambia con las features.

| Qué | Nombre del recurso | Quién entra |
|---|---|---|
| Front del piloto | `swa-postventa-ruesma` | Miembros del grupo `posventa-usuarios`, autenticados en Entra |
| Backend | `func-postventa-dev` | Solo a través del front: es el **backend enlazado** de la Static Web App |
| Tarjeta de acceso | `front-portal` (otro repositorio) | La misma restricción de grupo |

Los nombres de host **no se escriben aquí**, como ninguno del resto del
documento.

### Los endpoints, y qué hace cada uno

| Endpoint | Efecto |
|---|---|
| `GET /api/health` | Dice si el servicio vive. Sin datos y sin autenticación: lo usan el despliegue y el propio front |
| `POST /api/split` | Trocea una remesa. Sin efecto externo |
| `POST /api/extraer` | Llama al proveedor de IA. Gasta cuota |
| `POST /api/firma` | Llama al proveedor de IA. Gasta cuota |
| `POST /api/validar` | Solo reglas. Sin IA y sin efecto externo |
| `POST /api/remesa` | **Escribe** en `postventa.remesas` (esquema propio). Devuelve el `remesa_id` que hay que reenviar después |
| `POST /api/parte` | **Escribe** en `postventa.partes` y `postventa.validaciones`. Recalcula el veredicto con las reglas del dominio: nunca acepta el que venga en el cuerpo |
| `POST /api/estado` | **Escribe** en `postventa.historico_estado` (esquema propio): registra que **una persona** mueve un parte a `aprobado` o a `rechazado`, con su `oid`, el motivo —obligatorio al rechazar— y una huella del veredicto sobre el que decide. **No toca ningún sistema ajeno, y en Sigrid no consta**. Guarda además el parte y recalcula el veredicto: nunca acepta el que venga en el cuerpo. Es lo que decide si un parte entra después en el circuito de archivo y cierre —solo entra el que está `aprobado`—, y las tres puertas del backend lo comprueban una a una. Responde **409** si el parte ya está `cerrado`, que es un estado terminal porque lo escribió el ERP (F-028) |
| `GET /api/cola` | **Lee** la cola de validación humana. Único endpoint que devuelve **dato personal acumulado** sin que el llamante aporte el PDF: tope duro de 500 entradas por llamada |
| `POST /api/archivar` | **Escribe** en la biblioteca de dev de SharePoint y deja traza en la base. Exige que el parte **ya conste guardado**: si no, responde 409 sin subir nada |
| `POST /api/adjuntar` | **ESCRIBE EN EL ERP DE PRODUCCIÓN**: adjunta el PDF del parte a la reclamación como gráfico, **tres filas en dos bases**, por el endpoint de dominio de la pasarela. Va **antes** del cierre. `multipart/form-data`, con el fichero. **Por omisión es un dry-run** que solo lee; con `commit` exige además confirmación explícita o auto-cierre guardado. Desde un puesto de trabajo responde 503 sin tocar el ERP. **Su reintento es seguro**: el endpoint de la pasarela es idempotente por contenido |
| `POST /api/cerrar` | **ESCRIBE EN EL ERP DE PRODUCCIÓN**: mueve `con.est` al estado de cierre y añade una fila a `dbo.log`, en un solo batch transaccional con tope de dos filas. **Exige que el parte conste adjuntado** (F-012): con `commit` y sin gráfico responde 409 sin tocar el ERP. **Por omisión es un dry-run** que solo lee; con `commit` exige además confirmación explícita o auto-cierre guardado. Desde un puesto de trabajo responde 503 sin tocar el ERP |

> **Enmienda del 2026-09-24 (F-013), para el día del corte.** La fila de
> `POST /api/archivar` dice, literal, que «**Escribe** en la biblioteca de dev
> de SharePoint». Desde el corte escribe en la **biblioteca de Posventa**
> —decisión del humano del 2026-09-18—, puede **crear carpetas** en ella (una
> línea en `avisos` por cada una), **lee Sigrid dos veces** por parte y tiene
> un 409 más, el del destino no resuelto (con `motivo` y `candidatas`), y un
> 503 más, el de Sigrid (§3, «Con F-013»). Lo que no cambia: el contrato del
> cuerpo, el nombre del fichero y que un parte que ya consta archivado no se
> vuelve a subir.

Los tres endpoints de F-019 **no dependen de `ARCHIVO_HABILITADO`**: escriben
en el esquema propio del proyecto, no en un sistema ajeno. Con la ventana de
escritura cerrada —que es como se despliega— se sube la remesa, se trocea, se
extrae, se valida, **se guarda** y se lee la cola; solo `POST /api/archivar`
responde 503.

**`POST /api/estado` tampoco mira ninguna de las dos ventanas**, y es
deliberado: decidir es registrar una decisión en nuestra base, no escribir
fuera. Con `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` apagados se puede mover
de estado un parte y no pasa nada más; lo que el estado `aprobado` abre son las
puertas de `POST /api/archivar`, `POST /api/adjuntar` y `POST /api/cerrar`, que
**siguen teniendo las suyas intactas**. Dicho al revés, para que un parte acabe
dentro del ERP hacen falta las dos cosas: que esté `aprobado` y que la ventana
de escritura esté abierta.

Y admite un caso que antes no se podía ni enunciar: un parte que la máquina dio
por **apto** y que una persona **rechaza** deja de archivarse, de adjuntarse y
de cerrarse. La ruta de aprobación contestaba 409 a cualquier parte apto —«no
hay nada que aprobar»—, así que la única forma de pararlo era no mirar.

Los doce quedan en nivel **anónimo**, y **es deliberado**: con un backend
enlazado, la Static Web App autentica al usuario y reenvía una cabecera de
identidad, no una credencial que la Function pueda exigir. Quien lo cambie
rompe el front. Y ese nivel es **irrelevante desde internet**: la plataforma
activa Easy Auth con el proveedor `azureStaticWebApps` en el backend enlazado,
así que solo se acepta lo que entra por el proxy, y el proxy exige sesión y
pertenencia al grupo. El razonamiento completo y las capas de protección que
sí sostienen el acceso están en la cabecera de
`services/postventa-api/function_app.py` y en `docs/DESPLIEGUE.md` §4 y §5 bis.

### Lo que deja de escribirse desde F-028 (2026-09-16)

Es lo que necesita saber quien audite, y el motivo de que esta sección cambie:

| Qué | Hasta el 2026-09-16 | Desde F-028 |
|---|---|---|
| El endpoint de la decisión humana | La ruta de aprobación, `/api/aprobar` | **Retirada**: ya no existe ninguna ruta con ese nombre, y llamarla da 404. La sustituye `POST /api/estado` |
| Dónde queda la decisión | Una fila por parte en `postventa.aprobaciones`, **sustituida** en cada decisión nueva | Una fila **más** por decisión en `postventa.historico_estado`, que no se pisa nunca |
| `postventa.aprobaciones` | Se escribía en cada aprobación y en cada revocación | **Congelada**: sigue declarada, sigue creándose y sigue consultable, pero **no se le escribe ni una fila más**. Sus filas vigentes se sembraron una vez en el histórico |
| Qué se puede contradecir de la máquina | Solo **aprobar** un parte no apto | **Aprobar** y **rechazar**, también un parte que la máquina había dado por apto |
| La marca de aprobación revocada | Una segunda escritura marcaba la fila al cambiar el veredicto | **No se escribe nada**: la caducidad se resuelve al **derivar** el estado, comparando la huella guardada con la del veredicto de ahora |

Para el ecosistema, **nada de esto cruza ninguna frontera**: no se consume
ningún recurso nuevo, no hay ninguna variable de entorno nueva, no se pide nada
al servidor compartido fuera del esquema propio y **en Sigrid no queda
constancia de la decisión**, exactamente igual que con F-026. Quien necesite
distinguir un cierre automático de uno que una persona autorizó a pesar del
veredicto cruza `postventa.historico_estado` con `postventa.cierres` por
`hash_parte`; para lo decidido **antes** del 2026-09-16,
`postventa.aprobaciones` sigue ahí y sigue siendo la fuente.

### Qué NO está desplegado, y hay que decirlo antes de enseñarlo

| Qué falta | Feature | Consecuencia visible |
|---|---|---|
| Que Posventa lo use de verdad | — | El circuito completo está probado, pero **solo lo ha recorrido el responsable del proyecto**. Posventa todavía no ha cerrado ninguna incidencia con esto |
| Rehidratar la sesión al recargar el navegador | **feature nueva**, decidida el 2026-08-26 (D4 de F-019) | Lo guardado **queda guardado** y la cola sobrevive, pero si el usuario recarga la página **pierde el trabajo en curso**: volver a pintarlo exige leer una remesa entera con sus partes, y eso es un método de lectura nuevo en el puerto de persistencia |
| Mudar el archivo a la biblioteca real de Posventa | F-013 | Los partes aterrizan en la biblioteca de **dev** del sitio de IT |
| Recortar los permisos de Graph | F-018 | La identidad de aplicación conserva permisos amplios (ver §3) |

> **Precisión del 2026-09-24 (F-013).** La fila de la mudanza sigue siendo
> cierta: F-013 está implementada en su rama y **no desplegada**. Deja de
> serlo el día del corte (`docs/DESPLIEGUE.md` §9), que decide y ejecuta el
> humano; desde entonces, lo nuevo se archiva en la biblioteca de Posventa y
> los 133 partes de IT se quedan donde están (§3).

### Lo que YA se ha ejecutado contra el ERP, y con qué evidencia

> **Corrige lo que este documento dijo hasta el 2026-09-15.** Sus dos primeras
> filas decían que el cierre y el gráfico estaban implementados pero que
> «todavía no se ha ejecutado ni un cierre real», y que la verificación se haría
> «sobre reclamaciones de la obra de prueba 404». **Las dos cosas dejaron de ser
> verdad el 2026-09-11**: el responsable decidió el 2026-09-10 probar sobre una
> **obra en uso**, la `0626`, con autorización expresa e incidencia por
> incidencia.

**Dos cierres reales**, los dos auditados por lectura y no de palabra:

| Cuándo | Incidencia | Qué se probó | Fila de `dbo.log` |
|---|---|---|---|
| 2026-09-11 | `RS26.09/0150` | F-012 y F-009: parte archivado, **adjunto** a la reclamación y reclamación **cerrada** | `ide` 8457839, `10:28:12` |
| 2026-09-15 | `RS26.09/0149` | F-026: un parte **no apto** aprobado a mano, y de ahí al archivado y al cierre | `ide` 8467000, `14:30:05` |

Las dos filas pasan las **once comprobaciones campo a campo** del §7.3 del
diseño de F-009, y en las dos el par `fec`/`hor` está en **hora local**, que es
como escribe el ERP —se comprobó a propósito: escribir en UTC habría dejado
nuestras filas una o dos horas por detrás de los 6.843 cierres manuales que las
rodean, sin que nadie lo notara—.

**Las ventanas de escritura siguen siendo la puerta.** `ARCHIVO_HABILITADO` y
`CIERRE_HABILITADO` se despliegan **apagadas**, se abren para la prueba y se
vuelven a cerrar: al terminar la del 2026-09-15 quedaron las dos en `false`. Con
ellas cerradas, las rutas responden `503` y **Sigrid no se toca** —ni para
leer—, que es lo que había que decir antes del primer cierre y lo que sigue
siendo verdad después.

### Lo que este proyecto añade al ecosistema

- Un **grupo de recursos propio** y un **Key Vault propio**, como `partes`.
  Nada se mete en los de otros proyectos.
- Un **registro de aplicación nuevo** para el inicio de sesión, separado del
  de Graph: la credencial de mayor privilegio y la aplicación con la que se
  loguean los usuarios no comparten identidad.
- Una **tarjeta en el portal**, que es el único punto donde este proyecto
  cruza la frontera de otro repositorio. El bloque y el procedimiento están en
  `docs/DESPLIEGUE.md` §6.

## 9 · Dónde está cada cosa

| Qué | Dónde |
|---|---|
| El DDL, en `.sql` numerados | `services/postventa-api/infrastructure/persistencia/sql/` |
| El validador que lo revisa antes de aplicarlo | `services/postventa-api/infrastructure/persistencia/ddl.py` |
| Crear la base y el rol, una vez | `infra/crear_base_postventa.ps1` |
| Suite contra base efímera en Docker | `infra/pruebas_bbdd_efimera.ps1` |
| Diseño completo y decisiones de la persistencia | `specs/F-005-persistencia/` |
| El adaptador de SharePoint y su fábrica | `services/postventa-api/infrastructure/sharepoint/` |
| Comprobar el destino de dev, solo lecturas | `infra/verificar_destino_sharepoint.ps1` |
| Comprobar el archivo end-to-end en dev | `infra/verificar_archivo_dev.ps1` |
| Diseño completo y decisiones del archivo | `specs/F-006-sharepoint/` |
| Diseño completo y decisiones de la mudanza a Posventa | `specs/F-013-archivo-posventa/` |
| La regla de casado y de creación de carpetas, pura | `services/postventa-api/domain/models/destino_posventa.py` |
| El resolutor del destino | `services/postventa-api/application/pipelines/destino_archivo.py` |
| Las dos lecturas de Sigrid al archivar | `services/postventa-api/infrastructure/sigrid/ubicacion.py` y `consultas_ubicacion.py` |
| Medir en seco el destino de Posventa y las unidades de Sigrid, solo lecturas | `infra/23_destino_posventa.ps1` y `infra/24_ubicacion_sigrid.ps1` |
| El runbook del corte de F-013 | `docs/DESPLIEGUE.md` §9 |
| Nombres de recurso, regiones y tags del despliegue | `infra/00_vars_postventa.ps1` |
| Runbook del despliegue y tarjeta del portal | `docs/DESPLIEGUE.md` |
| Comprobar el despliegue, solo lecturas | `infra/verificar_despliegue.ps1` |
| Diseño completo y decisiones del despliegue | `specs/F-010-despliegue/` |
| Documento gemelo del ecosistema | `azure-apps/postventa_incidencias.md` |
