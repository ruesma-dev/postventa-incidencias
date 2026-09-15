# services/postventa-api/infrastructure/sigrid/__init__.py
"""El único paquete del servicio que conoce `sigrid-api` (F-009).

Igual que `infrastructure/sharepoint/` es el único que conoce Microsoft Graph y
`infrastructure/persistencia/` el único que conoce `psycopg`. Si mañana el
acceso al ERP cambia de forma, esta es la única pieza que hay que reescribir.

Dentro, la separación que hace probable la feature más peligrosa del proyecto:
`consultas.py` y `escrituras.py` son **puros** —devuelven `(sql, parámetros)` y
no abren nada—, y `cliente.py` es lo único que habla por la red.
"""
