from __future__ import annotations

import functools

import pytest

from pentest_llm import cli
from pentest_llm.models import ExecutionMode, Scope
from pentest_llm.storage import Storage


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    """Point the CLI's Storage() at a throwaway DB instead of the repo store."""
    db = tmp_path / "sessions.sqlite"
    monkeypatch.setattr(cli, "Storage", functools.partial(Storage, db))
    return Storage(db)


def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "penetration-llm" in capsys.readouterr().out


def test_sessions_subcommand_lists_sessions(isolated_storage, capsys):
    isolated_storage.create_session("Alpha", ExecutionMode.MANUAL, Scope())
    assert cli.main(["sessions"]) == 0
    assert "Alpha" in capsys.readouterr().out


def test_tools_subcommand_runs(isolated_storage, capsys):
    assert cli.main(["tools"]) == 0
    assert "Local Tool Inventory" in capsys.readouterr().out


def test_plan_subcommand_uses_latest_session(isolated_storage, capsys):
    isolated_storage.create_session(
        "Plan", ExecutionMode.MANUAL, Scope(allowed_categories=["recon"])
    )
    assert cli.main(["plan", "recon"]) == 0
    assert "Recon" in capsys.readouterr().out


def test_report_subcommand_exports_empty_session(isolated_storage, tmp_path, capsys):
    isolated_storage.create_session("Rep", ExecutionMode.MANUAL, Scope())
    out = tmp_path / "out.md"
    assert cli.main(["report", str(out)]) == 0
    assert out.exists()
    assert "Assessment Report: Rep" in out.read_text(encoding="utf-8")


def test_plan_without_session_returns_error(isolated_storage):
    assert cli.main(["plan"]) == 2
