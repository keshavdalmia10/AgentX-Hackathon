"""Unit tests for SchemaInspector."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from agentx.infrastructure.schema_inspector import SchemaInspector
from agentx.core.models import ColumnInfo, ForeignKey, TableInfo, SchemaSnapshot


class TestSchemaInspectorInit:
    """Tests for SchemaInspector initialization."""

    def test_init_sets_connection_and_schema(self):
        """Test that constructor sets connection and schema."""
        mock_conn = MagicMock()
        inspector = SchemaInspector(mock_conn, schema="test_schema")

        assert inspector._conn is mock_conn
        assert inspector.schema == "test_schema"

    def test_init_default_schema(self):
        """Test that default schema is 'public'."""
        mock_conn = MagicMock()
        inspector = SchemaInspector(mock_conn)

        assert inspector.schema == "public"


class TestGetTables:
    """Tests for get_tables method."""

    def test_get_tables_returns_list(self):
        """Test that get_tables returns list of table names."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"table_name": "users"},
            {"table_name": "orders"},
            {"table_name": "products"},
        ]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        tables = inspector.get_tables()

        assert tables == ["users", "orders", "products"]

    def test_get_tables_empty(self):
        """Test get_tables with no tables."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        tables = inspector.get_tables()

        assert tables == []


class TestGetColumns:
    """Tests for get_columns method."""

    def test_get_columns_basic(self):
        """Test get_columns returns ColumnInfo objects."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Simulate multiple query results
        call_count = [0]

        def mock_fetchall():
            call_count[0] += 1
            if call_count[0] == 1:
                # Column query
                return [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "udt_name": "int4",
                        "is_nullable": "NO",
                        "column_default": None,
                        "character_maximum_length": None,
                        "numeric_precision": None,
                        "numeric_scale": None,
                    },
                    {
                        "column_name": "name",
                        "data_type": "character varying",
                        "udt_name": "varchar",
                        "is_nullable": "YES",
                        "column_default": None,
                        "character_maximum_length": 255,
                        "numeric_precision": None,
                        "numeric_scale": None,
                    },
                ]
            elif call_count[0] == 2:
                # PK query
                return [{"column_name": "id"}]
            else:
                # FK query
                return []

        mock_cursor.fetchall = mock_fetchall
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        columns = inspector.get_columns("users")

        assert len(columns) == 2
        assert columns[0].name == "id"
        assert columns[0].dtype == "integer"
        assert columns[0].nullable is False
        assert columns[0].primary_key is True
        assert columns[1].name == "name"
        assert columns[1].dtype == "character varying(255)"
        assert columns[1].nullable is True


class TestGetForeignKeys:
    """Tests for get_foreign_keys method."""

    def test_get_foreign_keys_returns_list(self):
        """Test that get_foreign_keys returns ForeignKey objects."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "column_name": "user_id",
                "references_table": "users",
                "references_column": "id",
                "constraint_name": "orders_user_id_fkey",
            }
        ]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        fks = inspector.get_foreign_keys("orders")

        assert len(fks) == 1
        assert fks[0].column == "user_id"
        assert fks[0].references_table == "users"
        assert fks[0].references_column == "id"


class TestGetPrimaryKeys:
    """Tests for get_primary_keys method."""

    def test_get_primary_keys_single(self):
        """Test get_primary_keys with single column PK."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"column_name": "id"}]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        pks = inspector.get_primary_keys("users")

        assert pks == ["id"]

    def test_get_primary_keys_composite(self):
        """Test get_primary_keys with composite PK."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"column_name": "order_id"},
            {"column_name": "product_id"},
        ]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        inspector = SchemaInspector(mock_conn)
        pks = inspector.get_primary_keys("order_items")

        assert pks == ["order_id", "product_id"]


class TestSchemaSnapshot:
    """Tests for SchemaSnapshot model."""

    def test_has_table_case_insensitive(self):
        """Test has_table is case insensitive."""
        snapshot = SchemaSnapshot(
            dialect="postgresql",
            database="test",
            tables={
                "Users": TableInfo(name="Users", columns=[]),
            },
        )

        assert snapshot.has_table("Users") is True
        assert snapshot.has_table("users") is True
        assert snapshot.has_table("USERS") is True
        assert snapshot.has_table("nonexistent") is False

    def test_has_column_case_insensitive(self):
        """Test has_column is case insensitive."""
        snapshot = SchemaSnapshot(
            dialect="postgresql",
            database="test",
            tables={
                "users": TableInfo(
                    name="users",
                    columns=[
                        ColumnInfo(name="Email", dtype="varchar", nullable=True),
                    ],
                ),
            },
        )

        assert snapshot.has_column("users", "Email") is True
        assert snapshot.has_column("users", "email") is True
        assert snapshot.has_column("USERS", "EMAIL") is True
        assert snapshot.has_column("users", "nonexistent") is False

    def test_get_table(self):
        """Test get_table returns TableInfo."""
        table_info = TableInfo(name="users", columns=[])
        snapshot = SchemaSnapshot(
            dialect="postgresql",
            database="test",
            tables={"users": table_info},
        )

        assert snapshot.get_table("users") is table_info
        assert snapshot.get_table("Users") is table_info
        assert snapshot.get_table("nonexistent") is None
