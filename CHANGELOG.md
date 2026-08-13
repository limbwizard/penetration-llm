# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-12

### Added
- **Intelligent context-window budgeting** (`pentest_llm/context.py`). Chat
  history is now fitted to the model's 32K window before each request: system
  framing and the current turn are always kept, recent history fills the rest,
  and a single oversized message (a huge scan dump) is truncated head-and-tail
  instead of silently overflowing the window. Configurable via
  `PENTEST_LLM_CONTEXT_TOKENS` and `PENTEST_LLM_RESPONSE_TOKENS`.
- Test suite (`pytest`) covering models, LLM parsing, context budgeting,
  methodology, storage, reporting, and markup-safe rendering.
- Developer tooling: `ruff` (lint + format) and `mypy` configuration, a `dev`
  extra, a `Makefile`, `.editorconfig`, and a GitHub Actions CI workflow.
- `PENTEST_LLM_OLLAMA_HOST` / `PENTEST_LLM_URL` environment overrides for the
  local model endpoint; `emergency_contact` is now collected in the session
  wizard so it is populated end-to-end.

### Fixed
- **Rich markup crash.** Streamed model output and command/output panels were
  passed through Rich's markup parser, so any bracket sequence a scanner emits
  (`[+]`, `[*]`, `[/red]`, `[1-1000]`) could raise `MarkupError` and abort the
  session. All dynamic text now renders literally.
- **Ambiguous "latest session".** Sessions were ordered by whole-second
  timestamps with no tiebreak, so two sessions created in the same second had an
  undefined resume order. Timestamps are now microsecond-precise and ordering is
  deterministic.
- `Scope.from_dict` no longer drifts from the dataclass defaults, so a
  `to_dict()`/`from_dict()` round-trip is stable.

### Changed
- `cli.py` slimmed to orchestration; terminal rendering extracted to
  `pentest_llm/render.py`, and a single `LLMClient` is shared across a session.
- Project version is now sourced from `pentest_llm.__version__`.
- **Model tuned for maximum quality at native 32K on 16 GB VRAM.** The build now
  fetches the near-lossless **Q8_0** quant (~8.1 GB) and serves it with an **f16
  KV cache** (`OLLAMA_KV_CACHE_TYPE=f16`) for full attention precision. The
  Modelfile raises `num_predict` to 2048 so richer multi-step plans are not
  truncated, softens `repeat_penalty` to 1.05 (a coder model legitimately
  repeats flags/JSON keys/paths), adds `min_p` sampling, and documents an
  optional rope-scaling block for experimenting past 32K.
- `scripts/bake_rope.py`: self-contained tool to bake YaRN rope-scaling metadata
  into a GGUF, unlocking a larger context window (64K/96K/128K) when needed.

## [0.1.0]

### Added
- Initial release: local-first terminal pentest chat assistant, project-local
  Ollama/DeepHat-V1-7B build, SQLite session storage, command execution modes,
  offline methodology planner, tool inventory, and Markdown reporting.
