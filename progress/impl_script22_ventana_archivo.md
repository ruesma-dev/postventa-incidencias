<!-- progress/impl_script22_ventana_archivo.md -->
# `infra/22_ventana_archivo.ps1` · la segunda puerta

> **Veredicto: hecho y en verde.** El script existe, se parsea sin errores y se
> ha ejecutado en modo `-Estado` —la única llamada permitida—. `bash
> harness/init.sh` → **ENTORNO LISTO**.
>
> **Y un hallazgo que no estaba en el encargo y que hay que mirar hoy:** el
> encargo daba por supuesto que `ARCHIVO_HABILITADO` valía `false`. **Vale
> `true`.** Y `CIERRE_HABILITADO` **también**. Las dos puertas de `dev` están
> **abiertas ahora mismo**. Detalle y contraste en §3.

Rama `chore/script-22-ventana-archivo`. Ni un `git push`, ni merge a `dev`, ni
cambio de rama. Ni una línea de `services/`, de `.env`, de secretos ni de
ningún otro script de `infra/`. **Ninguna escritura** contra Azure, Sigrid,
SharePoint ni el PostgreSQL.

---

## 1 · Qué cambió

| Fichero | Qué es |
|---|---|
| `infra/22_ventana_archivo.ps1` | **Nuevo.** Consulta, abre y cierra la ventana de archivo en **SharePoint** (`ARCHIVO_HABILITADO` de nuestra Function App). 414 líneas. |
| `progress/current.md` | Entrada nueva del 2026-09-16 al principio: la tabla de las **dos puertas**, el estado real leído y el aviso de que un despliegue vuelve a cerrar la de SharePoint. |
| `progress/impl_utillaje_puesta_en_marcha.md` | Puntero en la fila del 19 de la tabla «Qué cambió», y **addendum fechado al final** con las dos puertas, por qué nace el 22 y qué hace. |

El `.ps1` es **ASCII puro, CRLF, sin BOM** —comprobado byte a byte; es lo que
usan todos los demás `.ps1` del directorio, que **no llevan BOM** precisamente
porque evitan los acentos, y `test_f010_scripts_infra.py` los lee con
`encoding="ascii"`—. Empieza por su ruta relativa y no escribe ni un nombre de
recurso literal.

---

## 2 · Decisiones de diseño

Calcado a `19_ventana_escritura.ps1` en forma, estructura y tono. Lo que no es
copia literal, y por qué:

1. **Los mismos códigos de salida que el 19** (2 sin sesión, 3 sin `az`, 4 modo
   ambiguo, 5 sin confirmar, 6 sin lectura, 8 escritura fallida, 9 no coincide).
   Son dos puertas distintas pero el mismo gesto: quien automatice una y otra no
   puede tener que aprender dos numeraciones. Va dicho en el propio comentario.
2. **El modo por omisión solo lee.** Sin parámetros, `-Estado`. Verificado en
   ejecución real: imprime el estado y sale `0` **sin escribir nada** (§3).
3. **El aviso de `-Abrir` dice lo que es de verdad**, y no lo del 19: detrás hay
   el **SharePoint de Posventa**, lo que se sube son **partes escaneados, PDF
   con datos personales de clientes, DNI incluido**, y la biblioteca es un
   sistema **ajeno y compartido** —lo que entra ahí no lo borra este servicio—.
4. **Dice explícitamente que las dos puertas son independientes**, tanto en el
   encabezado como en el aviso de `-Abrir` y en la salida de `-Estado`: abrir
   esta **no** abre el cierre en Sigrid, abrir la del ERP **no** abre esta, y
   para el circuito completo —archivar, adjuntar, cerrar— hacen falta **las
   dos**. Es la confusión que motivó el encargo.
5. **`-Cerrar` no pide confirmación**, igual que el 19: cerrar siempre es seguro
   y una palabra que teclear en ese camino solo consigue que alguien la salte y
   deje la puerta abierta.
