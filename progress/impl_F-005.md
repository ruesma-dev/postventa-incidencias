<!-- progress/impl_F-005.md -->
# F-005 · Persistencia en el PostgreSQL compartido — informe de implementación

> Rama `feature/F-005-persistencia`. Rigor **`critico`**. Contrato:
> `specs/F-005-persistencia/` (los tres ficheros) y `progress/explore_F-005.md`.
>
> **Ni un dato real en este informe.** Los ejemplos que aparecen son
> inventados y van marcados como tales. Los partes llevan DNI y observaciones
> manuscritas de clientes: eso vive en la base de datos, nunca en el
> repositorio.

## T1 · Precondición dura verificada: F-004 está mergeada en `dev`

Ejecutado en la rama `feature/F-005-persistencia`:

```
$ git log dev --oneline --grep F-004 | head -5
e3f5fcd Traer F-004 a la rama de F-005
62e91ed Merge F-004: validacion del parte y clasificacion de la firma
bb3ae58 F-004 CERRADA: revision APROBADA y cierre documental
ab9b677 F-004 T14: resultado real de la firma y cierre de D1
89e0a30 Backlog: F-005 y F-006 con spec lista, y dos deudas anotadas

$ git show dev:services/postventa-api/domain/models/validacion.py > /dev/null
validacion.py EXISTE en dev

$ git rev-list --count HEAD..dev
0
```

**La precondición está cumplida**: el merge de F-004 consta en `dev`
(`62e91ed`), `domain/models/validacion.py` existe ahí, y esta rama **no está
por detrás de `dev`** (0 commits pendientes de traer), así que no hace falta
rebasar. `ResultadoValidacion`, `Veredicto`, `Destino`, `CodigoMotivo` y
`ClasificacionFirma` están disponibles en el árbol de trabajo.

Portero antes de tocar nada: `bash harness/init.sh` → `ENTORNO LISTO`,
exit code 0.

## T2 · Decisiones D1–D6, resueltas por el humano el 2026-08-19

Las seis decisiones abiertas de `design.md` §10 **están resueltas** y
**ninguna bloquea**. Se copian aquí, con su fecha, porque son el contrato bajo
el que se ha implementado esta feature.

**D1 · Base propia `postventa` o esquema dentro de una base existente.**
RESUELTA el **2026-08-19**, CONFIRMANDO el diseño: **base propia `postventa`**,
con esquema nominado `postventa` dentro y `search_path` **sin `public`**.
Motivo aceptado: el ecosistema aísla por base, y meter un esquema en
`albaranes` ataría el ciclo de vida de dos proyectos. **La base la crea el
humano a mano; la aplicación nunca** (R7). Sin cambios en el diseño.

**D2 · ¿Se persiste el DNI del cliente?** RESUELTA el **2026-08-19**: **SÍ se
persiste**, en `partes.dni_cliente`. Decisión expresa del humano. Descartado el
booleano `dni_presente`. **Consecuencia implementada**: hay dato personal
directo en una base compartida, así que las salvaguardas de `design.md` §6 son
contrato verificable y no una intención — R37–R40, con **T19** (el DNI y las
observaciones nunca en el log) y **T19 bis** (ningún DNI en el repositorio).

**D3 · Docker o PostgreSQL local para la base efímera.** RESUELTA el
**2026-08-19**, CONFIRMANDO el diseño: **Docker** (`postgres:16-alpine`,
contenedor `--rm`). Dos datos verificados ese día en el puesto del humano y que
condicionan el script (**T21**): **Docker 29.5.3 está instalado** pero el
**demonio puede estar parado** (Docker Desktop cerrado), y **no hay `psql` en
el `PATH`**. El script comprueba lo primero que el demonio responde y aborta
con un mensaje accionable —«arranca Docker Desktop»— en vez de un error opaco
de conexión (R35), y no depende de `psql` en ningún punto (R36).

**D4 · ¿`numero_incidencia` único?** RESUELTA el **2026-08-19**, CONFIRMANDO el
diseño: **indexado pero NO único**. La deduplicación la hace el hash del parte.
Motivos aceptados: una misma incidencia puede tener más de un parte (más de una
visita), y un índice único rompería el día que F-014 reagrupe un parte de dos
hojas.

**D5 · ¿Se declara el DDL como ruta sensible del arnés?** RESUELTA el
**2026-08-19**: **NO se declara ahora**. F-005 **no** crea
`harness/rutas_sensibles.json` y el checkpoint C4 ter sigue siendo **N/A**.
Motivo del humano: hacerlo aquí cambiaría el arnés para todas las features y
obligaría a portarlo a `arnes-base` en el mismo trabajo. **No es un olvido**:
`services/postventa-api/infrastructure/persistencia/sql/**` queda como
**candidato reconocido a ruta sensible** y **la decisión vive en F-017**.

**D6 · ¿Se guarda `usuario_oid` ya en F-005?** RESUELTA el **2026-08-19**,
CONFIRMANDO el diseño: **la columna `usuario_oid` se crea ya y queda `NULL`**
hasta F-007/F-010, que son las que conocen al usuario autenticado. Cuesta cero
ahora y ahorra un `ALTER TABLE` contra una base compartida después.

Ninguna de las seis queda en `PENDIENTE`.

## Fase RED · las trazas reales, antes de que existiera el código

Rigor `critico`: para cada requisito central se escribió primero el test, se
ejecutó, y **aquí está pegada la salida real del fallo**. No es un resumen del
error: es lo que imprimió la consola.

