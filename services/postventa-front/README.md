<!-- services/postventa-front/README.md -->
# postventa-front

Pantalla de carga y revisión de partes de posventa. HTML + Tailwind (CDN) +
Alpine.js + un `dev_server.py` de biblioteca estándar. **Sin cadena de build,
sin `package.json`, sin `node_modules`.**

En producción va desplegado como **Static Web App** con la Function enlazada al
mismo origen; eso es **F-010**. En local, `dev_server.py` reproduce ese mismo
comportamiento.

## Arrancar en local

Hacen falta **dos terminales**. El humano trabaja en PowerShell: una línea por
línea, sin `&&`.

**Terminal A — el backend** (la Azure Function):

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
func start --port 7073
```

El **7073 no es el puerto por defecto de `func`**: es el que espera el proxy.
Si no existe `local.settings.json`, cópialo antes de
`local.settings.json.example` y rellénalo.

**Terminal B — el front**:

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
.\dev_front.ps1
```

Y en `http://localhost:5173/`. El script es un envoltorio de una línea sobre:

```
python dev_server.py --port 5173 --api http://localhost:7073
```

Para ver la ayuda **sin arrancar nada**:

```
.\dev_front.ps1 -Ayuda
```

> **Por qué `-Ayuda` y no `-?`.** Con `powershell -File`, Windows PowerShell 5.1
> se queda el `-?`: no ejecuta el script (bien) pero tampoco imprime nada. Y la
> ayuda basada en comentarios (`<# .SYNOPSIS #>`) solo la indexa `Get-Help` si
> el bloque es **lo primero** del fichero, lo que chocaría con la convención de
> abrir cada fichero con un comentario con su ruta. `-Ayuda` funciona con
> `-File` y respeta las dos cosas.

## Probarlo

```
cd C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-front
python -m pytest -q
```

Eso ejecuta **todo**: los tests de Python y, a través del puente
`tests/test_f007_js.py`, los de JavaScript. Para lanzar solo estos últimos:

```
node --test "tests_js/*.test.js"
```

> **El argumento es el patrón, no la carpeta.** Desde Node 24, `node --test
> tests_js` intenta cargar el directorio como módulo y muere con
> `MODULE_NOT_FOUND` sin descubrir ningún test.

**Si `node` no está, la suite FALLA diciéndolo**, no se salta con un `skip`: un
salto silencioso volvería a dejar el front sin comprobar.

El servicio está declarado en `harness/servicios.json`, así que
`bash harness/init.sh` ejecuta esta suite y se pone en rojo si falla.

## Cómo está organizado, y por qué se puede probar sin navegador

```
js/cola.js       lógica pura        sin fetch, sin DOM   ← el grueso de los tests
js/pipeline.js   orquestación       recibe `api` inyectada
js/seleccion.js  lógica pura        sin DOM (recibe File[])
js/traza.js      lógica pura
js/confirmacion.js  lógica pura     el doble clic antes de archivar (R19)
js/api.js        adaptador HTTP     `fetch` y temporizadores inyectables
js/app.js        pegamento Alpine   NO se prueba: no debe tener lógica
```

**Regla de oro: si algo merece un test, no vive en `app.js`.** Hay dos guardias
en `tests/test_f007_estaticos.py` que lo vigilan, porque `app.js` es la única
habitación sin tests de la casa.

Los módulos se exponen en las dos direcciones —`window.X` para el navegador,
`module.exports` para `node --test`—, que es lo que permite probarlos sin
herramientas nuevas.

## Tres cosas del `index.html` que parecen cosméticas y no lo son

1. **Los scripts propios van al final del `<body>` y SIN `defer`.** Con
   `defer`, Alpine arrancaría antes de que exista `appPostventa` y la pantalla
   quedaría muerta.
2. **Alpine sí va con `defer`, en el `<head>` y con versión fija `3.14.1`.**
3. **Ningún `type="module"`**: un módulo se difiere de forma implícita, que es
   el mismo fallo por otra puerta.

Las tres las vigila `tests/test_f007_estaticos.py`.

## `dev_server.py` frente a la puerta de cobertura (decisión D1)

**Se prueba.** Es la opción **O1** de `specs/F-007-front/design.md` §9, y la
confirmó el humano el **2026-08-20**.

**El problema.** `harness/alcance.py` considera código de producción cualquier
`.py` cuya ruta no lleve un segmento `tests`, `specs`, `progress` o `docs`. No
hay lista de exclusiones, ni por fichero ni por servicio. `dev_server.py` llega
**entero como fichero nuevo** frente a `dev`, así que sus ~114 líneas entran en
el alcance de la feature hagamos lo que hagamos: **no existe la opción «no
tocarlo»**. Sin tests, la puerta lo cuenta como no cubierto y `init.sh` se pone
en rojo. Eso es exactamente lo que expulsó al front de F-001.

**Lo que se descartó, y por qué:**