6. **Escribir y releer van en la MISMA función**, `Fijar-Ventana`. Separarlas
   permitiría un camino que escribe y da por bueno lo que pidió. Lo que se
   imprime es el valor **releído del plano de gestión**; si no coincide con lo
   pedido, sale con `9`. Y avisa de que la Function tarda unos segundos en
   reiniciar y hasta entonces puede servir con el valor anterior — el veredicto
   del **borde** (que `/api/archivar` responda 503) lo da
   `verificar_despliegue.ps1`, no este script.
7. **Falla cerrado.** Si `az` falla, `Leer-Ventana` devuelve el desconocido y el
   script sale con `6` diciendo **«Estado DESCONOCIDO»**, no «cerrada». Mismo
   criterio que `Get-Ventana-De-Escritura` de `verificar_despliegue.ps1`. La
   App Setting **ausente** sí es «cerrada», que es otra cosa: es el valor por
   defecto del código (`config/settings.py`, `archivo_habilitado = False`).
8. **Cada despliegue la vuelve a cerrar**, escrito en el encabezado con la
   referencia exacta: `infra/desplegar_backend.ps1` **línea 429** fuerza
   `ARCHIVO_HABILITADO=false` en cada pasada. Quien despliega y la quería
   abierta tiene que volver a abrirla a mano. Es el motivo de que apareciera
   cerrada tras el despliegue de las 07:33 UTC. También se repite en el último
   mensaje de los modos de escritura, que es donde lo va a leer quien acabe de
   abrirla.
9. **Ni un nombre de recurso.** `00_vars_postventa.ps1` por punto (R7). El único
   literal propio es `$APP_SETTING_VENTANA = "ARCHIVO_HABILITADO"`, arriba, para
   que se vea de un vistazo cuál es el interruptor que se toca.
10. **El identificador de suscripción se lee para saber que hay sesión y se
    descarta acto seguido** (`$suscripcion = $null`): no se imprime, no se
    escribe y no aparece en ningún mensaje (R8).
11. **El defecto de PowerShell 5.1 (F-029), esquivado y explicado.** El fallo es
    que PowerShell se come las **comillas dobles** que van dentro de un
    argumento de un ejecutable **nativo** —lo que rompió `& $python -c $codigo`
    en el 07 (líneas 161 y 248) y el 17 (línea 196), y que
    `Invoke-PythonDelServicio` del 08 documenta—. Aquí los argumentos se pasan
    como **array** (`az @Argumentos`) y **ningún argumento lleva comillas dobles
    dentro**: el único filtro JMESPath usa comillas **simples**
    (`[?name=='...']`), que PowerShell entrega tal cual. Va dicho en el
    encabezado y repetido junto a la función, para que nadie «mejore» el filtro
    metiéndole comillas dobles.

### Lo que NO hace, a propósito

- **No toca ninguna otra configuración.** Su única escritura es un `--settings`
  con esa variable y nada más.
- **No dot-sourcea `08_lectura_sigrid_comun.ps1`**: no habla con la pasarela del
  ERP. Define sus propias `Salir-Con` y `Valor-De-Az`, como el 19.

---

## 3 · Verificación ejecutada, con la salida real

### a) Análisis sintáctico — la comprobación que habría pillado F-029

```
PS> $errs = $null
PS> $toks = [System.Management.Automation.PSParser]::Tokenize(
        (Get-Content -Raw -LiteralPath .\infra\22_ventana_archivo.ps1), [ref]$errs)
PS> "22_ventana_archivo.ps1 : $($toks.Count) token(s), $($errs.Count) error(es) de sintaxis"

22_ventana_archivo.ps1 : 1180 token(s), 0 error(es) de sintaxis
```

### b) Ejecución real en modo `-Estado` (solo lectura)

