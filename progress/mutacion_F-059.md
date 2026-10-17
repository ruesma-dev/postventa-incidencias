<!-- progress/mutacion_F-059.md -->
# F-059 · Campaña final de mutación (T22)

> **Campaña final por la opción B, decidida por el humano el 2026-10-17** (por escrito, al líder). La campaña de
> la herramienta del tramo entero (`python -m harness.mutacion --feature F-059 --base 2d2efd7 --timeout 1800`)
> **no se ha lanzado**: estimada en unas 17 h con 8 workers, más de las 12 h del encargo
> (`progress/impl_F-059.md`, Bloque 5, T22, con la estimación y las tres alternativas). La opción B la sustituye:
> la **comparación mutante a mutante** de la campaña entera con las cuatro campañas de bloque, y **a mano** los
> mutantes que ninguna de ellas midió.

## Alcance de la campaña entera (calculado, sin ejecutarla)

`alcance_de_feature("F-059", base="2d2efd7", rama="feature/F-059-volcado-sigrid-backend")` y `generar_mutantes`
de `harness/mutacion.py`, sobre `44fcd21`: **3822 líneas de producción en 19 ficheros y 203 mutantes**. Desde la
campaña del Bloque 4 (`9db9847`) no ha cambiado ningún fichero de producción
(`git diff --name-only 9db9847 HEAD -- services/` sin `tests`: vacío): el Bloque 5 solo toca scripts, Markdown y
tests.

## Totales

| Métrica | Valor |
|---|---|
| Mutantes de la campaña entera | 203 |
| Idénticos a uno medido por una campaña de bloque | **201** |
| Que ninguna campaña de bloque midió | **2**, ejecutados a mano: **2 muertos** |
| Supervivientes abiertos | **0** |
| Equivalentes nuevos que aceptar | 0 (los ya aceptados, V05d, A09 y los 13 de E-1, son de mutantes a mano, no de la herramienta) |

**Cómo se compara.** Un mutante es «el mismo» si coinciden el fichero, el **texto** de la línea (recortado), la
columna, el operador y el cambio (texto original y mutado); **sin** el número de línea, que se mueve en cuanto el
fichero respira (el mismo criterio que `clave_de_mutante` de `harness/mutacion.py`). Cada campaña de bloque se
regenera en su commit y con su base, con el mismo código de la herramienta; se casa como multiconjunto (cada
mutante de bloque cuenta una vez). Las cuatro, juntas, dan 202 mutantes; 201 casan con la campaña entera. El que
sobra es del Bloque 1, `domain/models/volcado.py` `if ensayo.actor_oid != actor_oid:`, una línea que ya no
existe: la quitó B-1 (a) en el Bloque 2 (la persona la compara la base). Los 2 de la campaña entera que no casan
están abajo.

| Campaña de bloque | Base | Commit medido | Mutantes | Resultado | Informe |
|---|---|---|---|---|---|
| Bloque 1 | `477e596` | `e0e93db` | 85 | 85 muertos | `progress/mutacion_F-059_bloque1.md` |
| Bloque 2 | `13f9f51` | `55f27f5` | 26 | 26 muertos | `progress/mutacion_F-059_bloque2.md` |
| Bloque 3 | `5c0a6d2` | `eb8d03b` | 25 | 25 muertos | `progress/mutacion_F-059_bloque3.md` |
| Bloque 4 | `560811b` | `9db9847` | 66 | 64 muertos; 16 y 24 muertos después por sus tests (`8b7790d`) | `progress/mutacion_F-059_bloque4.md` |

Los cuatro reverificaron cada muerto contra los tests de F-059 solos (`progress/impl_F-059.md`, T3, T9, T12 y T17).

## La tabla de equivalencias

Numeración y línea, las de la campaña entera sobre `44fcd21`; «medido en», la campaña de bloque y la línea que
tenía allí.

