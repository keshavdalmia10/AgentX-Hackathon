"""Unit tests for FixtureLoader."""

import pytest
from unittest.mock import MagicMock, patch, mock_open

from agentx.infrastructure.fixture_loader import FixtureLoader


class TestFixtureLoaderInit:
    """Tests for FixtureLoader initialization."""

    def test_init_sets_parameters(self):
        """Test that constructor sets parameters correctly."""
        mock_db = MagicMock()
        loader = FixtureLoader(mock_db, schema="test_schema")

        assert loader._db_manager is mock_db
        assert loader.schema == "test_schema"

    def test_init_default_schema(self):
        """Test that default schema is 'public'."""
        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)

        assert loader.schema == "public"


class TestLoad:
    """Tests for load method."""

    def test_load_empty_rows(self):
        """Test load with empty rows returns 0."""
        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)

        result = loader.load("users", [])

        assert result == 0

    def test_load_single_row(self):
        """Test load with single row."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_copy = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.copy.return_value.__enter__ = MagicMock(return_value=mock_copy)
        mock_cursor.copy.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        result = loader.load("users", [{"id": 1, "name": "Alice"}])

        assert result == 1
        mock_conn.commit.assert_called_once()

    def test_load_multiple_rows(self):
        """Test load with multiple rows."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_copy = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.copy.return_value.__enter__ = MagicMock(return_value=mock_copy)
        mock_cursor.copy.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        result = loader.load("users", rows)

        assert result == 3

    def test_load_handles_none_values(self):
        """Test load handles None values."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_copy = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.copy.return_value.__enter__ = MagicMock(return_value=mock_copy)
        mock_cursor.copy.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        result = loader.load("users", [{"id": 1, "name": None}])

        assert result == 1

    def test_load_handles_dict_values(self):
        """Test load handles dict values (JSON columns)."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_copy = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.copy.return_value.__enter__ = MagicMock(return_value=mock_copy)
        mock_cursor.copy.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        result = loader.load("users", [{"id": 1, "metadata": {"key": "value"}}])

        assert result == 1


class TestTeardown:
    """Tests for teardown method."""

    def test_teardown_empty_tables(self):
        """Test teardown with empty table list does nothing."""
        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)

        loader.teardown([])

        mock_db.connection.assert_not_called()

    def test_teardown_single_table(self):
        """Test teardown truncates single table."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        loader.teardown(["users"])

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_teardown_multiple_tables(self):
        """Test teardown truncates multiple tables."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        loader.teardown(["orders", "users"])

        assert mock_cursor.execute.call_count == 2


class TestSavepoints:
    """Tests for savepoint methods."""

    def test_create_savepoint(self):
        """Test create_savepoint executes SAVEPOINT."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)
        loader.create_savepoint(mock_conn, "test_savepoint")

        mock_cursor.execute.assert_called_once_with("SAVEPOINT test_savepoint")

    def test_rollback_to_savepoint(self):
        """Test rollback_to_savepoint executes ROLLBACK TO."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)
        loader.rollback_to_savepoint(mock_conn, "test_savepoint")

        mock_cursor.execute.assert_called_once_with("ROLLBACK TO SAVEPOINT test_savepoint")

    def test_release_savepoint(self):
        """Test release_savepoint executes RELEASE."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_db = MagicMock()
        loader = FixtureLoader(mock_db)
        loader.release_savepoint(mock_conn, "test_savepoint")

        mock_cursor.execute.assert_called_once_with("RELEASE SAVEPOINT test_savepoint")


class TestSetupTestFixtures:
    """Tests for setup_test_fixtures method."""

    def test_setup_test_fixtures_multiple_tables(self):
        """Test setup_test_fixtures loads multiple tables."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_copy = MagicMock()

        mock_db.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.copy.return_value.__enter__ = MagicMock(return_value=mock_copy)
        mock_cursor.copy.return_value.__exit__ = MagicMock(return_value=False)

        loader = FixtureLoader(mock_db)
        fixtures = {
            "users": [{"id": 1, "name": "Alice"}],
            "orders": [{"id": 1, "user_id": 1}],
        }
        result = loader.setup_test_fixtures(fixtures)

        assert result == {"users": 1, "orders": 1}
