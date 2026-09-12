<!-- progress/mutacion_F-026.md -->
# F-026 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-026 --workers 8` el 2026-09-12 11:14.

## Alcance

Origen del diff: **rama** (`6cabd39bef601ad3d9e39f0e44307a73088055f0` .. `feature/F-026-aprobacion-humana`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/contexto_parte.py` | 25 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 609 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 650 |
| `services/postventa-api/config/settings.py` | 135 |
| `services/postventa-api/domain/models/aprobacion.py` | 285 |
| `services/postventa-api/domain/models/cierre.py` | 365 |
| `services/postventa-api/domain/models/errores.py` | 479 |
| `services/postventa-api/domain/models/grafico.py` | 367 |
| `services/postventa-api/domain/models/persistencia.py` | 80 |
| `services/postventa-api/domain/ports/erp.py` | 89 |
| `services/postventa-api/domain/ports/grafico.py` | 78 |
| `services/postventa-api/domain/ports/persistencia.py` | 62 |
| `services/postventa-api/domain/ports/usuarios_sigrid.py` | 59 |
| `services/postventa-api/function_app.py` | 352 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 170 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 175 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 318 |
| `services/postventa-api/infrastructure/sigrid/__init__.py` | 11 |
| `services/postventa-api/infrastructure/sigrid/cliente.py` | 420 |
| `services/postventa-api/infrastructure/sigrid/consultas.py` | 208 |
| `services/postventa-api/infrastructure/sigrid/escrituras.py` | 246 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 182 |
| `services/postventa-api/infrastructure/sigrid/graficos.py` | 338 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 365 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 314 |
| **Total** | **6382** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 242 |
| Mutantes evaluados | 242 |
| Muertos | 228 |
| Supervivientes | 14 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 2940.7 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/domain/models/aprobacion.py:114` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**HUECO REAL · tapado con un test nuevo** (`test_f026_una_aprobacion_no_se_puede_modificar_despues_de_creada`,
en `tests/test_f026_aprobacion_dominio.py`).

Por qué ningún test lo cazaba: la suite construía aprobaciones y las
comparaba, pero **nunca intentaba modificar una**. `frozen=True` no cambia
ningún resultado mientras nadie asigne.

Por qué importa, y por qué no se deja como equivalente: la `Aprobacion` viaja
desde el repositorio hasta la puerta que decide si un parte que la máquina
rechazó entra en el circuito, y lo que esa puerta compara es su
`destino_aprobado`. Con la instancia mutable, cualquier paso intermedio podría
cambiarlo entre leerla y comprobarla, y el registro que queda en la base diría
otra cosa que la decisión que se tomó. El test asigna a `destino_aprobado` y
exige `FrozenInstanceError`.

Verificado a mano: aplicada la mutación, el test falla; revertida, pasa.

### 2. `services/postventa-api/domain/models/aprobacion.py:180` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis

**HUECO REAL · tapado con un test nuevo** (`test_f026_r8_un_no_apto_sin_motivos_no_es_aprobable`,
en `tests/test_f026_aprobacion_dominio.py`).

La línea es la segunda guarda de `es_aprobable`:

```python
if not validacion.motivos:
    return False
```

Por qué ningún test lo cazaba: los tests del dominio usan `validar_parte` **de
verdad**, y F-004 no emite hoy la combinación «no apto **sin** motivos» —sin
motivos, el veredicto es apto—. La combinación solo se alcanza construyendo el
`ResultadoValidacion` a mano, que es lo que hace el test nuevo.

Por qué la guarda no sobra, y por tanto no es equivalente: sin ella queda
`all(...)` sobre una tupla vacía, que en Python es **verdadero**. Un no apto
del que no se sabe el motivo pasaría a ser aprobable. Es la línea que impide
que una regla futura de F-004 abra por accidente la única puerta por la que un
parte rechazado llega al ERP de producción.

Verificado a mano: aplicada la mutación, el test falla; revertida, pasa.

### 3. `services/postventa-api/domain/models/errores.py:871` [booleano]

- Original: `def __init__(self, motivo: str, *, reintento_seguro: bool = True) -> None:`
- Mutado:   `def __init__(self, motivo: str, *, reintento_seguro: bool = False) -> None:`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 4. `services/postventa-api/domain/models/grafico.py:184` [booleano]

- Original: `ya_cerrada: bool = False`
- Mutado:   `ya_cerrada: bool = True`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 5. `services/postventa-api/domain/models/grafico.py:187` [booleano]

- Original: `idempotente_previsto: bool = False`
- Mutado:   `idempotente_previsto: bool = True`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 6. `services/postventa-api/domain/models/persistencia.py:233` [booleano]

- Original: `idempotente: bool = False`
- Mutado:   `idempotente: bool = True`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 7. `services/postventa-api/infrastructure/persistencia/mapeo.py:182` [booleano]

- Original: `return json.dumps([codigo.value for codigo in codigos], ensure_ascii=False)`
- Mutado:   `return json.dumps([codigo.value for codigo in codigos], ensure_ascii=True)`

#### Análisis

**EQUIVALENTE (inobservable), justificado.** `json_de_codigos_de_motivo` recibe
`CodigoMotivo` y nada más, y los cuatro valores del `Enum`
—`codigo_obra_no_legible`, `numero_incidencia_no_legible`, `firma_no_humana`,
`observaciones_manuscritas`— son **ASCII puro**. `ensure_ascii` solo cambia la
salida cuando hay un carácter fuera de ASCII, así que sobre este dominio
cerrado las dos opciones producen exactamente la misma cadena: **ningún test
puede distinguirlas sin inventar un código de motivo que no existe**.

Se deja `ensure_ascii=False` a propósito y no se cambia: es lo que hacen
`json_de_motivos` y `json_de_avisos` del mismo módulo, donde sí importa
—ahí entran textos con tildes—, y tener dos criterios distintos en tres
funciones vecinas invita a copiar la equivocada.

Lo que mataría a este mutante es un `CodigoMotivo` con un carácter no ASCII. El
día que F-004 añada uno, este superviviente se convierte en un hueco real y hay
que volver aquí.

### 8. `services/postventa-api/infrastructure/persistencia/sentencias.py:448` [comparacion]

- Original: `"%s::jsonb" if columna == _COLUMNA_JSONB_APROBACION else "%s"`
- Mutado:   `"%s::jsonb" if columna != _COLUMNA_JSONB_APROBACION else "%s"`

#### Análisis

**HUECO REAL · tapado con un test nuevo** (`test_f026_solo_la_columna_de_motivos_se_declara_como_jsonb`,
en `tests/test_f026_persistencia.py`).

Por qué ningún test lo cazaba: el único test que miraba el `VALUES` contaba los
marcadores (`values.count("%s") == len(parametros)`), y con la comparación
invertida **siguen siendo siete**. Nadie comprobaba *cuál* de las columnas
llevaba el `::jsonb`.

Por qué no es cosmético, en las dos direcciones:

- sin `::jsonb` en `motivos_aprobados`, PostgreSQL rechaza el `INSERT`: no
  convierte `text` a `jsonb` por su cuenta;
- con `::jsonb` en las demás, el `oid` de quien aprueba y la huella se
  intentarían convertir a JSON y reventarían.

Las dos fallan en la **primera aprobación real** contra la base, no en la
suite, que es el peor sitio para enterarse. El test nuevo empareja columnas con
marcadores y exige que el conjunto de las que llevan `::jsonb` sea exactamente
`{"motivos_aprobados"}`.

Verificado a mano: aplicada la mutación, el test falla; revertida, pasa.

### 9. `services/postventa-api/infrastructure/sigrid/cliente.py:347` [booleano]

- Original: `if not respuesta.get("ok", False):`
- Mutado:   `if not respuesta.get("ok", True):`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 10. `services/postventa-api/infrastructure/sigrid/consultas.py:202` [logico]

- Original: `descripcion=str(descripcion or ""),`
- Mutado:   `descripcion=str(descripcion and ""),`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 11. `services/postventa-api/infrastructure/sigrid/consultas.py:207` [logico]

- Original: `estado_destino_res=str(destino_res or ""),`
- Mutado:   `estado_destino_res=str(destino_res and ""),`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 12. `services/postventa-api/infrastructure/sigrid/escrituras.py:217` [logico]

- Original: `f"{plan.motivo or 'sin motivo declarado'}"`
- Mutado:   `f"{plan.motivo and 'sin motivo declarado'}"`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 13. `services/postventa-api/interface_adapters/api/adjuntar.py:251` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

### 14. `services/postventa-api/interface_adapters/api/cerrar.py:219` [entero]

- Original: `confianza_observaciones=0,`
- Mutado:   `confianza_observaciones=1,`

#### Análisis

**FUERA DE F-026 · ya analizado en `progress/mutacion_F-012.md`.** Esta línea no
la escribe F-026: entra en el alcance porque la rama
`feature/F-026-aprobacion-humana` arranca de trabajo que todavía **no está
mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se calcula por diff
contra la base. Se deja constancia aquí y no se vuelve a analizar: repetir el
análisis en cada campaña posterior produce dos textos del mismo hecho que
divergen, y el bueno sería el de la feature dueña del código.

---

## Resumen del análisis (implementer del bloque 2, 2026-09-12)

**14 supervivientes, 14 analizados. Ninguna sección queda en `PENDIENTE`.**

| Veredicto | Cuántos | Cuáles |
|---|---|---|
| **Hueco real, tapado con test nuevo** | **3** | 1, 2, 8 |
| **Equivalente, justificado** | **1** | 7 |
| **Fuera de F-026**, ya analizado en `mutacion_F-012.md` | **10** | 3, 4, 5, 6, 9, 10, 11, 12, 13, 14 |

### Sobre los diez ajenos, para que no se lea como una excusa

El alcance de esta campaña son **6 382 líneas de 25 ficheros**, y F-026 ha
tocado seis de ellos. El resto entra porque la rama arranca de trabajo que
**todavía no está mergeado a `dev`** (F-009, F-012 y F-025), y el alcance se
calcula por diff contra la base. Los diez supervivientes ajenos están
analizados uno a uno en `progress/mutacion_F-012.md`, con el mismo nivel de
detalle: son en su mayoría valores por omisión de dataclasses reconstruidas que
ningún camino lee.

### Los tres tests nuevos

Se añaden al cerrar la campaña, y **matan a sus mutantes**: verificado
aplicando cada mutación a mano sobre el árbol limpio, ejecutando la suite y
revirtiendo.

```
FAILED tests/test_f026_aprobacion_dominio.py::test_f026_una_aprobacion_no_se_puede_modificar_despues_de_creada
FAILED tests/test_f026_aprobacion_dominio.py::test_f026_r8_un_no_apto_sin_motivos_no_es_aprobable
FAILED tests/test_f026_persistencia.py::test_f026_solo_la_columna_de_motivos_se_declara_como_jsonb
3 failed, 68 passed in 1.12s
```

Revertidas las mutaciones: `71 passed in 1.05s`.

### Advertencia sobre esta campaña

Se lanzó con la feature **a medias**: los bloques 3, 4, 4 bis y 5 no existen
todavía. **Hay que repetirla en T24**, al cerrar la feature, y entonces el
alcance incluirá el endpoint, las tres puertas y el front. Lo que esta campaña
demuestra es el estado de la persistencia y del dominio, que es lo que se ha
escrito hasta hoy.
