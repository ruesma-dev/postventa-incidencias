<!-- progress/impl_F-007.md -->
# F-007 · Front de carga y revisión — Informe de implementación

> Rama `feature/F-007-front`. Rigor **`estandar`**: fase RED en los requisitos
> centrales (T2, T3, T4, T7, T8), cobertura de líneas cambiadas ≥ 80 % y
> campaña de mutación con supervivientes analizados. **No** se exige fase RED
> en todo ni cero supervivientes.
>
> **Ni un dato real.** Todos los códigos, nombres y textos de este informe y de
> los tests están **inventados**. Ningún parte de `muestras/` se ha copiado al
> repositorio ni se ha impreso en ninguna salida.

## Decisiones del humano aplicadas (2026-08-20)

Las cinco decisiones abiertas de `design.md` §13 quedaron resueltas por el
humano el **2026-08-20**, antes de implementar. Se aplican tal cual:

| | Decisión del humano (2026-08-20) | Dónde se materializa |
|---|---|---|
| **D1** | **`dev_server.py` se PRUEBA** (opción O1 de `design.md` §9). Nada de excluirlo de la puerta de cobertura ni de moverlo a una carpeta excluida: se le escriben tests. Cierra a la vez los criterios de aceptación 5 y 6, no toca el arnés genérico y es lo único que reproduce en local el proxy de la Static Web App | T3 (`tests/test_f007_dev_server.py`), resumido en el `README.md` del front |
| **D2** | **El límite de concurrencia es 3 partes** (= 6 peticiones vivas), como razona `design.md` §5 | T10 (`js/config.js`, `CONCURRENCIA_PARTES: 3`) |
| **D3** | **Un campo corregido a mano vale confianza 100 y se marca como editado.** Lo ha mirado y escrito una persona: es el dato más fiable que hay y el semáforo tiene que poder pasar a verde. La marca permite distinguir después lo que escribió la persona de lo que dijo la IA | T8 (`js/pipeline.js`), T10/T11 (marca en pantalla) |
| **D4** | **La remesa NO se persiste en esta feature.** Recargar la pestaña pierde el trabajo de revisión, y se acepta para el piloto. **No se resuelve por la vía fácil**: prohibido `localStorage` e `IndexedDB`, porque los partes llevan DNI y observaciones de clientes (R28–R30). La solución está dada de alta como **F-019 · Endpoints de persistencia**, que es del servicio `postventa-api`, no del front | Nada que implementar aquí; se cita en el `README.md` del front y en `design.md` §10 |
| **D5** | **Navegador soportado: Edge/Chrome** (el selector de carpeta usa `webkitdirectory`, que Firefox no implementa igual) | T10/T12 (`README.md` del front) |

---

## T1 · Recuperar el esqueleto del front — HECHA

El esqueleto no se ha reescrito: ya estaba verificado. El líder lo recuperó en
el commit `440700c` («F-007: recuperado el esqueleto del front, que el merge de
dev habia borrado»), porque el merge de `dev` sobre esta rama lo había borrado
—`dev` lo tiene eliminado, se sacó de F-001—.

Los seis ficheros de `design.md` §1 están en el árbol:

```
services/postventa-front/index.html
services/postventa-front/css/styles.css
services/postventa-front/js/config.js
services/postventa-front/js/app.js
services/postventa-front/dev_server.py
services/postventa-front/staticwebapp.config.json
```

### Fase RED de R31 — el guardián que ya existía muerde

`bash harness/init.sh` con el esqueleto en el árbol y el servicio **sin
declarar**. Salida real, sin recortar la parte que importa:

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
...
    19 features, 13 abiertas, en curso: ['F-007'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 56 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
..............F
================================== FAILURES ===================================
_____________ test_f001_r4_cada_servicio_en_disco_esta_declarado ______________
tests\test_servicios_declarados.py:39: in test_f001_r4_cada_servicio_en_disco_esta_declarado
    assert relativa in declaradas, f"{relativa} existe pero no está declarado"
E   AssertionError: services/postventa-front existe pero no está declarado
E   assert 'services/postventa-front' in {'services/postventa-api'}
=========================== short test summary info ===========================
FAILED tests/test_servicios_declarados.py::test_f001_r4_cada_servicio_en_disco_esta_declarado
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 14 passed in 0.54s
[KO] pytest en rojo (¿pytest instalado en el venv?)
    1 servicio(s): api (python)
[OK] harness/servicios.json válido
[OK] servicio api (services/postventa-api): pytest en verde (caché: árbol sin cambios desde el último verde)
[KO] PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-007-front
----------------------------------------
2 comprobaciones fallidas. NO empieces a trabajar.
```

Eso es exactamente lo que demuestra el criterio de aceptación 5: **hasta hoy
nadie comprobaba el front**. El guardián existe desde F-001
(`tests/test_servicios_declarados.py`) y es la primera vez que puede morder,
porque hasta ahora la carpeta no estaba en el árbol.

**Los dos rojos son los esperados y ninguno más**:

1. `test_f001_r4_cada_servicio_en_disco_esta_declarado` → **fase RED de R31**,
   se cierra en T2.
2. `PUERTA COBERTURA: 0.0% de 114 líneas cambiadas cubiertas (0/114)` →
   **fase RED de R34**. Las 114 líneas son las de `dev_server.py`, que llega
   entero como fichero nuevo frente a `dev`. Es literalmente el problema que
   expulsó al front de F-001, y es lo que cierra T3 con D1/O1.