```
PS> powershell -ExecutionPolicy Bypass -File .\infra\22_ventana_archivo.ps1

Ventana de archivo en SharePoint
--------------------------------
  Grupo de recursos : rg-postventa-dev
  Function App      : func-postventa-dev
  App Setting       : ARCHIVO_HABILITADO
  Modo              : estado

Ahora mismo la ventana esta abierta.

ABIERTA: /api/archivar puede SUBIR partes al SharePoint de Posventa.
Si no hay una sesion de archivado en curso, cierrala: -Cerrar.

Esta es la puerta de SHAREPOINT. La del ERP es otra (CIERRE_HABILITADO): miralas por separado con el 19.

No se ha escrito nada.

CODIGO DE SALIDA: 0
```

### c) EL ENCARGO SUPONÍA `false` Y VALE `true`. Contraste directo

El encargo decía: «ahora mismo `ARCHIVO_HABILITADO` vale **`false`**». **No es
así.** Antes de dar por buena la salida del script contrasté con `az` a mano,
por si el que mentía era el script:

```
PS> az functionapp config appsettings list --name func-postventa-dev `
      --resource-group rg-postventa-dev `
      --query "[?name=='ARCHIVO_HABILITADO' || name=='CIERRE_HABILITADO'].{n:name,v:value}" `
      -o tsv --only-show-errors

ARCHIVO_HABILITADO      true
CIERRE_HABILITADO       true
LASTEXITCODE: 0
```

**El script dice la verdad**: `true` → «abierta». Lo que estaba desactualizado
era la premisa del encargo, y encaja con su propio relato: el humano **abrió
esa puerta a mano hoy** y **sigue abierta**.

**Y hay más de lo que se preguntaba: la puerta del ERP también está abierta.**
`CIERRE_HABILITADO=true` en `dev`. **Ninguna de las dos la ha abierto este
trabajo**, y este agente **no cierra nada**: es decisión del humano. Si no hay
una sesión de verificación en curso, lo que procede es:

```
powershell -ExecutionPolicy Bypass -File infra\22_ventana_archivo.ps1 -Cerrar
powershell -ExecutionPolicy Bypass -File infra\19_ventana_escritura.ps1 -Cerrar
```

### d) R7 y R8 a mano sobre el fichero nuevo

```
$ grep -n "rg-postventa|func-postventa|kv-postventa|stpostventa|swa-postventa|..." infra/22_ventana_archivo.ps1
(vacío)
$ grep -nE "[0-9a-f]{8}-[0-9a-f]{4}|https?://|\.azurewebsites\.|\.sharepoint\.|IP" infra/22_ventana_archivo.ps1
(vacío)
```

Ni un nombre de recurso literal, ni un GUID, ni un FQDN, ni una IP, ni una
credencial. Tampoco en este informe.

### e) Codificación

```
$ file infra/22_ventana_archivo.ps1
infra/22_ventana_archivo.ps1: ASCII text, with CRLF line terminators
bytes no ASCII: 0 · BOM: no · 414 líneas CRLF
```

Idéntico a `19_ventana_escritura.ps1`, `00_vars_postventa.ps1` y
`verificar_despliegue.ps1`, todos `ASCII text, with CRLF`. **No lleva BOM a
propósito**: el punto 10 del encargo lo condicionaba a «si eso es lo que usan
los demás», y no lo usan — resuelven el problema de PowerShell 5.1 por la vía
de no escribir acentos, que es la convención del punto 9.

### f) `bash harness/init.sh`, tal cual

```
[OK] Arnés v1.5.2 (2026-08-18)
    28 features, 13 abiertas, en curso: ninguna, bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 61 avisos (deuda previa, no bloquea).
62 passed in 4.49s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: N/A (la rama chore/script-22-ventana-archivo no corresponde a ninguna feature declarada)
[OK] Rama actual: chore/script-22-ventana-archivo
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

La caché de los servicios es legítima aquí: **no se ha tocado `services/`**.
Los 61 avisos de `ruff` son la deuda previa; ninguno en lo entregado, que no es
Python.

### NO se ejecutó

`-Abrir` y `-Cerrar`, como exige el encargo. Abrir es decisión del humano.

---

## 4 · Verificaciones MANUAL pendientes

