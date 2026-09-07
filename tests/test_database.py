import sqlite3

import pytest

from premium_model_budget_governor.database import connection


def test_connection_commits_and_closes(tmp_path):
    path = tmp_path / "test.sqlite3"
    with connection(path) as db:
        db.execute("CREATE TABLE test(value)")
        db.execute("INSERT INTO test VALUES (1)")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        db.execute("SELECT 1")
    with connection(path) as check:
        assert check.execute("SELECT value FROM test").fetchall() == [(1,)]


def test_connection_rolls_back_and_closes_on_error(tmp_path):
    path = tmp_path / "test.sqlite3"
    with connection(path) as db:
        db.execute("CREATE TABLE test(value)")
    with pytest.raises(ValueError):
        with connection(path) as failing:
            failing.execute("INSERT INTO test VALUES (1)")
            raise ValueError("failure")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        failing.execute("SELECT 1")
    with connection(path) as check:
        assert check.execute("SELECT value FROM test").fetchall() == []
