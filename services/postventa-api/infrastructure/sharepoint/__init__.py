# services/postventa-api/infrastructure/sharepoint/__init__.py
"""El único paquete del servicio que conoce Microsoft Graph (F-006).

Igual que `infrastructure/llm/` es el único que conoce el SDK de Gemini y
`infrastructure/persistencia/` el único que conoce `psycopg`. Que sea el único
lo vigila `tests/test_f006_arquitectura.py`, no la buena voluntad.
"""
