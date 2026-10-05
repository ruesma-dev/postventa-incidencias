<!-- progress/explore_F-036.md -->
# F-036 · T2: medición de los catálogos de la plantilla (obra 0677)

> Ejecutado por el humano el 2026-09-28 con
> `infra\26_catalogos_plantilla_sigrid.ps1 -CodigoObra 0677 -SigridBaseDatos ruesma -SalidaJson "$env:TEMP\catalogo_0677.json"`
> (commit del script `63c0879`). Veredicto del script: **PASA**. El JSON queda
> en `%TEMP%\catalogo_0677.json`, fuera del repositorio: lleva nombres de
> proveedor. Aquí, sin identificadores ni nombres de persona o de empresa.
> Anotado por el líder a partir de la salida de consola que pegó el humano.

## Unidades de posventa

- 1 obra con código 0677 y unidades de posventa. 15 unidades, `0677.03VILLA 1.`
  … `0677.03VILLA 15.`, con `con.res` «Viviendas Bloque Villa N». Ninguna con
  texto no reconocido: **no llevan nombres de persona**.
- «Villa 1» del Excel actual = `0677.03VILLA 1.` (D-9).
- `upv.espacios`: vacío en las 15.

## Oficios de la obra (`obrofc`)

- 39 filas, 31 oficios distintos, **0 de baja**, 36 proveedores distintos, 8
  oficios con más de un proveedor, **3 filas sin proveedor**: justo
  `0133 Solados y Alicatados`, `0144 Carpintería de aluminio` y
  `0166 Mobiliario cocina`, tres de los oficios que usa el Excel de Posventa.
- Parecidos **dentro de la obra**: por nombre sin mayúsculas ni tildes, 1 grupo
  (`0046 Carpinteria de madera` / `0143 Carpintería de madera`). Además, a
  ojo y fuera de lo que mide la intercalación, `0085 Mobiliario de cocinas` /
  `0166 Mobiliario cocina` y `0033 Solados y Alicatados M.O.` /
  `0133 Solados y Alicatados`. Es exactamente el caso que anticipó el humano
  (plural, «de», tilde).
- Global en `auxofc`: 130 oficios, 7 grupos de 2 por nombre sin
  mayúsculas ni tildes.

### Oficios del Excel actual frente a los de la obra

| Excel | En la obra | Nota |
|---|---|---|
| Carpintería de aluminio | `0144`, literal | sin proveedor en la obra |
| Solados y alicatados | `0133` «Solados y Alicatados» | difiere en mayúsculas; sin proveedor; parecido a `0033 … M.O.` |
| Pintura | `0028`, literal | |
| Mamparas | `0026`, literal | |
| Albañilería | `0145`, literal | |
| Mobiliario cocina | `0166`, literal | sin proveedor; parecido a `0085 Mobiliario de cocinas` |
| Carpintería de madera | `0143`, literal | gemelo sin tilde `0046` |
| Fontanería | `0134`, literal | |

## Proveedores

- En la obra: 0 sin CIF; **0 grupos** por CIF y 0 por nombre.
- En todos los proveedores que aparecen en algún `obrofc` (526): **0 grupos**
  por CIF y 0 por nombre.
- En el maestro completo (9.585): 151 sin CIF, **793 grupos por CIF** (1.980
  códigos) y **530 por nombre** (1.229 códigos).
- Los duplicados existen en el maestro, pero no entre los proveedores que
  están dados de alta en obras. La errata y el plural se miden en T8.

## Familias (tercera enmienda, `design.md` §16): la hipótesis NO se sostiene

- `auxfam`: **0 filas**. `confam`: **0 filas** para los 36 proveedores de la
  obra y para los 526 de `obrofc`. `entfam`: 0.
- `prv.ofcide` relleno en 1 de 36 (obra) y 3 de 526 (global); cuando lo está,
  coincide con un oficio suyo en `obrofc`.