| | Opción | Por qué no |
|---|---|---|
| **O2** | Añadir exclusiones configurables al arnés | Abre una puerta que se ensancha sola: cualquier fichero incómodo pasa a ser «script de desarrollo». Y es trabajo de **otro producto** (`arnes-base`), con su regla de propagación, no de esta feature |
| **O3** | Esconderlo en una carpeta ya excluida (`tests/`, `docs/`) | Es mentira: un servidor de desarrollo no es documentación ni un test. Y enseña el truco: «si no lo puedes probar, muévelo a `tests/`» |
| **O4** | Adelgazarlo hasta que casi no tenga líneas | Reescribir algo que ya funciona y está verificado. No elimina el problema, solo lo encoge |
| **O5** | Cerrar con el portero en rojo | `CLAUDE.md` lo prohíbe |

**Por qué O1 es mejor, y no solo «la que quedaba»:**

1. **Cierra dos criterios con el mismo trabajo**: que alguien compruebe el
   front, y qué hacer con `dev_server.py`. O2 y O3 resuelven el segundo y dejan
   el primero igual de abierto.
2. **`dev_server.py` no es un script cualquiera.** Es el único sitio donde se
   reproduce el comportamiento de la SWA en producción: proxy al mismo origen,
   cabeceras reenviadas, `x-ms-client-principal`. Si se rompe, el desarrollo
   local deja de parecerse al despliegue y nadie se entera hasta F-010. Es
   código que **merece** tests.
3. **Es barato y no toca el arnés.** El fichero no abre red por sí mismo: la
   conexión se crea en `_proxy` a través de `http.client.HTTP(S)Connection`,
   que en los tests se sustituye por un doble. Ni un socket.

Resultado: `tests/test_f007_dev_server.py`, y la puerta de cobertura mide esas
líneas en vez de contarlas como no medidas.

## Lo que este front NO hace (a propósito)

- **No guarda nada.** Ni `localStorage`, ni `sessionStorage`, ni `IndexedDB`,
  ni cookies. **Recargar la pestaña pierde el trabajo de revisión** y hay que
  volver a subir la remesa. Se acepta para el piloto (decisión **D4** del
  2026-08-20). La vía fácil está **prohibida**: los partes llevan DNI y
  observaciones manuscritas de clientes. La solución de verdad son endpoints de
  persistencia en `postventa-api`, dados de alta como
  **F-019 · Endpoints de persistencia**. Hay un test que impide tomar el atajo.
- **No hace login.** `/.auth/me`, el grupo de Entra y el `<TENANT_ID>` de
  `staticwebapp.config.json` son **F-010**. En local el backend va con
  `AUTH_DISABLED`.
- **No cierra la incidencia en Sigrid.** Es F-008 / F-009, y depende de un
  endpoint nuevo en otro repositorio.
- **No archiva desde tu puesto.** `/api/archivar` responde **503 «este entorno
  no archiva»** con la puerta de entorno apagada, que es lo **correcto**. El
  front lo pinta en azul y no en rojo justamente para que nadie intente
  «arreglarlo» tocando esa puerta.

## Datos personales

Los partes traen **DNI y observaciones manuscritas** de clientes reales.

- **Sí se enseñan en pantalla**: quien revisa los necesita para corregir una
  lectura y para decidir si el parte se cierra.
- **No se registran en ningún sitio.** El único registro que el front emite
  pasa por `js/traza.js`, que acepta **cuatro claves** (`hash`, `paso`,
  `estado`, `http`) y tira el resto. Es un filtro, no una convención.
- **No viajan al archivar**: `/api/archivar` recibe cinco campos y ninguno es
  personal.
- **No entran en el repositorio**: los fixtures son PDFs mínimos construidos en
  el propio test. Lo vigila `tests/test_f007_sin_datos_reales.py`.

## Navegador soportado

**Edge / Chrome** (decisión **D5**). El selector de carpeta usa
`webkitdirectory`, que Firefox no implementa igual. Es el navegador corporativo.

## Sobre `staticwebapp.config.json`

**No lleva comentarios, y no es un olvido**: el esquema de Static Web Apps
declara `additionalProperties: false`, así que cualquier clave de más —un
`$comentario`, por ejemplo— hace que la CLI **rechace el fichero entero** con
un `NoAdditionalPropertiesError`. Pasó de verdad al desplegar F-010 el
2026-08-21: Azure lo aceptaba igualmente, pero fiarse de eso es frágil, porque
el día que la CLI deje de subir la configuración la aplicación se queda **sin
autenticación** y sin que nadie se entere. Por eso lo que había que explicar se
explica aquí.

- **`openIdIssuer` lleva el marcador `<TENANT_ID>` a propósito.** El
  identificador de inquilino no se versiona (regla de `CLAUDE.md`). Lo
  sustituye `infra/desplegar_front.ps1` **en una copia de trabajo temporal**,
  que se borra al terminar: el fichero del repositorio no se toca nunca.
- **`clientIdSettingName` y `clientSecretSettingName` no son valores, son
  punteros**: nombran App Settings de la Static Web App (`AZURE_CLIENT_ID` y
  `AZURE_CLIENT_SECRET`), que el despliegue rellena desde el Key Vault. Es la
  misma convención que usan el portal y los demás fronts del ecosistema.
- **`allowedRoles: ["authenticated"]` NO restringe por grupo**: solo exige
  estar autenticado. Quien impide entrar a quien no es del piloto es la
  **asignación requerida** de la aplicación empresarial en Entra, con el grupo
  `posventa-usuarios` asignado. Sin eso, cualquiera de la empresa entraría
  aunque no vea la tarjeta en el portal.