| # | Fichero:línea | Tipo | Cambio | Medido en | Veredicto |
|---|---|---|---|---|---|
| 1 | `application/pipelines/volcado.py:160` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:160`) | muerto en la campaña |
| 2 | `application/pipelines/volcado.py:168` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:168`) | muerto en la campaña |
| 3 | `application/pipelines/volcado.py:177` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:177`) | muerto en la campaña |
| 4 | `application/pipelines/volcado.py:187` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:187`) | muerto en la campaña |
| 5 | `application/pipelines/volcado.py:195` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:195`) | muerto en la campaña |
| 6 | `application/pipelines/volcado.py:207` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:207`) | muerto en la campaña |
| 7 | `application/pipelines/volcado.py:220` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:220`) | muerto en la campaña |
| 8 | `application/pipelines/volcado.py:228` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 4 (`application/pipelines/volcado.py:228`) | muerto en la campaña |
| 9 | `application/pipelines/volcado.py:256` | comparacion | `if len(situaciones) > TOPE_LECTURA_OBRA:` → `if len(situaciones) >= TOPE_LECTURA_OBRA:` | Bloque 4 (`application/pipelines/volcado.py:256`) | muerto en la campaña |
| 10 | `application/pipelines/volcado.py:267` | entero | `aprobadas=sum(1 for _, e in estados if e is EstadoRevision.APROBADA),` → `aprobadas=sum(2 for _, e in estados if e is EstadoRevision.APROBADA),` | Bloque 4 (`application/pipelines/volcado.py:267`) | muerto en la campaña |
| 11 | `application/pipelines/volcado.py:268` | entero | `en_duda=sum(1 for _, e in estados if e is EstadoRevision.EN_DUDA),` → `en_duda=sum(2 for _, e in estados if e is EstadoRevision.EN_DUDA),` | Bloque 4 (`application/pipelines/volcado.py:268`) | muerto en la campaña |
| 12 | `application/pipelines/volcado.py:269` | entero | `volcadas=sum(1 for _, e in estados if e is EstadoRevision.VOLCADA),` → `volcadas=sum(2 for _, e in estados if e is EstadoRevision.VOLCADA),` | Bloque 4 (`application/pipelines/volcado.py:269`) | muerto en la campaña |
| 13 | `application/pipelines/volcado.py:300` | not | `if not seleccion.mandadas:` → `if seleccion.mandadas:` | Bloque 4 (`application/pipelines/volcado.py:300`) | muerto en la campaña |
| 14 | `application/pipelines/volcado.py:319` | booleano | `partes, obra=obra, usu=login, commit=False, base=ajustes_volcado.base_datos` → `partes, obra=obra, usu=login, commit=True, base=ajustes_volcado.base_datos` | Bloque 4 (`application/pipelines/volcado.py:319`) | muerto en la campaña |
| 15 | `application/pipelines/volcado.py:338` | aritmetico | `caduca_at_utc=ahora + CADUCIDAD_DEL_ENSAYO,` → `caduca_at_utc=ahora - CADUCIDAD_DEL_ENSAYO,` | Bloque 4 (`application/pipelines/volcado.py:338`) | muerto en la campaña |
| 16 | `application/pipelines/volcado.py:339` | booleano | `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),` → `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=False)),` | Bloque 4 (`application/pipelines/volcado.py:339`) | superviviente en la campaña; muerto después por su test (mutantes 16 y 24) |
| 17 | `application/pipelines/volcado.py:440` | not | `if not seleccion.mandadas:` → `if seleccion.mandadas:` | Bloque 4 (`application/pipelines/volcado.py:440`) | muerto en la campaña |
| 18 | `application/pipelines/volcado.py:458` | booleano | `partes, obra=obra, usu=login, commit=True, base=ajustes_volcado.base_datos` → `partes, obra=obra, usu=login, commit=False, base=ajustes_volcado.base_datos` | Bloque 4 (`application/pipelines/volcado.py:458`) | muerto en la campaña |
| 19 | `application/pipelines/volcado.py:479` | booleano | `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=True)),` → `partes=tuple(ParteMandado(p, r) for p, r in zip(partes, resultados, strict=False)),` | Bloque 4 (`application/pipelines/volcado.py:479`) | superviviente en la campaña; muerto después por su test (mutantes 16 y 24) |
| 20 | `application/pipelines/volcado.py:531` | comparacion | `if candidata.revision_id != evento.revision_id:` → `if candidata.revision_id == evento.revision_id:` | Bloque 4 (`application/pipelines/volcado.py:531`) | muerto en la campaña |
| 21 | `application/pipelines/volcado.py:533` | not | `if not huella_intacta(candidata):` → `if huella_intacta(candidata):` | Bloque 4 (`application/pipelines/volcado.py:533`) | muerto en la campaña |
| 22 | `application/pipelines/volcado.py:662` | not | `if not 1 <= cuantas <= ajustes.partes_por_llamada:` → `if 1 <= cuantas <= ajustes.partes_por_llamada:` | Bloque 4 (`application/pipelines/volcado.py:662`) | muerto en la campaña |
| 23 | `application/pipelines/volcado.py:662` | entero | `if not 1 <= cuantas <= ajustes.partes_por_llamada:` → `if not 2 <= cuantas <= ajustes.partes_por_llamada:` | Bloque 4 (`application/pipelines/volcado.py:662`) | muerto en la campaña |
| 24 | `application/pipelines/volcado.py:662` | comparacion | `if not 1 <= cuantas <= ajustes.partes_por_llamada:` → `if not 1 < cuantas <= ajustes.partes_por_llamada:` | Bloque 4 (`application/pipelines/volcado.py:662`) | muerto en la campaña |
| 25 | `application/pipelines/volcado.py:662` | comparacion | `if not 1 <= cuantas <= ajustes.partes_por_llamada:` → `if not 1 <= cuantas < ajustes.partes_por_llamada:` | Bloque 4 (`application/pipelines/volcado.py:662`) | muerto en la campaña |
| 26 | `config/settings.py:527` | booleano | `default=False,` → `default=True,` | Bloque 3 (`config/settings.py:527`) | muerto en la campaña |
| 27 | `config/settings.py:538` | entero | `default=5,` → `default=6,` | Bloque 3 (`config/settings.py:538`) | muerto en la campaña |
| 28 | `domain/models/revision.py:950` | logico | `and estado_de(situacion) in _CANDIDATOS` → `or estado_de(situacion) in _CANDIDATOS` | Bloque 1 (`domain/models/revision.py:950`) | muerto en la campaña |
| 29 | `domain/models/revision.py:1072` | logico | `if filtro is FiltroEstado.ACTIVAS and fila.estado in _FUERA_DE_ACTIVAS:` → `if filtro is FiltroEstado.ACTIVAS or fila.estado in _FUERA_DE_ACTIVAS:` | Bloque 1 (`domain/models/revision.py:1072`) | muerto en la campaña |
| 30 | `domain/models/situacion_volcado.py:66` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/situacion_volcado.py:66`) | muerto en la campaña |
| 31 | `domain/models/situacion_volcado.py:77` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/situacion_volcado.py:77`) | muerto en la campaña |
| 32 | `domain/models/situacion_volcado.py:88` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/situacion_volcado.py:88`) | muerto en la campaña |
| 33 | `domain/models/situacion_volcado.py:103` | logico | `and self.ultimo is not None` → `or self.ultimo is not None` | Bloque 1 (`domain/models/situacion_volcado.py:103`) | muerto en la campaña |
| 34 | `domain/models/situacion_volcado.py:104` | logico | `and self.ultimo.estado in ESTADOS_CON_PARTE` → `or self.ultimo.estado in ESTADOS_CON_PARTE` | Bloque 1 (`domain/models/situacion_volcado.py:104`) | muerto en la campaña |
| 35 | `domain/models/situacion_volcado.py:125` | logico | `if situacion.ultimo is not None and situacion.ultimo.estado in ESTADOS_EN_DUDA:` → `if situacion.ultimo is not None or situacion.ultimo.estado in ESTADOS_EN_DUDA:` | Bloque 1 (`domain/models/situacion_volcado.py:125`) | muerto en la campaña |
| 36 | `domain/models/volcado.py:115` | entero | `FORMA_ESCRITA = 1` → `FORMA_ESCRITA = 2` | Bloque 1 (`domain/models/volcado.py:115`) | muerto en la campaña |
| 37 | `domain/models/volcado.py:117` | booleano | `CAUSANTE = False` → `CAUSANTE = True` | Bloque 1 (`domain/models/volcado.py:117`) | muerto en la campaña |
| 38 | `domain/models/volcado.py:119` | entero | `CADUCIDAD_DEL_ENSAYO = timedelta(minutes=30)` → `CADUCIDAD_DEL_ENSAYO = timedelta(minutes=31)` | Bloque 1 (`domain/models/volcado.py:119`) | muerto en la campaña |
| 39 | `domain/models/volcado.py:121` | entero | `MAX_PARTES_POR_LLAMADA = 50` → `MAX_PARTES_POR_LLAMADA = 51` | Bloque 1 (`domain/models/volcado.py:121`) | muerto en la campaña |
| 40 | `domain/models/volcado.py:221` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:221`) | muerto en la campaña |
| 41 | `domain/models/volcado.py:230` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:230`) | muerto en la campaña |
| 42 | `domain/models/volcado.py:248` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:248`) | muerto en la campaña |
| 43 | `domain/models/volcado.py:261` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:261`) | muerto en la campaña |
| 44 | `domain/models/volcado.py:271` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:271`) | muerto en la campaña |
| 45 | `domain/models/volcado.py:289` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:283`) | muerto en la campaña |
| 46 | `domain/models/volcado.py:297` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:291`) | muerto en la campaña |
| 47 | `domain/models/volcado.py:308` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:302`) | muerto en la campaña |
| 48 | `domain/models/volcado.py:318` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:312`) | muerto en la campaña |
| 49 | `domain/models/volcado.py:326` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 1 (`domain/models/volcado.py:320`) | muerto en la campaña |
| 50 | `domain/models/volcado.py:350` | not | `if not isinstance(incidencia_id, UUID):` → `if isinstance(incidencia_id, UUID):` | Bloque 1 (`domain/models/volcado.py:344`) | muerto en la campaña |
| 51 | `domain/models/volcado.py:352` | aritmetico | `return PREFIJO_REFERENCIA + str(incidencia_id)` → `return PREFIJO_REFERENCIA - str(incidencia_id)` | Bloque 1 (`domain/models/volcado.py:346`) | muerto en la campaña |
| 52 | `domain/models/volcado.py:364` | logico | `if texto is None or not texto.strip():` → `if texto is None and not texto.strip():` | **ninguno** | a mano (tabla siguiente): muerto |
| 53 | `domain/models/volcado.py:364` | not | `if texto is None or not texto.strip():` → `if texto is None or texto.strip():` | **ninguno** | a mano (tabla siguiente): muerto |
| 54 | `domain/models/volcado.py:441` | not | `if not isinstance(commit, bool):` → `if isinstance(commit, bool):` | Bloque 1 (`domain/models/volcado.py:420`) | muerto en la campaña |
| 55 | `domain/models/volcado.py:443` | not | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` → `if 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` | Bloque 1 (`domain/models/volcado.py:422`) | muerto en la campaña |
| 56 | `domain/models/volcado.py:443` | entero | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` → `if not 2 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` | Bloque 1 (`domain/models/volcado.py:422`) | muerto en la campaña |
| 57 | `domain/models/volcado.py:443` | comparacion | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` → `if not 1 < len(partes) <= MAX_PARTES_POR_LLAMADA:` | Bloque 1 (`domain/models/volcado.py:422`) | muerto en la campaña |
| 58 | `domain/models/volcado.py:443` | comparacion | `if not 1 <= len(partes) <= MAX_PARTES_POR_LLAMADA:` → `if not 1 <= len(partes) < MAX_PARTES_POR_LLAMADA:` | Bloque 1 (`domain/models/volcado.py:422`) | muerto en la campaña |
| 59 | `domain/models/volcado.py:448` | comparacion | `if len(set(referencias)) != len(referencias):` → `if len(set(referencias)) == len(referencias):` | Bloque 1 (`domain/models/volcado.py:427`) | muerto en la campaña |
| 60 | `domain/models/volcado.py:461` | comparacion | `return huella_de_valores(candidata.valores) == candidata.huella` → `return huella_de_valores(candidata.valores) != candidata.huella` | Bloque 1 (`domain/models/volcado.py:440`) | muerto en la campaña |
| 61 | `domain/models/volcado.py:470` | comparacion | `if len(set(incidencias)) != len(incidencias):` → `if len(set(incidencias)) == len(incidencias):` | Bloque 1 (`domain/models/volcado.py:449`) | muerto en la campaña |
| 62 | `domain/models/volcado.py:502` | comparacion | `elif situacion.obra_codigo != obra:` → `elif situacion.obra_codigo == obra:` | Bloque 1 (`domain/models/volcado.py:481`) | muerto en la campaña |
| 63 | `domain/models/volcado.py:504` | logico | `elif situacion.volcado is not None and situacion.volcado.volcada is not None:` → `elif situacion.volcado is not None or situacion.volcado.volcada is not None:` | Bloque 1 (`domain/models/volcado.py:483`) | muerto en la campaña |
| 64 | `domain/models/volcado.py:512` | logico | `elif candidata is None or not es_candidata(situacion):` → `elif candidata is None and not es_candidata(situacion):` | Bloque 1 (`domain/models/volcado.py:491`) | muerto en la campaña |
| 65 | `domain/models/volcado.py:512` | not | `elif candidata is None or not es_candidata(situacion):` → `elif candidata is None or es_candidata(situacion):` | Bloque 1 (`domain/models/volcado.py:491`) | muerto en la campaña |
| 66 | `domain/models/volcado.py:514` | not | `elif not huella_intacta(candidata):` → `elif huella_intacta(candidata):` | Bloque 1 (`domain/models/volcado.py:493`) | muerto en la campaña |
| 67 | `domain/models/volcado.py:537` | comparacion | `if ensayo.obra_codigo != obra:` → `if ensayo.obra_codigo == obra:` | Bloque 1 (`domain/models/volcado.py:515`) | muerto en la campaña |
| 68 | `domain/models/volcado.py:541` | not | `if not ensayo.de_la_persona:` → `if ensayo.de_la_persona:` | Bloque 2 (`domain/models/volcado.py:541`) | muerto en la campaña |
| 69 | `domain/models/volcado.py:546` | aritmetico | `if ahora - ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO:` → `if ahora + ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO:` | Bloque 1 (`domain/models/volcado.py:524`) | muerto en la campaña |
| 70 | `domain/models/volcado.py:546` | comparacion | `if ahora - ensayo.at_utc >= CADUCIDAD_DEL_ENSAYO:` → `if ahora - ensayo.at_utc > CADUCIDAD_DEL_ENSAYO:` | Bloque 1 (`domain/models/volcado.py:524`) | muerto en la campaña |
| 71 | `domain/models/volcado.py:560` | logico | `if evento is None or evento.estado is not EstadoEvento.PREVISTO:` → `if evento is None and evento.estado is not EstadoEvento.PREVISTO:` | Bloque 1 (`domain/models/volcado.py:538`) | muerto en la campaña |
| 72 | `domain/models/volcado.py:562` | comparacion | `if evento.revision_id != pedida.revision_id:` → `if evento.revision_id == pedida.revision_id:` | Bloque 1 (`domain/models/volcado.py:540`) | muerto en la campaña |
| 73 | `domain/models/volcado.py:570` | comparacion | `actual.revision_id != evento.revision_id` → `actual.revision_id == evento.revision_id` | Bloque 1 (`domain/models/volcado.py:548`) | muerto en la campaña |
| 74 | `domain/models/volcado.py:571` | logico | `or actual.accion is not AccionRevision.APROBAR` → `and actual.accion is not AccionRevision.APROBAR` | Bloque 1 (`domain/models/volcado.py:549`) | muerto en la campaña |
| 75 | `domain/models/volcado.py:574` | comparacion | `if actual.huella != evento.huella:` → `if actual.huella == evento.huella:` | Bloque 1 (`domain/models/volcado.py:552`) | muerto en la campaña |
| 76 | `domain/models/volcado.py:605` | entero | `excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[1]))` → `excluidas.append(Excluida(pedida.incidencia_id, motivo[1], motivo[1]))` | Bloque 1 (`domain/models/volcado.py:583`) | muerto en la campaña |
| 77 | `domain/models/volcado.py:605` | entero | `excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[1]))` → `excluidas.append(Excluida(pedida.incidencia_id, motivo[0], motivo[2]))` | Bloque 1 (`domain/models/volcado.py:583`) | muerto en la campaña |
| 78 | `domain/models/volcado.py:617` | logico | `return isinstance(valor, int) and not isinstance(valor, bool)` → `return isinstance(valor, int) or not isinstance(valor, bool)` | Bloque 1 (`domain/models/volcado.py:595`) | muerto en la campaña |
| 79 | `domain/models/volcado.py:617` | not | `return isinstance(valor, int) and not isinstance(valor, bool)` → `return isinstance(valor, int) and isinstance(valor, bool)` | Bloque 1 (`domain/models/volcado.py:595`) | muerto en la campaña |
| 80 | `domain/models/volcado.py:646` | logico | `or elemento.get("referencia_externa") != parte.referencia_externa` → `and elemento.get("referencia_externa") != parte.referencia_externa` | Bloque 1 (`domain/models/volcado.py:624`) | muerto en la campaña |
| 81 | `domain/models/volcado.py:646` | comparacion | `or elemento.get("referencia_externa") != parte.referencia_externa` → `or elemento.get("referencia_externa") == parte.referencia_externa` | Bloque 1 (`domain/models/volcado.py:624`) | muerto en la campaña |
| 82 | `domain/models/volcado.py:650` | not | `if not isinstance(crudo, str) or crudo not in {e.value for e in validos}:` → `if isinstance(crudo, str) or crudo not in {e.value for e in validos}:` | Bloque 1 (`domain/models/volcado.py:628`) | muerto en la campaña |
| 83 | `domain/models/volcado.py:650` | logico | `if not isinstance(crudo, str) or crudo not in {e.value for e in validos}:` → `if not isinstance(crudo, str) and crudo not in {e.value for e in validos}:` | Bloque 1 (`domain/models/volcado.py:628`) | muerto en la campaña |
| 84 | `domain/models/volcado.py:655` | not | `if not _es_entero(ide) or ide < 1:` → `if _es_entero(ide) or ide < 1:` | Bloque 1 (`domain/models/volcado.py:633`) | muerto en la campaña |
| 85 | `domain/models/volcado.py:655` | logico | `if not _es_entero(ide) or ide < 1:` → `if not _es_entero(ide) and ide < 1:` | Bloque 1 (`domain/models/volcado.py:633`) | muerto en la campaña |
| 86 | `domain/models/volcado.py:655` | comparacion | `if not _es_entero(ide) or ide < 1:` → `if not _es_entero(ide) or ide <= 1:` | Bloque 1 (`domain/models/volcado.py:633`) | muerto en la campaña |
| 87 | `domain/models/volcado.py:655` | entero | `if not _es_entero(ide) or ide < 1:` → `if not _es_entero(ide) or ide < 2:` | Bloque 1 (`domain/models/volcado.py:633`) | muerto en la campaña |
| 88 | `domain/models/volcado.py:657` | not | `if not isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None:` → `if isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None:` | Bloque 1 (`domain/models/volcado.py:635`) | muerto en la campaña |
| 89 | `domain/models/volcado.py:657` | logico | `if not isinstance(cod, str) or PATRON_COD_PARTE.fullmatch(cod) is None:` → `if not isinstance(cod, str) and PATRON_COD_PARTE.fullmatch(cod) is None:` | Bloque 1 (`domain/models/volcado.py:635`) | muerto en la campaña |
| 90 | `domain/models/volcado.py:666` | not | `if not isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` → `if isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` | Bloque 1 (`domain/models/volcado.py:644`) | muerto en la campaña |
| 91 | `domain/models/volcado.py:666` | logico | `if not isinstance(codigo, str) or PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` → `if not isinstance(codigo, str) and PATRON_CODIGO_MOTIVO.fullmatch(codigo) is None:` | Bloque 1 (`domain/models/volcado.py:644`) | muerto en la campaña |
| 92 | `domain/models/volcado.py:693` | not | `if not isinstance(datos, Mapping):` → `if isinstance(datos, Mapping):` | Bloque 1 (`domain/models/volcado.py:671`) | muerto en la campaña |
| 93 | `domain/models/volcado.py:696` | not | `if not isinstance(partes, list) or not isinstance(dry_run, bool):` → `if isinstance(partes, list) or not isinstance(dry_run, bool):` | Bloque 1 (`domain/models/volcado.py:674`) | muerto en la campaña |
| 94 | `domain/models/volcado.py:696` | logico | `if not isinstance(partes, list) or not isinstance(dry_run, bool):` → `if not isinstance(partes, list) and not isinstance(dry_run, bool):` | Bloque 1 (`domain/models/volcado.py:674`) | muerto en la campaña |
| 95 | `domain/models/volcado.py:696` | not | `if not isinstance(partes, list) or not isinstance(dry_run, bool):` → `if not isinstance(partes, list) or isinstance(dry_run, bool):` | Bloque 1 (`domain/models/volcado.py:674`) | muerto en la campaña |
| 96 | `domain/models/volcado.py:698` | comparacion | `if dry_run == (modo is ModoVolcado.VOLCADO):` → `if dry_run != (modo is ModoVolcado.VOLCADO):` | Bloque 1 (`domain/models/volcado.py:676`) | muerto en la campaña |
| 97 | `domain/models/volcado.py:702` | not | `if not isinstance(elemento, Mapping):` → `if isinstance(elemento, Mapping):` | Bloque 1 (`domain/models/volcado.py:680`) | muerto en la campaña |
| 98 | `domain/models/volcado.py:705` | not | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if _es_entero(indice) or not 0 <= indice < len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 99 | `domain/models/volcado.py:705` | logico | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if not _es_entero(indice) and not 0 <= indice < len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 100 | `domain/models/volcado.py:705` | not | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if not _es_entero(indice) or 0 <= indice < len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 101 | `domain/models/volcado.py:705` | entero | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if not _es_entero(indice) or not 1 <= indice < len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 102 | `domain/models/volcado.py:705` | comparacion | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if not _es_entero(indice) or not 0 < indice < len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 103 | `domain/models/volcado.py:705` | comparacion | `if not _es_entero(indice) or not 0 <= indice < len(mandados):` → `if not _es_entero(indice) or not 0 <= indice <= len(mandados):` | Bloque 1 (`domain/models/volcado.py:683`) | muerto en la campaña |
| 104 | `domain/models/volcado.py:748` | logico | `if r.estado is not EstadoEvento.CREADO or anterior is None:` → `if r.estado is not EstadoEvento.CREADO and anterior is None:` | Bloque 1 (`domain/models/volcado.py:726`) | muerto en la campaña |
| 105 | `domain/models/volcado.py:751` | logico | `if parte is not None and parte.sigrid_ide != r.sigrid_ide:` → `if parte is not None or parte.sigrid_ide != r.sigrid_ide:` | Bloque 1 (`domain/models/volcado.py:729`) | muerto en la campaña |
| 106 | `domain/models/volcado.py:751` | comparacion | `if parte is not None and parte.sigrid_ide != r.sigrid_ide:` → `if parte is not None and parte.sigrid_ide == r.sigrid_ide:` | Bloque 1 (`domain/models/volcado.py:729`) | muerto en la campaña |
| 107 | `domain/models/volcado.py:771` | not | `if not isinstance(codigo, str):` → `if isinstance(codigo, str):` | Bloque 1 (`domain/models/volcado.py:749`) | muerto en la campaña |
| 108 | `domain/models/volcado.py:797` | entero | `clave: sum(1 for r in lista if r.estado is estado) for clave, estado in claves` → `clave: sum(2 for r in lista if r.estado is estado) for clave, estado in claves` | Bloque 1 (`domain/models/volcado.py:775`) | muerto en la campaña |
| 109 | `domain/models/volcado.py:810` | not | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 110 | `domain/models/volcado.py:810` | logico | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if not _es_entero(n) and not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 111 | `domain/models/volcado.py:810` | not | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if not _es_entero(n) or 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 112 | `domain/models/volcado.py:810` | entero | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if not _es_entero(n) or not 2 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 113 | `domain/models/volcado.py:810` | comparacion | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if not _es_entero(n) or not 1 < n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 114 | `domain/models/volcado.py:810` | comparacion | `if not _es_entero(n) or not 1 <= n <= MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` → `if not _es_entero(n) or not 1 <= n < MAX_PARTES_POR_LLAMADA:  # type: ignore[operator]` | Bloque 1 (`domain/models/volcado.py:788`) | muerto en la campaña |
| 115 | `domain/ports/volcado.py:79` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 3 (`domain/ports/volcado.py:79`) | muerto en la campaña |
| 116 | `domain/ports/volcado.py:93` | not | `if not isinstance(self.tipo, FamiliaDeRespuesta):` → `if isinstance(self.tipo, FamiliaDeRespuesta):` | Bloque 3 (`domain/ports/volcado.py:93`) | muerto en la campaña |
| 117 | `domain/ports/volcado.py:95` | comparacion | `if (self.datos is not None) != (self.tipo is FamiliaDeRespuesta.OK):` → `if (self.datos is not None) == (self.tipo is FamiliaDeRespuesta.OK):` | Bloque 3 (`domain/ports/volcado.py:95`) | muerto en la campaña |
| 118 | `domain/ports/volcado.py:97` | logico | `if self.codigo is not None and self.tipo is not FamiliaDeRespuesta.LOTE_400:` → `if self.codigo is not None or self.tipo is not FamiliaDeRespuesta.LOTE_400:` | Bloque 3 (`domain/ports/volcado.py:97`) | muerto en la campaña |
| 119 | `function_app.py:1873` | entero | `CuerpoDeVolcadoInvalido: 400,` → `CuerpoDeVolcadoInvalido: 401,` | Bloque 4 (`function_app.py:1873`) | muerto en la campaña |
| 120 | `function_app.py:1874` | entero | `VolcadoDeshabilitado: 503,` → `VolcadoDeshabilitado: 504,` | Bloque 4 (`function_app.py:1874`) | muerto en la campaña |
| 121 | `function_app.py:1875` | entero | `ConfiguracionDeVolcadoInvalida: 503,` → `ConfiguracionDeVolcadoInvalida: 504,` | Bloque 4 (`function_app.py:1875`) | muerto en la campaña |
| 122 | `function_app.py:1876` | entero | `ConfiguracionSigridIncompleta: 503,` → `ConfiguracionSigridIncompleta: 504,` | Bloque 4 (`function_app.py:1876`) | muerto en la campaña |
| 123 | `function_app.py:1877` | entero | `ConfiguracionPgIncompleta: 503,` → `ConfiguracionPgIncompleta: 504,` | Bloque 4 (`function_app.py:1877`) | muerto en la campaña |
| 124 | `function_app.py:1878` | entero | `PersistenciaNoDisponible: 503,` → `PersistenciaNoDisponible: 504,` | Bloque 4 (`function_app.py:1878`) | muerto en la campaña |
| 125 | `function_app.py:1879` | entero | `EnsayoNoValido: 409,` → `EnsayoNoValido: 410,` | Bloque 4 (`function_app.py:1879`) | muerto en la campaña |
| 126 | `function_app.py:1880` | entero | `EnsayoSinRespuesta: 502,` → `EnsayoSinRespuesta: 503,` | Bloque 4 (`function_app.py:1880`) | muerto en la campaña |
| 127 | `function_app.py:1881` | entero | `VolcadoSinRespuesta: 502,` → `VolcadoSinRespuesta: 503,` | Bloque 4 (`function_app.py:1881`) | muerto en la campaña |
| 128 | `function_app.py:1882` | entero | `VolcadoSinTraza: 500,` → `VolcadoSinTraza: 501,` | Bloque 4 (`function_app.py:1882`) | muerto en la campaña |
| 129 | `function_app.py:1883` | entero | `UsuarioSigridNoMapeado: 409,` → `UsuarioSigridNoMapeado: 410,` | Bloque 4 (`function_app.py:1883`) | muerto en la campaña |
| 130 | `function_app.py:1884` | entero | `UsuarioSigridInexistente: 409,` → `UsuarioSigridInexistente: 410,` | Bloque 4 (`function_app.py:1884`) | muerto en la campaña |
| 131 | `function_app.py:1885` | entero | `BandejaDemasiadoGrande: 409,` → `BandejaDemasiadoGrande: 410,` | Bloque 4 (`function_app.py:1885`) | muerto en la campaña |
| 132 | `function_app.py:1936` | entero | `400,` → `401,` | Bloque 4 (`function_app.py:1936`) | muerto en la campaña |
| 133 | `function_app.py:1955` | entero | `return _json(cuerpo, 200)` → `return _json(cuerpo, 201)` | Bloque 4 (`function_app.py:1955`) | muerto en la campaña |
| 134 | `function_app.py:1984` | entero | `return _json(cuerpo, 200)` → `return _json(cuerpo, 201)` | Bloque 4 (`function_app.py:1984`) | muerto en la campaña |
| 135 | `function_app.py:2014` | entero | `return _json(cuerpo, 200)` → `return _json(cuerpo, 201)` | Bloque 4 (`function_app.py:2014`) | muerto en la campaña |
| 136 | `infrastructure/persistencia/repositorio_revision_pg.py:236` | not | `if not filas:` → `if filas:` | Bloque 2 (`infrastructure/persistencia/repositorio_revision_pg.py:236`) | muerto en la campaña |
| 137 | `infrastructure/persistencia/repositorio_revision_pg.py:238` | entero | `_, bloqueada = sentencias_volcado.fila_a_bloqueada(filas[0])` → `_, bloqueada = sentencias_volcado.fila_a_bloqueada(filas[1])` | Bloque 2 (`infrastructure/persistencia/repositorio_revision_pg.py:238`) | muerto en la campaña |
| 138 | `infrastructure/persistencia/repositorio_volcado_pg.py:85` | not | `if not incidencias:` → `if incidencias:` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:85`) | muerto en la campaña |
| 139 | `infrastructure/persistencia/repositorio_volcado_pg.py:156` | not | `if not pedidas:` → `if pedidas:` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:156`) | muerto en la campaña |
| 140 | `infrastructure/persistencia/repositorio_volcado_pg.py:251` | not | `if not partes or len(partes) != len(resultados):` → `if partes or len(partes) != len(resultados):` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:251`) | muerto en la campaña |
| 141 | `infrastructure/persistencia/repositorio_volcado_pg.py:251` | logico | `if not partes or len(partes) != len(resultados):` → `if not partes and len(partes) != len(resultados):` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:251`) | muerto en la campaña |
| 142 | `infrastructure/persistencia/repositorio_volcado_pg.py:251` | comparacion | `if not partes or len(partes) != len(resultados):` → `if not partes or len(partes) == len(resultados):` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:251`) | muerto en la campaña |
| 143 | `infrastructure/persistencia/repositorio_volcado_pg.py:256` | comparacion | `if (parte.incidencia_id, parte.referencia_externa) != (` → `if (parte.incidencia_id, parte.referencia_externa) == (` | Bloque 2 (`infrastructure/persistencia/repositorio_volcado_pg.py:256`) | muerto en la campaña |
| 144 | `infrastructure/persistencia/sentencias_revision.py:337` | aritmetico | `fin_ultima_original = fin_original + _ANCHO_REVISION` → `fin_ultima_original = fin_original - _ANCHO_REVISION` | Bloque 2 (`infrastructure/persistencia/sentencias_revision.py:337`) | muerto en la campaña |
| 145 | `infrastructure/persistencia/sentencias_revision.py:346` | comparacion | `volcado=None if volcado == _SIN_EVENTOS else volcado,` → `volcado=None if volcado != _SIN_EVENTOS else volcado,` | Bloque 2 (`infrastructure/persistencia/sentencias_revision.py:346`) | muerto en la campaña |
| 146 | `infrastructure/persistencia/sentencias_volcado.py:118` | booleano | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:118`) | muerto en la campaña |
| 147 | `infrastructure/persistencia/sentencias_volcado.py:217` | aritmetico | `f"VALUES ({', '.join(['%s'] * len(COLUMNAS_INSERT))})"` → `f"VALUES ({', '.join(['%s'] // len(COLUMNAS_INSERT))})"` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:217`) | muerto en la campaña |
| 148 | `infrastructure/persistencia/sentencias_volcado.py:290` | not | `if not filas:` → `if filas:` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:290`) | muerto en la campaña |
| 149 | `infrastructure/persistencia/sentencias_volcado.py:292` | entero | `if len({(fila[0], fila[1]) for fila in filas}) != 1:` → `if len({(fila[1], fila[1]) for fila in filas}) != 1:` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:292`) | muerto en la campaña |
| 150 | `infrastructure/persistencia/sentencias_volcado.py:292` | entero | `if len({(fila[0], fila[1]) for fila in filas}) != 1:` → `if len({(fila[0], fila[2]) for fila in filas}) != 1:` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:292`) | muerto en la campaña |
| 151 | `infrastructure/persistencia/sentencias_volcado.py:292` | comparacion | `if len({(fila[0], fila[1]) for fila in filas}) != 1:` → `if len({(fila[0], fila[1]) for fila in filas}) == 1:` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:292`) | muerto en la campaña |
| 152 | `infrastructure/persistencia/sentencias_volcado.py:292` | entero | `if len({(fila[0], fila[1]) for fila in filas}) != 1:` → `if len({(fila[0], fila[1]) for fila in filas}) != 2:` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:292`) | muerto en la campaña |
| 153 | `infrastructure/persistencia/sentencias_volcado.py:294` | entero | `primera = filas[0]` → `primera = filas[1]` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:294`) | muerto en la campaña |
| 154 | `infrastructure/persistencia/sentencias_volcado.py:297` | entero | `obra_codigo=primera[0],` → `obra_codigo=primera[1],` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:297`) | muerto en la campaña |
| 155 | `infrastructure/persistencia/sentencias_volcado.py:298` | entero | `de_la_persona=all(fila[2] for fila in filas),` → `de_la_persona=all(fila[3] for fila in filas),` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:298`) | muerto en la campaña |
| 156 | `infrastructure/persistencia/sentencias_volcado.py:299` | entero | `at_utc=_con_zona(primera[1]),` → `at_utc=_con_zona(primera[2]),` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:299`) | muerto en la campaña |
| 157 | `infrastructure/persistencia/sentencias_volcado.py:302` | entero | `incidencia_id=como_uuid(fila[3]),` → `incidencia_id=como_uuid(fila[4]),` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:302`) | muerto en la campaña |
| 158 | `infrastructure/persistencia/sentencias_volcado.py:303` | entero | `revision_id=fila[4],` → `revision_id=fila[5],` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:303`) | muerto en la campaña |
| 159 | `infrastructure/persistencia/sentencias_volcado.py:304` | entero | `huella=fila[5],` → `huella=fila[6],` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:304`) | muerto en la campaña |
| 160 | `infrastructure/persistencia/sentencias_volcado.py:305` | entero | `estado=EstadoEvento(fila[6]),` → `estado=EstadoEvento(fila[7]),` | Bloque 2 (`infrastructure/persistencia/sentencias_volcado.py:305`) | muerto en la campaña |
| 161 | `infrastructure/sigrid/fabrica.py:310` | booleano | `return _adaptador_de_volcado(ajustes, escritura_habilitada=False)` → `return _adaptador_de_volcado(ajustes, escritura_habilitada=True)` | Bloque 3 (`infrastructure/sigrid/fabrica.py:310`) | muerto en la campaña |
| 162 | `infrastructure/sigrid/fabrica.py:323` | not | `if not ajustes.volcado_habilitado:` → `if ajustes.volcado_habilitado:` | Bloque 3 (`infrastructure/sigrid/fabrica.py:323`) | muerto en la campaña |
| 163 | `infrastructure/sigrid/fabrica.py:333` | booleano | `return _adaptador_de_volcado(ajustes, escritura_habilitada=True)` → `return _adaptador_de_volcado(ajustes, escritura_habilitada=False)` | Bloque 3 (`infrastructure/sigrid/fabrica.py:333`) | muerto en la campaña |
| 164 | `infrastructure/sigrid/volcado.py:96` | entero | `_HTTP_DEL_LOTE = 400` → `_HTTP_DEL_LOTE = 401` | Bloque 3 (`infrastructure/sigrid/volcado.py:96`) | muerto en la campaña |
| 165 | `infrastructure/sigrid/volcado.py:173` | booleano | `reraise=True,` → `reraise=False,` | Bloque 3 (`infrastructure/sigrid/volcado.py:173`) | muerto en la campaña |
| 166 | `infrastructure/sigrid/volcado.py:184` | not | `if not filas:` → `if filas:` | Bloque 3 (`infrastructure/sigrid/volcado.py:184`) | muerto en la campaña |
| 167 | `infrastructure/sigrid/volcado.py:185` | booleano | `return False` → `return True` | Bloque 3 (`infrastructure/sigrid/volcado.py:185`) | muerto en la campaña |
| 168 | `infrastructure/sigrid/volcado.py:186` | entero | `return int(filas[0][0]) == 1` → `return int(filas[1][0]) == 1` | Bloque 3 (`infrastructure/sigrid/volcado.py:186`) | muerto en la campaña |
| 169 | `infrastructure/sigrid/volcado.py:186` | entero | `return int(filas[0][0]) == 1` → `return int(filas[0][1]) == 1` | Bloque 3 (`infrastructure/sigrid/volcado.py:186`) | muerto en la campaña |
| 170 | `infrastructure/sigrid/volcado.py:186` | comparacion | `return int(filas[0][0]) == 1` → `return int(filas[0][0]) != 1` | Bloque 3 (`infrastructure/sigrid/volcado.py:186`) | muerto en la campaña |
| 171 | `infrastructure/sigrid/volcado.py:186` | entero | `return int(filas[0][0]) == 1` → `return int(filas[0][0]) == 2` | Bloque 3 (`infrastructure/sigrid/volcado.py:186`) | muerto en la campaña |
| 172 | `infrastructure/sigrid/volcado.py:190` | booleano | `if cuerpo.get("commit") is not False:` → `if cuerpo.get("commit") is not True:` | Bloque 3 (`infrastructure/sigrid/volcado.py:190`) | muerto en la campaña |
| 173 | `infrastructure/sigrid/volcado.py:196` | not | `if not self._escritura_habilitada:` → `if self._escritura_habilitada:` | Bloque 3 (`infrastructure/sigrid/volcado.py:196`) | muerto en la campaña |
| 174 | `infrastructure/sigrid/volcado.py:201` | booleano | `if cuerpo.get("commit") is not True:` → `if cuerpo.get("commit") is not False:` | Bloque 3 (`infrastructure/sigrid/volcado.py:201`) | muerto en la campaña |
| 175 | `infrastructure/sigrid/volcado.py:213` | aritmetico | `segundos = time.monotonic() - arranque` → `segundos = time.monotonic() + arranque` | Bloque 3 (`infrastructure/sigrid/volcado.py:213`) | muerto en la campaña |
| 176 | `infrastructure/sigrid/volcado.py:214` | logico | `partes = len(cuerpo.get("partes") or ())` → `partes = len(cuerpo.get("partes") and ())` | Bloque 3 (`infrastructure/sigrid/volcado.py:214`) | muerto en la campaña |
| 177 | `infrastructure/sigrid/volcado.py:244` | comparacion | `if respuesta.status_code == _HTTP_DEL_LOTE:` → `if respuesta.status_code != _HTTP_DEL_LOTE:` | Bloque 3 (`infrastructure/sigrid/volcado.py:244`) | muerto en la campaña |
| 178 | `infrastructure/sigrid/volcado.py:254` | not | `if not isinstance(datos, dict):` → `if isinstance(datos, dict):` | Bloque 3 (`infrastructure/sigrid/volcado.py:254`) | muerto en la campaña |
| 179 | `infrastructure/sigrid/volcado.py:268` | not | `if not isinstance(datos, dict):` → `if isinstance(datos, dict):` | Bloque 3 (`infrastructure/sigrid/volcado.py:268`) | muerto en la campaña |
| 180 | `interface_adapters/api/volcado.py:160` | entero | `return 503` → `return 504` | Bloque 4 (`interface_adapters/api/volcado.py:160`) | muerto en la campaña |
| 181 | `interface_adapters/api/volcado.py:161` | entero | `return 409` → `return 410` | Bloque 4 (`interface_adapters/api/volcado.py:161`) | muerto en la campaña |
| 182 | `interface_adapters/api/volcado.py:207` | comparacion | `return {clave: valor for clave, valor in volcado.items() if clave != "volcado_por"}` → `return {clave: valor for clave, valor in volcado.items() if clave == "volcado_por"}` | Bloque 4 (`interface_adapters/api/volcado.py:207`) | muerto en la campaña |
| 183 | `interface_adapters/api/volcado.py:277` | booleano | `if datos["confirmado"] is not True:` → `if datos["confirmado"] is not False:` | Bloque 4 (`interface_adapters/api/volcado.py:277`) | muerto en la campaña |
| 184 | `interface_adapters/api/volcado.py:332` | not | `if not isinstance(cuerpo, dict) or set(cuerpo) != claves:` → `if isinstance(cuerpo, dict) or set(cuerpo) != claves:` | Bloque 4 (`interface_adapters/api/volcado.py:332`) | muerto en la campaña |
| 185 | `interface_adapters/api/volcado.py:332` | logico | `if not isinstance(cuerpo, dict) or set(cuerpo) != claves:` → `if not isinstance(cuerpo, dict) and set(cuerpo) != claves:` | Bloque 4 (`interface_adapters/api/volcado.py:332`) | muerto en la campaña |
| 186 | `interface_adapters/api/volcado.py:332` | comparacion | `if not isinstance(cuerpo, dict) or set(cuerpo) != claves:` → `if not isinstance(cuerpo, dict) or set(cuerpo) == claves:` | Bloque 4 (`interface_adapters/api/volcado.py:332`) | muerto en la campaña |
| 187 | `interface_adapters/api/volcado.py:359` | comparacion | `if str(identificador) == crudo.lower():` → `if str(identificador) != crudo.lower():` | Bloque 4 (`interface_adapters/api/volcado.py:359`) | muerto en la campaña |
| 188 | `interface_adapters/api/volcado.py:366` | not | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 189 | `interface_adapters/api/volcado.py:366` | logico | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if not isinstance(crudo, list) and not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 190 | `interface_adapters/api/volcado.py:366` | not | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if not isinstance(crudo, list) or 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 191 | `interface_adapters/api/volcado.py:366` | entero | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if not isinstance(crudo, list) or not 2 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 192 | `interface_adapters/api/volcado.py:366` | comparacion | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if not isinstance(crudo, list) or not 1 < len(crudo) <= MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 193 | `interface_adapters/api/volcado.py:366` | comparacion | `if not isinstance(crudo, list) or not 1 <= len(crudo) <= MAX_PARTES_POR_LLAMADA:` → `if not isinstance(crudo, list) or not 1 <= len(crudo) < MAX_PARTES_POR_LLAMADA:` | Bloque 4 (`interface_adapters/api/volcado.py:366`) | muerto en la campaña |
| 194 | `interface_adapters/api/volcado.py:386` | not | `if not isinstance(elemento, dict) or set(elemento) != _CLAVES_DE_PEDIDA:` → `if isinstance(elemento, dict) or set(elemento) != _CLAVES_DE_PEDIDA:` | Bloque 4 (`interface_adapters/api/volcado.py:386`) | muerto en la campaña |
| 195 | `interface_adapters/api/volcado.py:386` | logico | `if not isinstance(elemento, dict) or set(elemento) != _CLAVES_DE_PEDIDA:` → `if not isinstance(elemento, dict) and set(elemento) != _CLAVES_DE_PEDIDA:` | Bloque 4 (`interface_adapters/api/volcado.py:386`) | muerto en la campaña |
| 196 | `interface_adapters/api/volcado.py:386` | comparacion | `if not isinstance(elemento, dict) or set(elemento) != _CLAVES_DE_PEDIDA:` → `if not isinstance(elemento, dict) or set(elemento) == _CLAVES_DE_PEDIDA:` | Bloque 4 (`interface_adapters/api/volcado.py:386`) | muerto en la campaña |
| 197 | `interface_adapters/api/volcado.py:392` | not | `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` → `if isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` | Bloque 4 (`interface_adapters/api/volcado.py:392`) | muerto en la campaña |
| 198 | `interface_adapters/api/volcado.py:392` | logico | `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` → `if not isinstance(revision_id, int) and isinstance(revision_id, bool) or revision_id < 1:` | Bloque 4 (`interface_adapters/api/volcado.py:392`) | muerto en la campaña |
| 199 | `interface_adapters/api/volcado.py:392` | logico | `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` → `if not isinstance(revision_id, int) or isinstance(revision_id, bool) and revision_id < 1:` | Bloque 4 (`interface_adapters/api/volcado.py:392`) | muerto en la campaña |
| 200 | `interface_adapters/api/volcado.py:392` | comparacion | `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` → `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id <= 1:` | Bloque 4 (`interface_adapters/api/volcado.py:392`) | muerto en la campaña |
| 201 | `interface_adapters/api/volcado.py:392` | entero | `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 1:` → `if not isinstance(revision_id, int) or isinstance(revision_id, bool) or revision_id < 2:` | Bloque 4 (`interface_adapters/api/volcado.py:392`) | muerto en la campaña |
| 202 | `interface_adapters/api/volcado.py:409` | comparacion | `if len(set(ids)) != len(ids):` → `if len(set(ids)) == len(ids):` | Bloque 4 (`interface_adapters/api/volcado.py:409`) | muerto en la campaña |
| 203 | `interface_adapters/api/volcado.py:419` | comparacion | `if cuantas > n:` → `if cuantas >= n:` | Bloque 4 (`interface_adapters/api/volcado.py:419`) | muerto en la campaña |

## Los dos que ninguna campaña de bloque midió, a mano

Los dos son de `_con_texto`, la regla de C-B1-1 y C-B1-2 (la corrección de la review del Bloque 1, posterior a su
campaña y anterior a la base del Bloque 2). En un worktree desechable de `HEAD` en el scratchpad (ya retirado; el
árbol de trabajo no se mutó), cada mutante aplicado sobre `domain/models/volcado.py` y los tests de F-059 sin
`test_f059_alcance_cerrado.py`, con `-x`, desde el scratchpad (sin `.env`):

| # | Fichero:línea | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|---|
| 52 | `domain/models/volcado.py:364` | `if texto is None or not texto.strip():` → `if texto is None and not texto.strip():` | **muerto** (`1 failed, 324 passed in 14.19s`) | `test_f059_pipeline_volcado.py::test_f059_s10_el_ensayo_va_base_login_ensayo_y_base` |
| 53 | `domain/models/volcado.py:364` | `if texto is None or not texto.strip():` → `if texto is None or texto.strip():` | **muerto** (`1 failed, 536 passed in 9.21s`) | `test_f059_volcado_dominio.py::test_f059_r6_el_parte_clave_a_clave` |

## Referencias

- La estimación, las alternativas A, B y C y la decisión: `progress/impl_F-059.md`, Bloque 5, T22.
- Los cuatro informes de bloque: `progress/mutacion_F-059_bloque1.md`, `progress/mutacion_F-059_bloque2.md`,
  `progress/mutacion_F-059_bloque3.md` y `progress/mutacion_F-059_bloque4.md`.
- Los mutantes a mano de cada bloque y los equivalentes aceptados por el humano (V05d, A09 y los 13 de E-1):
  `progress/impl_F-059.md`, T3, T9, T12, T17 y «Mutantes 16 y 24».
