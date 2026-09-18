# Script 25 · Mediciones del despliegue de F-032 y F-033

Encargo operativo sin feature propia (patrón de `chore/script-22-ventana-archivo`).
Rama `chore/script-25-mediciones-despliegue`, fusionada en `dev` con `--no-ff`.
**No se ha ejecutado contra la base**: lo lanza el humano.

## Qué se ha hecho

Un fichero nuevo: `infra/25_mediciones_despliegue.ps1`, calcado de
`infra/21_historico_estado.ps1` (psycopg desde el `.venv` del servicio, sin
`psql`; contraseña como `SecureString`, solo en memoria y en el entorno del
proceso, que se limpia al terminar; Python por fichero con
`Invoke-PythonDelServicio` del 08; rutas desde `$PSScriptRoot`, así que se lanza
desde cualquier carpeta; veredicto con `Comprobar`/`Escribir-Veredicto`).
Además, la sesión se abre con `read_only = True` de psycopg: la base rechazaría
cualquier escritura.

**Modo por omisión (antes de desplegar):**

1. **F-032 T14 (R26)**: la consulta de `impl_F-032.md` §T14, con un único
   cambio de forma: los blancos se escriben con `chr(32)||chr(9)||chr(10)||chr(13)||chr(160)||chr(8239)`
   en vez de `E' \t\n\r'` (mismo conjunto, sin depender del escape de Python).
2. **F-033 T13 (R26)**: las dos consultas de `impl_F-033.md` tal cual
   (recuento por estado con `con_biblioteca`, y lista de `pendiente`).
3. **Para F-013**: trazas `archivado` por `drive_id` distinto. El SQL solo
   devuelve agregados (`drive_id IS NULL`, recuento, primer y último
   `archivado_at_utc`); el id no sale de la base. Se rotulan «biblioteca 1, 2…»
   por orden de su primer archivado, lo que ayuda a distinguir la de IT (la
   más antigua) de la de Posventa.

Veredicto: F-032 = 0 filas y F-033 = 0 `pendiente` → `PASA` («se puede
desplegar»), salida 0. Si no, `NO PASA` (salida 6) y un bloque «QUE HACER» con
lo que dice cada spec: F-032 → anotar `hash_parte`, `carpeta` y
`nombre_fichero`, y esos partes no se re-archivan desde el circuito (R27);
F-033 → una persona mira esas carpetas en SharePoint antes de desplegar.

**Modo parte (F-033 T14, después de desplegar):** `-HashParte` o
`-NumeroIncidencia` imprime `estado`, `intentos` y `archivado_at_utc` y una
línea `FOTO` para copiar. Relanzado con `-FotoAntes "<esa línea>"`, el veredicto
compara los tres valores (R27: ninguna escritura). También comprueba que el
parte consta `archivado`, que es la precondición de T14.

## Cómo lanzarlo (PowerShell, desde la raíz del repo)

Antes de desplegar:

```
powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1
```

Después de desplegar, foto antes de re-archivar y foto después:

```
powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1 -HashParte "<hash>"
powershell -ExecutionPolicy Bypass -File infra\25_mediciones_despliegue.ps1 -HashParte "<hash>" -FotoAntes "<linea FOTO de antes>"
```

Pide el host de PostgreSQL y la contraseña de `postventa_app` por consola.

## Verificado

- Sin caracteres no ASCII ni BOM; primera línea `# infra/25_mediciones_despliegue.ps1`.
- El parser de PowerShell 5.1 (`Parser.ParseFile`) lo da por bueno: 0 errores.
- El bloque Python extraído compila (`ast.parse`) con el `.venv` del servicio
  (psycopg 3.3.4, que admite `read_only`).
- `bash harness/init.sh`: verde (62 tests de raíz; servicios en verde).
- Barrido de identificadores y tests de scripts de `infra/`
  (`test_f006_repo_sin_identificadores.py` y los seis `test_*scripts_infra*`):
  **323 passed, 3 skipped**, con el script ya commiteado. Ninguno fija un
  inventario cerrado que obligue a dar de alta el 25 (21 y 22 tampoco están).

## Qué no se ha verificado / qué falta

- **No se ha ejecutado contra la base** (encargo explícito). La primera
  ejecución real es la del humano; si algo del formateo falla, la lectura es
  igualmente de solo lectura.
- Anotar los resultados en `impl_F-032.md` (T14) e `impl_F-033.md` (T13, T14) y
  marcar esas casillas de `tasks.md`: es del humano o del líder tras la medición.
- `azure-apps/` no cambia: el script no altera nada de lo que el proyecto
  expone o consume.
