from __future__ import annotations

from pentest_llm.llm import (
    _trim_history,
    build_messages,
    extract_command_proposal,
    extract_findings,
    extract_json_payloads,
    scope_context,
)
from pentest_llm.models import RiskLevel, Scope


def test_extract_json_payloads_from_fenced_block():
    text = """Here you go:
```json
{"type": "command_proposal", "commands": ["nmap -sV 10.0.0.5"], "risk_level": "low"}
```
"""
    payloads = extract_json_payloads(text)
    assert any(p.get("type") == "command_proposal" for p in payloads)


def test_extract_json_payloads_deduplicates():
    # The same object appears fenced and bare; it must be returned once.
    obj = '{"type": "finding", "title": "x", "severity": "low"}'
    text = f"```json\n{obj}\n```\nalso inline {obj}"
    payloads = [p for p in extract_json_payloads(text) if p.get("type") == "finding"]
    assert len(payloads) == 1


def test_extract_command_proposal_prefers_json():
    text = """```json
{"type":"command_proposal","phase":"Recon","commands":["nmap -sV -p- 10.0.0.5"],"risk_level":"low"}
```"""
    proposal = extract_command_proposal(text)
    assert proposal is not None
    assert proposal.commands == ["nmap -sV -p- 10.0.0.5"]
    assert proposal.risk_level is RiskLevel.LOW


def test_extract_command_proposal_falls_back_to_shell_fence():
    text = """Run a service scan next.
```bash
# scan the host
nmap -sV -p- 10.0.0.5
```
"""
    proposal = extract_command_proposal(text)
    assert proposal is not None
    assert proposal.commands == ["nmap -sV -p- 10.0.0.5"]


def test_shell_fence_joins_line_continuations_and_drops_prose():
    text = """```sh
ffuf -u https://app.test/FUZZ \\
  -w words.txt
This sentence is prose that the model dropped into the fence.
```"""
    proposal = extract_command_proposal(text)
    assert proposal is not None
    assert proposal.commands == ["ffuf -u https://app.test/FUZZ -w words.txt"]


def test_extract_command_proposal_returns_none_without_command():
    assert extract_command_proposal("Just some analysis, no command here.") is None


def test_extract_findings():
    text = """```json
{"type":"finding","title":"SQLi","severity":"critical","evidence":"boolean-based"}
```"""
    findings = extract_findings(text)
    assert len(findings) == 1
    assert findings[0].severity is RiskLevel.CRITICAL


def test_build_messages_orders_system_then_history():
    scope = Scope(authorized_targets=["10.0.0.5"])
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    messages = build_messages(scope, history, user_text="next?")
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "next?"}
    assert [m["role"] for m in messages[2:4]] == ["user", "assistant"]


def test_trim_history_keeps_most_recent_within_budget():
    history = [{"role": "user", "content": "x" * 100} for _ in range(10)]
    for i, item in enumerate(history):
        item["content"] = f"{i}:" + item["content"]
    kept = _trim_history(history, budget=250)
    # Budget fits ~2 of the ~102-char messages; the newest must be retained.
    assert kept[-1] is history[-1]
    assert len(kept) < len(history)


def test_trim_history_always_keeps_newest_even_if_oversized():
    history = [{"role": "user", "content": "tiny"}, {"role": "user", "content": "z" * 5000}]
    kept = _trim_history(history, budget=100)
    assert kept == [{"role": "user", "content": "z" * 5000}]


def test_build_messages_drops_old_history_over_budget():
    scope = Scope()
    history = [{"role": "user", "content": "old " * 30000}, {"role": "assistant", "content": "recent"}]
    messages = build_messages(scope, history)
    # Two system messages + only the recent turn survive the budget.
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "assistant", "content": "recent"}
    assert all("old" not in m["content"] for m in messages)


def test_scope_context_lists_targets():
    scope = Scope(authorized_targets=["10.0.0.5", "app.test"], target_type="web app")
    ctx = scope_context(scope)
    assert "10.0.0.5, app.test" in ctx
    assert "web app" in ctx
