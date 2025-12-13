"""Infrastructure module for PostgreSQL data layer.

This module provides zero-ORM database connectivity using psycopg3,
schema introspection via pg_catalog, and bulk loading via COPY protocol.
"""

from agentx.infrastructure.database_manager import DatabaseManager
from agentx.infrastructure.fixture_loader import FixtureLoader
from agentx.infrastructure.schema_inspector import SchemaInspector

__all__ = [
    "DatabaseManager",
    "SchemaInspector",
    "FixtureLoader",
]