- [ ] `22_ventana_archivo.ps1 -Abrir`: que el aviso se lee bien en pantalla, que
      exige teclear `ABRIR`, que cualquier otra cosa aborta con `5` sin tocar
      nada, y que al releer dice «abierta».
- [ ] `22_ventana_archivo.ps1 -Cerrar`: cierra sin preguntar y al releer dice
      «cerrada».
- [ ] El veredicto del **borde**, que este script no da: `/api/archivar`
      responde **503** con la ventana cerrada (`verificar_despliegue.ps1`).
- [ ] **Decidir si se cierran las dos puertas de `dev`**, hoy abiertas (§3c).

---

## 5 · Lo que queda fuera, y alguien debería decidirlo

1. **El 22 no tiene tests.** Los del 19 viven en
   `services/postventa-api/tests/test_f012_scripts_infra.py` y el censo de R1,
   R7 y R8 en `test_f010_scripts_infra.py` —ambos con **listas fijas de
   nombres**, así que el 22 **no entra en ningún barrido automático**—. Añadirlo
   exigía tocar `services/`, que este encargo **prohíbe expresamente**. Es la
   única desviación respecto al listón del 19, y está aquí para que no se pierda:
   lo comprobado a mano en §3d y §3e es exactamente lo que esos tests
   comprobarían solos en cada edición futura.
2. **Los documentos que todavía llevan el `az` copiado a mano** para abrir
   `ARCHIVO_HABILITADO` no se han tocado (fuera de alcance). Mientras no
   remitan al 22, conviven las dos vías y la del documento es la que se queda
   vieja — el mismo aviso que dejó el informe de F-012 sobre el guion del
   bloque 9 y el script 19.
3. **F-029 sigue abierta.** Aquí solo se ha **evitado** el defecto en el fichero
   nuevo; el 07 y el 17 siguen rotos.

---

## 6 · Evidencias

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados · suite raíz del arnés** | **62 pasan**, 0 fallan | `bash harness/init.sh` |
| **Tests ejecutados · suites de servicio** | **en verde**, resueltas por caché (`árbol sin cambios desde el último verde`) — legítimo: no se tocó `services/` | `bash harness/init.sh` |
| **Tests nuevos de este encargo** | **0**, y es una desviación consciente: añadirlos exigía tocar `services/`, prohibido por el encargo (§5.1) | — |
| **Cobertura de las líneas cambiadas** | **N/A.** Lo entregado es **PowerShell y Markdown**; `harness/alcance.py` solo mide `.py`. El propio `init.sh` lo dice: `PUERTA COBERTURA: N/A (la rama ... no corresponde a ninguna feature declarada)` | línea `PUERTA COBERTURA` del `init.sh` |
| **Mutantes generados y supervivientes** | **N/A**, por lo mismo: la campaña de mutación solo opera sobre `.py` y no se ha añadido ni modificado una línea de Python. No se ha lanzado. | — |
| **Tiempo de ejecución de la suite** | **4,49 s** (suite raíz, 62 tests) | salida de la propia suite |
| **Análisis sintáctico PowerShell** | **0 errores**, 1 180 tokens | `PSParser::Tokenize`, §3a |
| **Ejecución real `-Estado`** | código de salida **0**, veredicto «abierta», **sin escribir** | §3b |
| **Contraste del veredicto contra `az`** | `ARCHIVO_HABILITADO=true` · `CIERRE_HABILITADO=true` — el script **dice la verdad** | §3c |
| **Codificación** | ASCII puro, CRLF, sin BOM, 414 líneas | `file` + barrido de bytes, §3e |
| **R7 / R8** | **0** nombres de recurso literales, **0** identificadores, FQDN, IP o credenciales | §3d |
| **`ruff`** | **61 avisos**, la deuda previa; **0** en lo entregado (no es Python) | `bash harness/init.sh` |

> Nota de método: en un proyecto que sí fuera Python, la cobertura de líneas
> cambiadas y la campaña de mutación serían obligatorias. Aquí no están porque
> **no son aplicables a un `.ps1`**, no porque se hayan omitido.
