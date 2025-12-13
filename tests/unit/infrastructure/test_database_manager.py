"""Unit tests for DatabaseManager."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from agentx.infrastructure.database_manager import DatabaseManager


class TestDatabaseManagerInit:
    """Tests for DatabaseManager initialization."""

    def test_init_sets_parameters(self):
        """Test that constructor sets parameters correctly."""
        db = DatabaseManager(
            database_url="postgresql://user:pass@localhost/db",
            pool_min_size=5,
            pool_max_size=20,
            pool_timeout=60.0,
        )

        assert db._database_url == "postgresql://user:pass@localhost/db"
        assert db._pool_min_size == 5
        assert db._pool_max_size == 20
        assert db._pool_timeout == 60.0
        assert db._pool is None
        assert db._is_open is False

    def test_init_with_defaults(self):
        """Test that default parameters are set."""
        db = DatabaseManager("postgresql://localhost/test")

        assert db._pool_min_size == 2
        assert db._pool_max_size == 10
        assert db._pool_timeout == 30.0

    def test_is_open_false_when_not_opened(self):
        """Test is_open returns False when pool not opened."""
        db = DatabaseManager("postgresql://localhost/test")
        assert db.is_open is False


class TestDatabaseManagerConnection:
    """Tests for connection management."""

    @patch("agentx.infrastructure.database_manager.ConnectionPool")
    def test_open_creates_pool(self, mock_pool_class):
        """Test that open() creates a connection pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        db = DatabaseManager("postgresql://localhost/test")
        db.open()

        mock_pool_class.assert_called_once()
        assert db.is_open is True

    @patch("agentx.infrastructure.database_manager.ConnectionPool")
    def test_close_closes_pool(self, mock_pool_class):
        """Test that close() closes the pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        db = DatabaseManager("postgresql://localhost/test")
        db.open()
        db.close()

        mock_pool.close.assert_called_once()
        assert db.is_open is False

    @patch("agentx.infrastructure.database_manager.ConnectionPool")
    def test_open_idempotent(self, mock_pool_class):
        """Test that calling open() twice doesn't create duplicate pools."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        db = DatabaseManager("postgresql://localhost/test")
        db.open()
        db.open()  # Second call should be no-op

        assert mock_pool_class.call_count == 1

    def test_execute_requires_open(self):
        """Test that execute raises if pool not open."""
        db = DatabaseManager("postgresql://localhost/test")

        with pytest.raises(RuntimeError, match="not open"):
            db.execute("SELECT 1")

    def test_connection_context_requires_open(self):
        """Test that connection() raises if pool not open."""
        db = DatabaseManager("postgresql://localhost/test")

        with pytest.raises(RuntimeError, match="not open"):
            with db.connection():
                pass


class TestDatabaseManagerContextManager:
    """Tests for context manager usage."""

    @patch("agentx.infrastructure.database_manager.ConnectionPool")
    def test_context_manager_opens_and_closes(self, mock_pool_class):
        """Test that context manager opens and closes pool."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_conn = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

        with DatabaseManager("postgresql://localhost/test") as db:
            assert db.is_open is True

        mock_pool.close.assert_called_once()


class TestDatabaseManagerExecute:
    """Tests for execute method."""

    @patch("agentx.infrastructure.database_manager.ConnectionPool")
    def test_execute_returns_dict_rows(self, mock_pool_class):
        """Test that execute returns list of dicts."""
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        db = DatabaseManager("postgresql://localhost/test")
        db.open()
        result = db.execute("SELECT id, name FROM users")

        assert result == [{"id": 1, "name": "test"}]
        mock_conn.commit.assert_called()


class TestDatabaseManagerHealthCheck:
    """Tests for health check."""

    def test_health_check_false_when_not_open(self):
        """Test health check returns False when pool not open."""
        db = DatabaseManager("postgresql://localhost/test")
        assert db.check_health() is False


class TestDatabaseManagerPoolStats:
    """Tests for pool statistics."""

    def test_pool_stats_closed(self):
        """Test pool stats when pool is closed."""
        db = DatabaseManager("postgresql://localhost/test")
        stats = db.get_pool_stats()

        assert stats == {"status": "closed"}