### RED 1 · T5 — los puertos de persistencia no existían (R30, R31)

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_arquitectura.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f005_arquitectura.py _______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f005_arquitectura.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f005_arquitectura.py:26: in <module>
    from domain.ports.persistencia import (
E   ModuleNotFoundError: No module named 'domain.ports.persistencia'
=========================== short test summary info ===========================
ERROR tests/test_f005_arquitectura.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.27s
```

**VERDE tras T7**, con los puertos ya escritos:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_arquitectura.py -q
....                                                                     [100%]
4 passed in 0.58s
```

### RED 2 · T8 — la guarda del DDL no existía (R5, R6, R12, R3)

Es el requisito central de la feature: la prohibición dura de `CLAUDE.md`
—«ni DDL fuera del esquema propio, ni nada de ámbito de servidor»— convertida
en código que se ejecuta **antes de abrir ninguna conexión**.

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_ddl_seguro.py -q
=================================== ERRORS ====================================
_______________ ERROR collecting tests/test_f005_ddl_seguro.py ________________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f005_ddl_seguro.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f005_ddl_seguro.py:25: in <module>
    from infrastructure.persistencia.ddl import sentencias, validar
E   ModuleNotFoundError: No module named 'infrastructure.persistencia'
=========================== short test summary info ===========================
ERROR tests/test_f005_ddl_seguro.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.46s
```

**VERDE tras T9**, con `infrastructure/persistencia/ddl.py` escrito:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_ddl_orden.py tests/test_f005_ddl_seguro.py -q
...................................................                      [100%]
51 passed in 0.23s
```

## Desviaciones respecto a la spec, justificadas

Tres, y ninguna toca el contrato de la feature.

**1 · T13 se ha hecho antes que T12.** `tasks.md` las lista en el orden T12
(`arranque.py` y su test) → T13 (`tests/utiles_pg.py`, el doble de conexión),
pero la propia T13 dice que **el doble «se usa desde T12»** y la verificación
de T12 exige el doble. Es una inversión de dependencia en la lista, no un
cambio de alcance: se ha implementado T13 primero para que T12 pudiera
verificarse, con un commit por tarea igualmente.

**2 · Un campo `pg_*` de más: `pg_idle_in_transaction_timeout_s`.**
`design.md` §5 declara diez campos, y **R9 exige fijar de sesión
`idle_in_transaction_session_timeout` «con los valores que declara la
configuración»** — pero §5 no le dio campo. Los diez de §5 están todos, con sus
alias y sus valores por defecto exactos; este es el undécimo, alias
`PG_IDLE_IN_TRANSACTION_TIMEOUT_S`, por defecto **60 s**, holgadamente por
encima del `statement_timeout` de 30 s para que nunca corte una transacción que
solo está trabajando. Se ha añadido porque **el requisito EARS manda sobre el
recuento de una tabla del diseño**, y porque una sesión colgada se queda en el
servidor **de otros** (riesgo 3 de `design.md` §9).

**3 · Una guarda de más en `conexion.py`: ningún timeout puede valer 0.** En
PostgreSQL `0` significa **sin límite**. No lo pide ningún requisito de forma
explícita, pero un `PG_STATEMENT_TIMEOUT_S=0` desactivaría en silencio la única
protección que R9 pone sobre un servidor compartido, y hacerlo desde una
variable de entorno es demasiado fácil. Levanta `ConfiguracionPgIncompleta`
nombrando la variable.

### RED 3 · T19 — el vigilante del log muerde de verdad (R29, R37)

Aquí el entregable **es el propio test**: no hay código nuevo cuyo fallo previo
enseñar, porque lo que se comprueba es una **ausencia** (que el DNI y las
observaciones no salgan por ningún lado). `CHECKPOINTS.md` C4 bis contempla ese
caso: la fase RED se demuestra **rompiendo deliberadamente lo que el test
vigila** y pegando la traza.

Se añadió a mano, de forma temporal, el atajo que uno escribe depurando —volcar
los parámetros de la sentencia en el log de `guardar_parte`— y el test cayó:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_logs_sin_datos_personales.py -q
    def _sin_datos_personales(texto: str) -> None:
        """Falla nombrando el valor que se ha filtrado."""
        for valor in PROHIBIDO_EN_EL_LOG:
>           assert valor not in texto, f"el log ha publicado un dato del parte: {valor!r}"
E           AssertionError: el log ha publicado un dato del parte: '00000000T'
E           assert '00000000T' not in "INFO     in...5f', '[]')\n"
E
E             '00000000T' is contained here:
E               ia', 90, '00000000T', 90, 'texto manuscrito inventado para este test', 90, '1', 98, 'gemini', ...
E             ?           +++++++++

tests\test_f005_logs_sin_datos_personales.py:87: AssertionError
------------------------------ Captured log call ------------------------------
INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:108 F-005 parte guardado: hash=hash-inventado-0001 resultado=creado parametros=(... '00000000T', 90, 'texto manuscrito inventado para este test', ...)
=========================== short test summary info ===========================
FAILED tests/test_f005_logs_sin_datos_personales.py::test_f005_r37_guardar_un_parte_no_publica_el_dni_ni_las_observaciones
1 failed, 4 passed in 0.85s
```

La línea que se añadió se **revirtió con `git checkout --`** en el acto, y
`git status` sobre ese fichero quedó limpio. El DNI que aparece en la traza es
`00000000T`: un número **no emitido**, marcador de uso convencional, que no
identifica a nadie.

Verde tras revertir:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_logs_sin_datos_personales.py -q
.....                                                                    [100%]
5 passed in 0.73s
```

### RED 4 · T22 — el barrido de `docs/INTEGRACION.md` (T22)

El documento que este proyecto va a copiar a `azure-apps/` es, de todos los
ficheros de la feature, el que más papeletas tiene para acabar llevando un
host o una contraseña «para que se entienda mejor»: lo va a leer gente de
otros proyectos y la tentación de concretar es real. Por eso el barrido se
escribió **antes** que el documento, y falló porque el documento no existía:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_integracion_sin_secretos.py -q --tb=short
E   FileNotFoundError: [Errno 2] No such file or directory: 'C:\Users\pgris\PycharmProjects\postventa-incidencias\docs\INTEGRACION.md'
________________ test_f005_t22_el_documento_no_queda_huerfano _________________
tests\test_f005_integracion_sin_secretos.py:155: in test_f005_t22_el_documento_no_queda_huerfano
    assert "INTEGRACION.md" in texto
E   AssertionError: assert 'INTEGRACION.md' in '<!-- docs/ARCHITECTURE.md -->\n# Arquitectura · postventa-incidencias\n...'
=========================== short test summary info ===========================
FAILED tests/test_f005_integracion_sin_secretos.py::test_f005_t22_el_documento_de_integracion_existe
FAILED tests/test_f005_integracion_sin_secretos.py::test_f005_t22_el_documento_dice_que_consumimos
FAILED tests/test_f005_integracion_sin_secretos.py::test_f005_t22_el_documento_lista_los_nombres_de_las_variables
FAILED tests/test_f005_integracion_sin_secretos.py::test_f005_t22_ningun_secreto_ni_identificador_en_el_documento
FAILED tests/test_f005_integracion_sin_secretos.py::test_f005_t22_el_documento_no_queda_huerfano
5 failed, 17 passed in 0.24s
```

Los 17 que ya pasaban en rojo son los **controles**: los nueve negativos —un
valor inventado por familia de patrón, para demostrar que el barrido muerde— y
los ocho positivos de texto legítimo, para demostrar que no muerde a
cualquiera. Un guardián que grita con todo se acaba desactivando, y un
guardián que nunca se ha visto gritar no protege nada.

Verde con el documento escrito:

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_f005_integracion_sin_secretos.py -q
......................                                                   [100%]
22 passed in 0.04s
```

Las seis familias que el documento no puede contener: **FQDN** de Azure
(`*.postgres.database.azure.com` y compañía; el **nombre** del recurso sí, que
es lo que pide `design.md` §11), **GUID** (suscripción, tenant, aplicación,
`oid`), **`VARIABLE=valor`** para cualquier `PG_*`, `POSTGRES_*` o
`POSTVENTA_*`, **`password=`** y sus primos, **URI con credencial
incrustada**, y cualquier **IPv4** que no sea el bucle local de la base
efímera. El patrón de credencial exige `=` a propósito: en prosa española «la
contraseña: ...» lleva dos puntos y no es un secreto, y hay un control
positivo que lo fija.

## T21 · el script de la base efímera, ejecutado de verdad

`tasks.md` T21 promete que, con el demonio de Docker parado, el script sale
con un mensaje accionable y **código distinto de cero** sin dejar nada vivo.
Ejecutado tal cual el 2026-08-19, con Docker Desktop cerrado:

```
> powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
==> Comprobando Docker

Docker esta instalado pero el demonio no responde.

  ARRANCA DOCKER DESKTOP y vuelve a lanzar este script.

(El 2026-08-19 estaba instalado -29.5.3- con el demonio parado: es el caso normal en este puesto.)
EXITCODE=3
```

El script aborta **en el primer paso**, antes de intentar levantar nada, que
es justo lo que pide la decisión D3: distinguir «Docker no instalado» de
«demonio parado» y decir qué hacer, en vez de morir tres pasos después con un
error opaco de conexión a la base. No queda ningún contenedor porque no llega
a crearse ninguno: el propio `docker ps -a` de comprobación tampoco puede
hablar con el demonio.

Ese código de salida 3 es **la mitad de la verificación de T21**. La otra
mitad —el camino feliz, con Docker arrancado— es **M1 (T24)** y la ejecuta el
humano.

## T23 · la campaña de mutación, en dos vueltas

El informe generado vive en `progress/mutacion_F-005.md`. Aquí queda el
resumen y —esto es lo importante— **la copia durable del análisis de los
timeouts**: el generador reescribe la sección «Timeouts» como lista pelada en
cada campaña y no conserva lo escrito a mano, a diferencia de lo que hace con
la de supervivientes. Si alguien repite la campaña, el análisis se recupera de
aquí.

Comando, siempre el mismo:

```
python -m harness.mutacion --feature F-005
```

Alcance: 2.206 líneas cambiadas en 14 ficheros, campaña **completa** (sin
muestreo), 104 mutantes generados y 104 evaluados en las dos vueltas.

| Campaña | Mutantes | Muertos | Supervivientes | Timeouts | Tiempo |
|---|---|---|---|---|---|
| 15:33 (primera) | 104 | 71 | **31** | 2 | 250,2 s |
| 16:13 (cierre de las 27 tareas) | 104 | **101** | **0** | 3 | 395,0 s |
| 23:09 (tras los dos arreglos de review) | 106 | **103** | **0** | 3 | 330,4 s |

La tercera campaña es la que exige el nivel `critico` después de tocar código
de producción: los dos mutantes nuevos son los del recorte de avisos, y los
tres timeouts son **exactamente los tres de siempre**, misma línea y mismo
operador. Detalle en «Los dos arreglos de la review», al final.

### Qué se mató, y cómo

Los 31 supervivientes de la primera vuelta se concentraban donde era
previsible: **19 de los 31 en el troceador de `ddl.py`**, la pieza con más
lógica de carácter a carácter de toda la feature, y 7 más en los modelos de
`domain/models/persistencia.py`. Ninguno era equivalente: los 31 se mataron
con test.

Primera tanda (`0b13e3b`), 111 tests de F-005 en verde:

- **El troceado del DDL en sus bordes**, en un fichero nuevo
  (`services/postventa-api/tests/test_f005_ddl_troceado.py`, 13 tests):
  comentarios de bloque pegados, vacíos y sin cerrar; literales vacíos;
  comillas dobladas; cuerpos con delimitador de dólar sin cerrar. Ahí vivían
  los 19.
- **La clave del bloqueo consultivo**, escrita a mano en el test y no
  importada de la constante que vigila: importarla hacía el test tautológico.
- **El recorte a 80 caracteres** del mensaje de `DdlInseguro`, con un caso a
  cada lado del borde.
- **La inmutabilidad de los cinco registros**, parametrizada.
- **`EPOCA_SIN_DECIDIR`**, fijada al 1 de enero de 1970.

Esa tanda dejó la campaña en 3 supervivientes. Segunda tanda (`84736ea`), con
cada test verificado aplicando la mutación al fichero real y viéndolo fallar:

- **`ddl.py:177`** (`posicion + 1 < fin`): invisible desde `sentencias`
  —lo compensa el propio bucle, comprobado—, pero rompe el contrato
  documentado de `_fin_de_literal`, que es donde se comprueba ahora.
- **`mapeo.py:136`** (`ensure_ascii`): el test que había comparaba la lista ya
  deserializada, y `json.loads` devuelve lo mismo se escapen los acentos o no.
  Ahora se mira **el texto que se guarda**.
- **`sentencias.py:142`** (el cast a `jsonb`): comprobar que el marcador con
  cast aparece en el SQL seguía pasando con el cast puesto en todas las
  columnas menos la que lo necesita. Ahora se **emparejan columnas y
  marcadores**.

Resultado final: **0 supervivientes**.

### Los tres timeouts (copia durable del análisis)

Los tres caen en el bucle del troceador de `ddl.sentencias` y los tres son el
**mismo defecto**: la mutación destruye el avance del escáner y el bucle deja
de terminar. No son mutantes que se escapen sin que nadie se entere —que es lo
que preocupa de un superviviente—, sino mutantes que **cuelgan la suite**: con
cualquiera de los tres aplicado, `bash harness/init.sh` no vuelve nunca, y eso
es tan visible como un test en rojo.

No se pueden «matar» con un test: un test no puede afirmar nada sobre una
función que no retorna. Se comprueban ejecutándolos con un reloj por fuera.

Comprobado el 2026-08-19 cargando `ddl.py` con la mutación aplicada en un
espacio de nombres aparte —sin tocar el repositorio— y ejecutándolo bajo
`timeout 15`. Los tres devuelven código de salida **124**, que es como
`timeout` dice «lo he matado yo, seguía corriendo»:

| Mutante | Por qué no termina | Caso que lo cuelga | Salida |
|---|---|---|---|
| `ddl.py:131` `salto == -1` → `salto == -2` | `str.find` devuelve `-1` cuando no encuentra, nunca `-2`. Con un `--` final sin salto de línea, `posicion` pasa a valer `-1` en vez de `fin`, y el bucle vuelve a entrar por el final del texto una y otra vez. | `CREATE SCHEMA IF NOT EXISTS postventa; -- cola` | exit 124 |
| `ddl.py:158` `posicion += 1` → `posicion -= 1` | Es el avance tras consumir un `;`. Retrocediendo, el escáner vuelve al carácter anterior al `;`, lo vuelve a leer, vuelve al `;`, y así siempre. | `CREATE SCHEMA postventa;CREATE TABLE postventa.x ()` | exit 124 |
| `ddl.py:162` `posicion += 1` → `posicion -= 1` | Es el avance del carácter suelto, el caso general. Retrocediendo, `posicion` no llega jamás a `fin`. | el mismo | exit 124 |

**La lección de la vuelta:** los dos primeros ya estaban en la campaña de las
15:33; el tercero **apareció** en la final, después de añadir los tests del
troceado. Que aparezca un timeout **más** al añadir tests no es una regresión:
antes esa línea no la recorría ningún test y la mutación moría sin colgarse
porque nadie entraba por ahí. Ahora sí hay tests que la ejercitan. Un mutante
que pasa de «nadie lo mira» a «cuelga el reloj» es una mejora de cobertura
real, no un empeoramiento del número.

## T27 · `bash harness/init.sh` en verde

Ejecutado tal cual, sin pipes ni decoración, el 2026-08-19 al cierre de la
feature. Salida real, íntegra:

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    17 features, 13 abiertas, en curso: ['F-005'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 53 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
................                                                         [100%]
16 passed in 0.47s
[OK] pytest en verde (con medición de cobertura)
    1 servicio(s): api (python)
[OK] harness/servicios.json válido
........................................................................ [ 10%]
........................................................................ [ 20%]
........................................................................ [ 31%]
........................................................................ [ 41%]
........................................................................ [ 52%]
........................................................................ [ 62%]
........................................................................ [ 73%]
........................................................................ [ 83%]
........................................................................ [ 94%]
..............................ssssssssss                                 [100%]
678 passed, 10 skipped in 20.22s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 97.0% de 591 líneas cambiadas cubiertas (573/591, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-005-persistencia
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

Exit code 0. La puerta de cobertura en `[OK]` con **97,0 %** frente al umbral
del 80 % que fija `harness/rigor.json` para el nivel `critico`.

## Verificaciones MANUALES pendientes (las hace el humano)

Tres, y las tres necesitan algo que un agente no puede o no debe tocar:

- **T24 · M1 — la suite contra base efímera.** Necesita Docker Desktop
  **abierto**; el 2026-08-19 estaba instalado (29.5.3) con el demonio parado.
  Es la otra mitad de la verificación de T21: aquí solo está comprobado el
  camino de error (exit 3, más arriba).
- **T25 · M2 — la primera aplicación del DDL contra la base real de dev.** Es
  escritura en el PostgreSQL compartido: la ejecuta el humano, nunca un
  agente, y solo después de M1 en verde. El dry-run va primero y no abre
  conexión.
- **T26 · M3 — copiar `docs/INTEGRACION.md` a
  `azure-apps/postventa_incidencias.md`** y dar de alta su fila en el
  `README.md` de ese repositorio. Es **otro repositorio git**: lo commitea el
  humano.

Los `tests_bbdd/` que dependen de la base efímera están **apagados por
defecto** (los 10 `skipped` de la salida de arriba): sin su variable de
entorno no se ejecutan, y por eso `init.sh` puede cerrar en verde sin Docker.

## Evidencias

Números reales, medidos el 2026-08-19. Nivel de rigor de F-005: **`critico`**.

**Actualizada tras los dos arreglos de la review**: la columna «al cierre de
las 27 tareas» se conserva para que se vea qué movió cada arreglo.

| Evidencia | Al cierre de las tareas | **Tras los arreglos de review** | De dónde sale |
|---|---|---|---|
| Tests ejecutados (servicio `api`) | 678 passed, 10 skipped | **682 passed, 10 skipped** | salida de la suite en `init.sh` |
| Tests ejecutados (arnés) | 16 passed | **16 passed** | misma salida |
| Los 10 `skipped` | `tests_bbdd/`, apagados sin su variable de entorno | íd. | son M1 (T24), del humano |
| Cobertura de las líneas cambiadas | 97,0 % (573/591) | **97,0 %** (578/596), umbral 80 % | línea `PUERTA COBERTURA` de `init.sh` |
| Mutantes generados / evaluados | 104 / 104 | **106 / 106**, campaña completa sin muestreo | `progress/mutacion_F-005.md` |
| Mutantes muertos | 101 | **103** | íd. |
| **Supervivientes** | 0 | **0** | íd. |
| Timeouts | 3 | **3**, los mismos tres, analizados arriba (exit 124 cada uno) | íd. |
| Tiempo de la suite del servicio | 20,22 s | **19,36 s** | salida de la suite en `init.sh` |
| Tiempo de la campaña de mutación | 395,0 s | **330,4 s** | `progress/mutacion_F-005.md` |

Los cuatro tests nuevos y los cinco de más en el alcance de cobertura salen
del arreglo 2; los dos mutantes nuevos, también, y los dos murieron.

## T24 · M1, la suite contra base efímera — EJECUTADA POR EL HUMANO el 2026-08-19

Ejecutada en PowerShell desde la raíz del repositorio, con Docker Desktop ya
arrancado (el primer intento, con el demonio parado, abortó en el primer paso
tal y como promete T21):

```
powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
```

Salida real, resumida en sus pasos:

```
==> Comprobando Docker
    Docker responde.
==> Levantando PostgreSQL efimera (postgres:16-alpine) en 127.0.0.1:55432
Status: Downloaded newer image for postgres:16-alpine
==> Esperando a que la base acepte conexiones
    La base acepta conexiones.
==> Ejecutando la suite de base de datos (tests_bbdd)
..........                                                               [100%]
10 passed in 2.40s
==> Destruyendo el contenedor
SUITE DE BASE DE DATOS EN VERDE.
```

**Los 10 tests que la suite normal declara `skipped`** —los que necesitan una
base de verdad— **pasan contra PostgreSQL 16**: el DDL es idempotente aplicado
dos veces, el reproceso de un parte no duplica filas y `public` no recibe
ninguna tabla nuestra. Es la comprobación que ningún doble de conexión puede
dar, porque quien decide si un `CREATE ... IF NOT EXISTS` es idempotente de
verdad es el motor, no nuestro código.

El contenedor **queda destruido**: comprobado después con
`docker ps -a --filter name=postventa`, que no lista ninguno. La base efímera
escucha en `127.0.0.1:55432` y no toca en ningún momento el servidor
compartido `psql-albaranes-rs9k2`.

Primera ejecución en este puesto, así que Docker se descargó la imagen
`postgres:16-alpine` (digest `sha256:cf78e766...`). Las siguientes no
pagarán esa descarga.

## T25 · M2, el DDL contra la base real de dev — EJECUTADA POR EL HUMANO el 2026-08-19

Escritura en el servidor PostgreSQL compartido, con las dos pasadas que pide
la verificación. La ejecutó el humano, nunca un agente, y solo después de M1
en verde.

**Ni el FQDN del servidor, ni el usuario administrador, ni ninguna de las dos
contraseñas se escriben aquí**: es la misma regla que aplica el barrido de
secretos de T22 sobre `docs/INTEGRACION.md`, y vale igual para `progress/`.

### El dry-run, antes de tocar nada

`cargar_ddl` sobre los siete `.sql`, sin abrir conexión: **14 sentencias** —
1 `CREATE SCHEMA` + 6 `CREATE TABLE` + 7 `CREATE INDEX`—, **todas con
`IF NOT EXISTS` y todas cualificadas con `postventa.`**. Ni un `DROP`, ni un
`ALTER`, ni un `GRANT`, ni una sola sentencia fuera del esquema propio. Es lo
que exige la regla dura del proyecto sobre un servidor que sostiene la
producción de otros tres.

### Primera pasada

El script creó el rol `postventa_app` y la base `postventa` con ese rol como
propietario, y aplicó el DDL dentro del esquema. Comprobado después con una
consulta de **solo lectura** al catálogo:

```
TABLAS en 'postventa' (6): archivos, cierres, partes, preferencias_usuario,
                           remesas, validaciones
FALTAN: ninguna, las seis estan
INDICES en 'postventa': 13
NUESTRAS TABLAS EN 'public': ninguna (correcto)
RECUENTO DE FILAS: 0 en las seis
VEREDICTO M2: OK
```

Los **13 índices** son los 7 nuestros (`ix_remesas_recibida`,
`ix_partes_numero_incidencia`, `ix_partes_codigo_obra`, `ix_partes_remesa`,
`ix_validaciones_cola` —el parcial de la cola—, `ix_archivos_estado` e
`ix_cierres_estado`) más los 6 de clave primaria que PostgreSQL crea solo.

**Ninguna tabla nuestra en `public`**: es la comprobación que justifica el
`search_path` sin `public` (R8). Con `public` en el camino, una sentencia sin
cualificar habría aterrizado en las tablas de albaranes o de partes.

### Segunda pasada, la de la idempotencia

Mismo comando, otra vez:

```
==> Creando rol y base
    El rol postventa_app ya existia: no se toca.
    La base postventa ya existia: no se toca.

==> Aplicando el DDL del servicio en el esquema postventa
    DDL aplicado.
```

Y el catálogo, idéntico al de la primera pasada: mismas 6 tablas, mismos 13
índices, 0 filas, nada en `public`. **La re-ejecución no falla ni cambia
nada**, que es exactamente lo que promete el patrón «DDL idempotente al
arranque» heredado de sv3 y lo que hace seguro que la Function App lo aplique
cada vez que arranca.

La idempotencia ya estaba probada contra base efímera en M1; esto la confirma
contra el motor y la base reales, que es donde importa.

### Un tropiezo del script de comprobación, que no era del código

La primera versión del script de verificación —que vive fuera del repositorio,
como todos los de las manuales— pedía `ajustes.pg_schema` y reventó con
`AttributeError`. Los campos de `config/settings.py` van **en español**
(`pg_esquema`, `pg_base`, `pg_usuario`) y exponen su `validation_alias` **en
inglés** (`PG_SCHEMA`, `PG_DB`, `PG_USER`), que es lo que lee el `.env` y lo
que exporta `infra/crear_base_postventa.ps1`. Ese doble nombre es deliberado y
está bien: el fallo era del script de fuera, no del servicio.

## T26 · M3, el documento de integración en `azure-apps` — HECHA A MEDIAS, POR DECISIÓN DEL HUMANO

Los dos ficheros quedan **escritos en el árbol de trabajo de `azure-apps`**,
preparados el 2026-08-19:

- `postventa_incidencias.md` (nuevo, 172 líneas): copia de `docs/INTEGRACION.md`
  con la cabecera que exige la regla 2 de ese repositorio —origen
  `postventa-incidencias`, commit `aeabbbd`, fecha— y una nota de estado: la
  base ya existe en el servidor, pero el código sigue en su rama sin mergear.
- `README.md`: la fila del índice detrás de `remesas.md`, que da de alta al
  proyecto como **cuarto inquilino** de `psql-albaranes-rs9k2` con base propia.

Barrido de secretos pasado sobre la copia —FQDN de Azure, GUID, IPv4,
`password=`, usuario administrador—: **limpia**.

**Lo que NO se ha hecho: el commit.** El humano decidió el 2026-08-19 dejarlo
sin commitear. Conviene que conste con precisión, porque `azure-apps` **sí es
un repositorio git** —su último commit es `6bfa3ed`— y su propio `README.md`
explica por qué dejó de ser una carpeta suelta: «sin historial, un documento
viejo es indistinguible de uno vigente».

**Consecuencia práctica**: mientras no se commitee, el documento no tiene
fecha comprobable ni diff, y un `git checkout` o una limpieza del árbol de
`azure-apps` se lo lleva por delante. La tarea se marca hecha en lo que
depende de este proyecto —el contenido está escrito y verificado— y queda
**pendiente el commit en el otro repositorio**, que es del humano.

## Los dos arreglos de la review (2026-08-19, tras el veredicto CHANGES_REQUESTED)

La review (`progress/review_F-005.md`) rechazó F-005 con **dos** cambios
requeridos. Ninguno toca la arquitectura. Aquí queda qué se hizo y por qué.

### Arreglo 1 · El host no local del test pasa a ser inventado

**Commit `9284e79`.** Fichero:
`services/postventa-api/tests/test_f005_conexion.py`, en el test
`test_f005_r11_cualquier_otro_host_no_es_local`.

**El defecto.** El test escribía el **nombre completo de dominio** del
servidor PostgreSQL compartido dentro de un fichero versionado. `CLAUDE.md` lo
prohíbe sin matices —«el historial de git no suelta lo que entra»— y esta
misma feature se lo prohibía a sí misma en otros dos sitios:
`test_f005_ajustes.py` afirma que ese sufijo de dominio no aparece en los
ejemplos de configuración, y `test_f005_integracion_sin_secretos.py` usa a
propósito un host inventado como control negativo justo para no escribir el
real.

**El arreglo.** Se sustituye por el mismo host inventado que ya usa el fichero
hermano, y el docstring explica en prosa cuál es el servidor que preocupa
**sin escribir su sufijo de dominio**. El test no pierde nada: lo que
comprueba es que un host que no es esta máquina se rechaza.

**Barrido de la rama, después del arreglo.** Se buscó el nombre del recurso
seguido de punto en todo lo versionado:

```
git grep -n "psql-albaranes-rs9k2\." -- .
(sin resultados)
```

Las apariciones que quedan del sufijo de dominio son las legítimas —los dos
`assert ... not in ejemplo` de `test_f005_ajustes.py`, que vigilan que no
aparezca, y el host **inventado** del control negativo de
`test_f005_integracion_sin_secretos.py`— más la mención al patrón en este
mismo informe. El fichero `.env` local **no está versionado**
(`git check-ignore` lo confirma: `.gitignore:27`), igual que `.pytest_cache/`.

17 tests de `test_f005_conexion.py` en verde tras el cambio.

### Arreglo 2 · Los avisos se recortan al persistirlos (observación O1)

**Commit `882d3c6`.** Ficheros:
`services/postventa-api/infrastructure/persistencia/mapeo.py` (la constante
`_RECORTE_AVISO`, `json_de_avisos` y `_recortar_aviso`) y sus tests en
`services/postventa-api/tests/test_f005_mapeo.py`.

**La decisión, con fecha y dueño.** O1 venía heredada de F-004 y
`progress/current.md` encargaba a F-005 decidir si el valor crudo del modelo
se guarda o se recorta. Se quedó sin decidir, y la review lo cazó. **El humano
decidió el 2026-08-19 que se RECORTA**, que es lo que recomendaba el reviewer.
Queda como decisión **D7**.

**El defecto.** El aviso de etiqueta desconocida
(`application/pipelines/paso_firma.py`) incrusta el valor crudo que devolvió
el modelo, y `json_de_avisos()` lo publicaba verbatim, sin cota, en la columna
`avisos jsonb` de `04_validaciones.sql`. Un aviso es un **diagnóstico**, no un
almacén; y esa es precisamente la tabla cuyo DDL proclama que ahí no se copia
texto del cliente (R21, R39). Además el disco del servidor es compartido con
otros tres proyectos, y `design.md` fija como restricción «sin JSON crudo
gigante».

**La cota: 240 caracteres, y por qué ese número.** No es un número al azar. Se
midieron los avisos que el pipeline emite de verdad:

| Aviso | Texto fijo | Parte variable |
|---|---|---|
| etiqueta desconocida (`paso_firma.py`) | **111** | el valor que devolvió el modelo |
| campo fuera del contrato (`paso_extraccion.py`, `paso_firma.py`) | 76 | el nombre del campo |
| confianza mal declarada (`confianza.py`) | 73 | — |
| reproceso (`paso_persistencia.py`) | 66 | — |
| ZIP que no se puede abrir (`zip_estandar.py`) | 41 | nombre del documento + error |
| PDF sin páginas / no es PDF ni ZIP | 36–37 | nombre del documento |
| campo que el modelo no devolvió | 32 | nombre del campo |

El esqueleto fijo más largo son **111** caracteres. La parte variable más
grande no es el valor del modelo sino **el nombre del documento**, que dentro
de un ZIP es una ruta (`remesa.zip/carpeta/parte 0012345.pdf`) y pasa de los
cien caracteres con facilidad. 240 es algo más del doble del esqueleto y deja
unos 130 libres para esa parte variable: **ningún aviso legítimo se mutila**.
Por arriba acota lo que entra en la base: un parte emite del orden de una
decena de avisos, así que la columna queda en unos pocos KB por fila en vez de
en un volcado del modelo.

**Por qué no el 80 de `ddl.py`.** El patrón sí se reutiliza —constante con su
razón escrita, recorte con la señal `…`, test a cada lado del borde— pero el
número no puede ser el mismo: 80 cortaría por la mitad el aviso legítimo de
111 caracteres, que es justo lo que no se quiere. El 80 de `ddl.py` acota el
**mensaje de un error**, donde basta reconocer la sentencia culpable; aquí se
acota un diagnóstico que alguien va a leer entero en la cola de revisión.

**Fase RED (obligatoria en `critico`): los tests, antes que el código.**

Los cuatro tests se escribieron primero. Comando exacto, desde
`services/postventa-api`:

```
./.venv/Scripts/python.exe -m pytest tests/test_f005_mapeo.py -q -k "aviso"
```

Salida real, **en rojo**, con `json_de_avisos()` todavía sin recorte (los
tramos de equis largos van abreviados con `[…]` para que la tabla se lea; el
resto es literal):

```
    def test_f005_r20_un_aviso_mas_largo_se_recorta_a_240_y_lo_dice():
        assert len(AVISO_DE_241) == 241

        guardado = json.loads(json_de_avisos((AVISO_DE_241,)))

>       assert guardado == [AVISO_DE_241[:240] + "…"]
E       AssertionError: assert ['aviso inven...xxxxxxxxxxxx'] == ['aviso inven...xxxxxxxxxxx…']
E
E         At index 0 diff: 'aviso inventado: xxx[…]xxx' != 'aviso inventado: xxx[…]xx…'
E         Use -v to get more diff

tests\test_f005_mapeo.py:258: AssertionError
________ test_f005_r20_la_cota_se_aplica_a_cada_aviso_y_no_al_conjunto ________

        guardado = json.loads(
            json_de_avisos(("corto inventado", AVISO_DE_241, "otro corto inventado"))
        )

        assert guardado[0] == "corto inventado"
>       assert guardado[1] == AVISO_DE_241[:240] + "…"
E       AssertionError: assert 'aviso invent...xxxxxxxxxxxxx' == 'aviso invent...xxxxxxxxxxxx…'
E
E         Skipping 230 identical leading characters in diff, use -v to show
E         - xxxxxxxxxx…
E         ?           ^
E         + xxxxxxxxxxx
E         ?           ^

tests\test_f005_mapeo.py:288: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f005_mapeo.py::test_f005_r20_un_aviso_mas_largo_se_recorta_a_240_y_lo_dice
FAILED tests/test_f005_mapeo.py::test_f005_r20_la_cota_se_aplica_a_cada_aviso_y_no_al_conjunto
2 failed, 4 passed, 13 deselected in 1.07s
```

Los otros dos —el borde de 240 exactos y el aviso legítimo más largo— pasaban
ya en rojo, y **es correcto que pasaran**: fijan lo que la cota **no** puede
romper, no lo que la cota añade. Los que tenían que fallar, fallaron.

Con el código escrito, el mismo fichero entero: **19 passed in 0.44 s**.

**Los cuatro tests, y qué fija cada uno:**

- `..._un_aviso_de_240_caracteres_se_guarda_entero`: el borde por debajo. El
  aviso entra completo y **sin** la marca de recorte.
- `..._un_aviso_mas_largo_se_recorta_a_240_y_lo_dice`: el borde por encima, y
  que la señal `…` esté. Sin la señal, quien lea la cola creería estar viendo
  el aviso entero y buscaría la causa donde no está.
- `..._el_aviso_legitimo_mas_largo_del_pipeline_no_se_mutila`: el texto de 111
  caracteres copiado literalmente de `paso_firma.py`. Es la razón del número
  puesta como test: si alguien bajara la cota hasta rozarlo, este test lo dice.
- `..._la_cota_se_aplica_a_cada_aviso_y_no_al_conjunto`: el recorte es **por
  aviso**. Si se aplicara al JSON entero, un aviso largo se llevaría por
  delante a los cortos de detrás, que suelen ser los que explican qué le falta
  al parte.

El 240 va escrito **a mano** en el test y no importado de `mapeo.py`, por la
misma razón por la que `test_f005_ddl_seguro.py` escribe su 80: un test que
leyera la constante se movería con ella y dejaría de vigilar el borde.

### Campaña de mutación relanzada (la exige `critico` al tocar producción)

```
python -m harness.mutacion --feature F-005
```

**106 mutantes generados, 106 evaluados, 103 muertos, 0 supervivientes,
3 timeouts, 330,4 s.** Los dos mutantes de más respecto a la campaña de las
16:13 son los del recorte, y **los dos murieron**:

| Mutante nuevo | Veredicto | Quién lo mata |
|---|---|---|
| `mapeo.py:67` `_RECORTE_AVISO = 240 -> 241` | muerto | el test del borde de 241: con la cota en 241, el aviso de 241 caracteres dejaría de recortarse |
| `mapeo.py:170` `if len(aviso) <= _RECORTE_AVISO` → `<` | muerto | el test del borde de 240: con `<`, un aviso de exactamente 240 se recortaría |

Y el tercer mutante que toca la línea nueva, `mapeo.py:164`
(`ensure_ascii=False -> True` dentro del `json.dumps` que ahora lleva la
comprensión), también muere: lo caza el test de acentos que T23 había añadido.

**Los tres timeouts son los tres de siempre** —`ddl.py:131`, `158` y `162`,
mismo operador y misma mutación—, ya verificados uno a uno con reloj externo
(exit 124). No ha aparecido ninguno nuevo y ninguno cae en `mapeo.py`. El
análisis durable se ha **traído de vuelta** a `progress/mutacion_F-005.md`,
que el generador reescribe en cada campaña.

### Un tercer commit, de higiene

`progress/review_F-005.md` estaba sin commitear. Se ha versionado —mismo
tratamiento que los `impl_*.md`— porque además la campaña paralela **se niega
a arrancar con el árbol sucio**: crea sus worktrees desde `HEAD` y evaluaría
un código distinto del que hay en disco. Lo dice el propio comando al abortar.

### Lo que NO se ha tocado

- Las 27 tareas de `tasks.md` siguen como estaban; T26 sigue `[~]`, que la
  review declaró **deuda aceptable con dueño** y no motivo de rechazo. Su
  traslado a `progress/history.md` al cerrar es cosa del líder.
- Los **16 worktrees huérfanos** de una campaña anterior (observación O-B de
  la review) siguen registrados en `.git/worktrees`, anclados en `48fb104`. No
  son de esta sesión, viven fuera del repositorio y no ensucian `git status`.
  No se tocan: la review los declara mejora **genérica** de
  `harness/mutacion.py` y su sitio es `arnes-base`.
- Dos avisos `I001` de ruff en los bloques de import de los dos ficheros de
  test tocados: **son deuda previa**, comprobado ejecutando ruff sobre la
  versión de esos mismos ficheros en el commit anterior (`47da451`), donde ya
  salían. Entran en los 53 avisos que `init.sh` reporta como deuda que no
  bloquea.

### Verificación final

`bash harness/init.sh`, tal cual, sin pipes ni decoración:

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 53 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
16 passed in 0.47s
[OK] pytest en verde (con medición de cobertura)
682 passed, 10 skipped in 19.36s
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: 97.0% de 596 líneas cambiadas cubiertas (578/596, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-005-persistencia
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

Los dos cambios requeridos quedan hechos. Nada más de F-005 se ha rehecho.