- Conclusión: las «familias asignadas a un proveedor» de las que habla el
  humano **no están en `confam`/`auxfam`/`entfam`**. Candidata sin medir vista
  en el diccionario: `auxtarprv` («Clasificaciones Proveedor»). Según T3, se
  vuelve al spec-author.

### Dónde están de verdad: `conact` → `auxpronat` (2026-09-28)

Correo del director de Compras al humano, «RE: familias proveedores», del
2026-09-28, con captura de la ficha de un proveedor. La captura no se versiona:
trae datos de contacto. Lo que dice:

- Las actividades de cada proveedor se recogen en la caja **«Naturaleza de
  productos, servicios y/o actividades que suministra o desarrolla
  [múltiples]»**, en la pestaña **Datos fiscales** de la ficha del proveedor.
  El botón **Expandir** enseña las actividades y **el árbol**.
- En la misma pestaña, justo debajo, está la caja «Familia de productos,
  servicios y/o actividades… [múltiples]». En la captura está **vacía**, igual
  que `confam` en la medición.
- Ejemplos de valores en la captura: «REVESTIMIENTOS HORIZONTALES Y
  VERTICALES», «APARATOS SANITARIOS Y GRIFERIA», «MOBILIARIO, EQUIPAMIENTOS Y
  TEXTILES». Es **otro vocabulario** que el de los oficios (`auxofc`:
  «Solados y Alicatados», «Fontanería»…).

En el diccionario (`azure-apps/sigrid_tablas.md`):

- **`conact`** («Actividades de una entidad», NN): `conide` → `con`,
  `actide` → **`auxpronat`**, `homolo`, `tot`, `tipfab`, `tipdis`, `tipsmo`…
  Es el gemelo de `confam`.
- **`auxpronat`** («Gestión: Naturalezas de Productos / Actividades», tipo
  `TC`, catálogo en árbol): `cod` de 16, `res` de 48, `pos`, `fecbaj`, y las
  cuentas contables.

Sin medir todavía: cuántos proveedores de la obra tienen filas en `conact`, la
forma del árbol de `auxpronat` (niveles, cómo se codifican los padres) y cuánto
casa con `auxofc`. Por el vocabulario, la correspondencia actividad → oficio
casi seguro **no** será la identidad: será una tabla que confirma el humano,
posiblemente a nivel de rama del árbol.

## Ubicaciones (`rcp.resubi`)

- 1.219 reclamaciones de la obra, 1 sin ubicación, **44 ubicaciones
  distintas**, texto libre sin nombres de persona. Las más frecuentes: jardín
  (178), cocina (70), escalera (64), salón (62), garaje (58), baño 1 (55),
  dormitorio 1 (55), distribuidor p. baja (48)…
- Con variantes del mismo sitio: `baño 3` / `bao 3`, `cuarto plancha` /
  `Cuarto de plancha`, `terraza instalaciones` / `terraza instaciones`,
  `lavandería` / `lavanderçia/tendedero`. Base para la lista cerrada (D-3).

## Defecto del script: el texto llega con doble codificación

La consola enseña las tildes mal (`DomÃ³tica`, `baÃ±o`), y el JSON **también
las guarda mal**: comprobado por el líder, `Fontanería` está escrito como
`Fontaner` + `C3 83 C2 AD` (UTF-8 de «Ã­»), es decir, la respuesta de la
pasarela se decodifica como Latin-1 y se vuelve a codificar en UTF-8. Los
recuentos hechos en SQL no cambian, pero **todo nombre del JSON está
corrompido**. T8 (propuesta de parecidos sobre los nombres) no puede correr
sobre él: hay que corregir la lectura en el T1 y repetir T2.

## T2 repetida (2026-09-29), con T1 bis (`1b3edfb`)

Mismo comando, contra la red real. Veredicto **PASA**. Las tildes salen bien
en consola (`Fontanería`, `Albañilería`, `baño 1`) y el JSON se reescribe en
`%TEMP%`. Los recuentos de arriba no cambian (1.221 reclamaciones, dos más
que ayer). Lo nuevo, las actividades:

