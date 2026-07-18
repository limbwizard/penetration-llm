from __future__ import annotations

from pentest_llm.executor import CommandExecutor


def test_run_captures_stdout_and_exit_code():
    result = CommandExecutor().run("echo hello")
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert not result.timed_out


def test_run_captures_nonzero_exit():
    result = CommandExecutor().run("exit 3")
    assert result.exit_code == 3


def test_run_times_out():
    result = CommandExecutor(timeout=1).run("sleep 5")
    assert result.timed_out
    assert result.exit_code is None
