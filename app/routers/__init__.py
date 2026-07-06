"""
routers package
---------------
Each module in this package groups a set of related endpoints behind an
``APIRouter``. ``app/main.py`` imports and mounts them. Splitting endpoints by
domain (machines, maintenance, health) keeps every file small and focused,
which is the standard way large FastAPI projects stay maintainable.
"""