- **Obra**: 33 de 36 proveedores tienen actividades en `conact`: 81 filas y 58
  actividades distintas. Distribución: 3 con 0, 8 con 1, 10 con 2, 10 con 3,
  3 con 4, 1 con 5 y 1 con 6. **Homologadas: 0**. De baja: 0.
- **Global** (proveedores de `obrofc`): 360 de 526 con actividades, 825 filas,
  234 actividades distintas; homologadas, 0.
- **Árbol de `auxpronat`**: 514 actividades, ninguna de baja. El padre se
  codifica por **prefijo**, sin separadores, en **3 niveles** (9 / 195 / 310).
  Formas `AA` → `AA99` o `AAAA` → `AA9999` o `AAAA99`.
- Las actividades de la obra caen en **5 de las 9 ramas** de primer nivel
  (24, 17, 14, 2 y 1 actividades).
- **Cruce con `auxofc`**: 0 códigos en común. Por nombre sin mayúsculas ni
  tildes, **21 actividades** se llaman igual que un oficio (12 oficios
  distintos).

Consecuencias para T3:

- `homolo` no se usa en Sigrid (0 de 825): la D-27 no filtra nada.
- El árbol se reconstruye, así que la D-29 puede ser «hoja y rama».
- La correspondencia actividad → oficio no es la identidad (D-28): 21
  propuestas salen solas por nombre y el resto es a mano (58 actividades en
  la obra y 234 en todas las obras).

## Ubicaciones: las 44 `rcp.resubi` de la 0677, completas (T2 repetida, 2026-09-29)

Copiadas tal cual de la consola, con su recuento; son 1.221 reclamaciones y
una sin ubicación. Revisadas por el líder: ningún nombre de persona. Se
conservan las erratas del origen (`bao 3`, `lavanderçia/tendedero`,
`terraza instaciones`) porque de ellas sale la normalización de T6.

| Recuento | Ubicación |
|---:|---|
| 179 | jardín |
| 70 | cocina |
| 64 | escalera |
| 62 | salón |
| 58 | Garaje |
| 55 | baño 1 |
| 55 | dormitorio 1 |
| 48 | distribuidor p. baja |
| 46 | dormitorio 3 |
| 44 | almacén |
| 40 | dormitorio 4 |
| 40 | sala/estudio |
| 39 | dormitorio 2 |
| 32 | terraza planta 2 |
| 31 | terraza 1 |
| 28 | baño 7 |
| 27 | baño 2 |
| 26 | bao 3 |
| 25 | office |
| 24 | Cuarto de plancha |
| 24 | vestíbulo sótano |
| 20 | lavandería |
| 20 | terraza 3 |
| 19 | baño 6 |
| 15 | baño 4 |
| 11 | terraza instalaciones |
| 10 | aseo |
| 10 | distribuidor p. 1 |
| 9 | baño 5 |
| 9 | vestidor 3 |
| 8 | baño 3 |
| 8 | cuarto plancha |
| 7 | cuarto instalaciones |
| 7 | lavanderçia/tendedero |
| 7 | patio trasero |
| 7 | terraza instaciones |
| 7 | vestíbulo p. baja |
| 7 | vestidor 1 |
| 6 | comedor |
| 5 | patio delantero |
| 4 | despacho |
| 3 | ascensor |
| 2 | terraza 4 |
| 2 | trastero |

## Los 31 oficios de la 0677, nombres exactos de Sigrid (T24, 2026-09-30)

Sacados por el implementer del JSON de la T2 repetida
(`%TEMP%\catalogo_0677.json`, fuera del repositorio), **solo** el código y el
nombre del oficio (`auxofc.res`, tal cual): ni proveedores ni recuentos por
proveedor. Es la lista contra la que se escriben los oficios de
`scripts/migracion_f036_correcciones.yaml` (R97) y la que lee
`tests/test_f036_migracion_contenido.py`. «Sin proveedor» = sin ninguna fila
de `obrofc` con proveedor en la obra.

