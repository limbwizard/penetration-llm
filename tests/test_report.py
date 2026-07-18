from __future__ import annotations

from pentest_llm.models import ExecutionMode, Finding, RiskLevel, Scope
from pentest_llm.report import export_markdown
from pentest_llm.storage import Storage


def _storage(tmp_path):
    return Storage(tmp_path / "sessions.sqlite")


def test_export_markdown_writes_sections(tmp_path):
    storage = _storage(tmp_path)
    session = storage.create_session(
        "Report test",
        ExecutionMode.MANUAL,
        Scope(target_type="web app", authorized_targets=["app.test"]),
    )
    storage.add_finding(
        session.id,
        Finding(
            title="Reflected XSS",
            severity=RiskLevel.HIGH,
            evidence="payload reflected",
            remediation="encode output",
        ),
    )
    storage.add_command_run(
        session.id,
        {"technique": "service scan", "risk_level": "low"},
        {"command": "nmap -sV app.test", "stdout": "80/tcp open http", "stderr": ""},
        "exit_0",
    )

    destination = tmp_path / "report.md"
    out = export_markdown(storage, session, destination, executive_summary="Overall low risk.")
    text = out.read_text(encoding="utf-8")

    assert "# Assessment Report: Report test" in text
    assert "## Executive Summary" in text
    assert "Overall low risk." in text
    assert "Reflected XSS" in text
    assert "encode output" in text
    assert "nmap -sV app.test" in text
    assert "80/tcp open http" in text


def test_export_markdown_handles_empty_session(tmp_path):
    storage = _storage(tmp_path)
    session = storage.create_session("Empty", ExecutionMode.MANUAL, Scope())
    out = export_markdown(storage, session, tmp_path / "empty.md")
    text = out.read_text(encoding="utf-8")
    assert "No findings have been recorded yet." in text
    assert "No commands have been executed through the assistant." in text
