from __future__ import annotations

import pytest

from pentest_llm.models import ExecutionMode, Finding, RiskLevel, Scope
from pentest_llm.storage import Storage


@pytest.fixture()
def storage(tmp_path):
    return Storage(tmp_path / "sessions.sqlite")


def test_create_and_get_session_roundtrip(storage):
    scope = Scope(target_type="api", authorized_targets=["10.0.0.5"])
    session = storage.create_session("Test", ExecutionMode.ASSISTED, scope)
    fetched = storage.get_session(session.id)
    assert fetched is not None
    assert fetched.name == "Test"
    assert fetched.mode is ExecutionMode.ASSISTED
    assert fetched.scope.authorized_targets == ["10.0.0.5"]


def test_latest_session_returns_most_recent(storage):
    first = storage.create_session("first", ExecutionMode.MANUAL, Scope())
    second = storage.create_session("second", ExecutionMode.MANUAL, Scope())
    second.name = "second-updated"
    storage.update_session(second)
    latest = storage.latest_session()
    assert latest is not None
    assert latest.id == second.id
    assert {s.id for s in storage.list_sessions()} == {first.id, second.id}


def test_messages_are_returned_in_chronological_order(storage):
    session = storage.create_session("s", ExecutionMode.MANUAL, Scope())
    for i in range(5):
        storage.add_message(session.id, "user", f"msg {i}")
    messages = storage.list_messages(session.id, limit=3)
    # limit keeps the newest 3, still oldest-first.
    assert [m["content"] for m in messages] == ["msg 2", "msg 3", "msg 4"]


def test_findings_roundtrip(storage):
    session = storage.create_session("s", ExecutionMode.MANUAL, Scope())
    storage.add_finding(
        session.id,
        Finding(title="XSS", severity=RiskLevel.HIGH, evidence="reflected"),
    )
    findings = storage.list_findings(session.id)
    assert len(findings) == 1
    assert findings[0].title == "XSS"
    assert findings[0].severity is RiskLevel.HIGH


def test_command_runs_and_events_are_scoped(storage):
    session = storage.create_session("s", ExecutionMode.MANUAL, Scope())
    other = storage.create_session("other", ExecutionMode.MANUAL, Scope())
    storage.add_command_run(session.id, {"technique": "scan"}, {"command": "nmap"}, "exit_0")
    storage.add_event(session.id, "command_executed", {"command": "nmap"})
    assert len(storage.list_command_runs(session.id)) == 1
    assert len(storage.list_command_runs(other.id)) == 0
    assert storage.list_events(session.id)[0]["kind"] == "command_executed"


def test_get_missing_session_returns_none(storage):
    assert storage.get_session("does-not-exist") is None