| Código | Nombre en Sigrid | Nota |
|---|---|---|
| `0010` | Domótica | |
| `0011` | Electricidad | |
| `0018` | Fachada Ventilada | |
| `0021` | Impermeabilizaciones | |
| `0026` | Mamparas | |
| `0028` | Pintura | |
| `0029` | Piscina | |
| `0030` | Pladur | |
| `0033` | Solados y Alicatados M.O. | gemelo de `0133` |
| `0034` | Tarima | |
| `0035` | Telecomunicaciones | |
| `0037` | Vidrios | |
| `0039` | Ascensores | |
| `0046` | Carpinteria de madera | sin tilde; gemelo de `0143` |
| `0054` | Cerramientos exteriores | |
| `0065` | Enfoscados y gunitados | |
| `0067` | Plastones | |
| `0085` | Mobiliario de cocinas | gemelo de `0166` |
| `0118` | V-Aire acondicionado | |
| `0133` | Solados y Alicatados | sin proveedor |
| `0134` | Fontanería | |
| `0138` | Tabiquería móvil | |
| `0142` | Hormigón pulido | |
| `0143` | Carpintería de madera | |
| `0144` | Carpintería de aluminio | sin proveedor |
| `0145` | Albañilería | |
| `0147` | Cerrajería | |
| `0153` | Calefacción y suelo refrescante | |
| `0155` | Sate | |
| `0159` | Puertas RF | |
| `0166` | Mobiliario cocina | sin proveedor |

## T8 (2026-09-29): propuesta de oficios casi duplicados

> Ejecutado por el implementer, desde `services/postventa-api`, con
> `.venv/Scripts/python.exe scripts/medir_catalogos_f036.py --catalogo "%TEMP%\catalogo_0677.json"`
> (el JSON de la T2 repetida, fuera del repositorio). Umbrales: la opción por
> defecto de D-22. El script solo imprime recuentos; aquí, sin nombres ni
> códigos.

**Oficios de la obra** (31 oficios, 39 filas de `obrofc`, 3 sin proveedor):

- 3 propuestas, las 3 grupos enteros de 2 códigos; 0 por pares; 0 componentes
  que no son clique.
- Por motivo: `mismo_nombre` 1, `plural` 1, `errata` 0, `incluido` 1. Son los
  tres pares que se vieron a ojo en T2, cada uno con el motivo esperado.

**Todo `auxofc`** (130 oficios):

- 12 propuestas, las 12 grupos enteros: 9 de 2 códigos, 1 de 3 y 2 de 4; 0 por
  pares; 0 componentes que no son clique.
- Pares propuestos por motivo: `mismo_nombre` 11, `plural` 3, `errata` 9,
  `incluido` 1: 24, que son todos los pares de esos 12 grupos (9 + 3 + 2 × 6),
  cada uno con un solo motivo.
- T2 contaba 7 grupos de 2 por nombre sin mayúsculas ni tildes; la clave de
  §15.2 (sin puntuación ni palabras vacías, con siglas) une más.

**La plantilla de la obra**:

| | Sin grupos | Con lo propuesto en la obra confirmado | Con lo propuesto en `auxofc` confirmado |
|---|---:|---:|---:|
| Opciones de `Oficio` | 31 | 28 | 28 |
| Grupos con más de un código en la obra (futuros `oficio_ambiguo`, D-19) | 0 | 3 | 3 |
| Pares de la columna `Proveedor` | 36 | 36 | 36 |
| Oficios con un solo proveedor que resuelve (los que R91 rellenaría) | 20 | 18 | 18 |
| Oficios sin ningún proveedor en `obrofc` | 3 | 1 | 1 |

Lectura: confirmar además los grupos de todo `auxofc` no cambia ningún
recuento de la plantilla de la 0677. Confirmar los tres grupos deja **3 oficios ambiguos** en la obra
y dos de los tres oficios sin proveedor (de los que usa el Excel de Posventa)
pasan a ofrecer los proveedores de su gemelo: elegir uno resuelve el oficio al
código del gemelo (R94), no al suyo. Queda uno sin ninguno.
