from __future__ import annotations

from pentest_llm.models import (
    CommandProposal,
    CommandResult,
    Finding,
    RiskLevel,
    Scope,
)


def test_risk_level_from_text_aliases():
    assert RiskLevel.from_text("info") is RiskLevel.INFORMATIONAL
    assert RiskLevel.from_text("CRIT") is RiskLevel.CRITICAL
    assert RiskLevel.from_text("  High ") is RiskLevel.HIGH
    assert RiskLevel.from_text("med") is RiskLevel.MEDIUM


def test_risk_level_from_text_unknown_defaults_to_medium():
    assert RiskLevel.from_text(None) is RiskLevel.MEDIUM
    assert RiskLevel.from_text("nonsense") is RiskLevel.MEDIUM


def test_scope_roundtrip_preserves_fields():
    scope = Scope(
        target_type="api",
        authorized_targets=["10.0.0.5", "app.example.test"],
        excluded_targets=["10.0.0.1"],
        allowed_categories=["recon", "scanning"],
        testing_window="Mon-Fri 09:00-17:00",
        intensity="aggressive",
        emergency_contact="soc@example.test",
        authorization_label="PO-123",
        notes="dev environment only",
    )
    restored = Scope.from_dict(scope.to_dict())
    assert restored == scope


def test_scope_summary_includes_optional_fields_when_present():
    scope = Scope(emergency_contact="soc@example.test", notes="ping first")
    summary = scope.summary()
    assert "Emergency contact: soc@example.test" in summary
    assert "Notes: ping first" in summary


def test_command_proposal_from_payload_normalizes_commands():
    proposal = CommandProposal.from_payload(
        {
            "type": "command_proposal",
            "phase": "Scanning",
            "commands": ["  nmap -sV 10.0.0.5  ", "", "  "],
            "risk": "high",
        }
    )
    assert proposal.commands == ["nmap -sV 10.0.0.5"]
    assert proposal.risk_level is RiskLevel.HIGH
    assert proposal.phase == "Scanning"


def test_command_proposal_accepts_single_string_command():
    proposal = CommandProposal.from_payload({"command": "whoami"})
    assert proposal.commands == ["whoami"]


def test_command_proposal_to_dict_serializes_enum():
    proposal = CommandProposal.from_payload({"commands": ["id"], "risk_level": "low"})
    assert proposal.to_dict()["risk_level"] == "low"


def test_finding_roundtrip():
    finding = Finding.from_payload(
        {
            "title": "Reflected XSS",
            "severity": "high",
            "evidence": "payload reflected unescaped",
            "business_impact": "session theft",
        }
    )
    assert finding.severity is RiskLevel.HIGH
    assert finding.to_dict()["severity"] == "high"
    assert finding.title == "Reflected XSS"


def test_command_result_combined_output_merges_streams():
    result = CommandResult(
        command="echo hi",
        exit_code=0,
        stdout="hi\n",
        stderr=" warn ",
        started_at="t0",
        completed_at="t1",
    )
    assert result.combined_output() == "hi\nwarn"
