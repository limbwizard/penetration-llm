# Local Terminal Pentest Chat Agent

`penetration-llm` is a lean local-first terminal chat assistant for authorized security testing. It connects only to a project-local Chat Completions-compatible Ollama server at `http://127.0.0.1:11435/v1` using `deephat` (DeepHat-V1-7B, an offensive-security fine-tune of Qwen2.5-Coder-7B, built locally from an in-repo Modelfile with a 32K context window), keeps session context in SQLite, proposes pentest-aware commands, captures output, and exports Markdown reports.

The app intentionally stays small. Bring your own operational guardrails, authorization workflow, and target restrictions.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On Linux or Kali:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Start a Session

```bash
penetration-llm
```

The first run starts a short context wizard. You will provide:

- targets/context
- target type and allowed test categories
- optional exclusions, testing window, and authorization reference
- intensity and notes

The local model settings are built into the app.

## Project-Local Data

Runtime data is kept inside this repo under `.penetration-llm/`:

- `.penetration-llm/sessions.sqlite` for chat/session history
- `.penetration-llm/reports/` for default report exports
- `.penetration-llm/ollama/models/` for this app's Ollama model store
- `.penetration-llm/home`, `.penetration-llm/config`, `.penetration-llm/cache`, and `.penetration-llm/share` for local runtime state

The app does not use `~/.penetration-llm`, `~/.ollama`, `/root/.ollama`, or the default Ollama `localhost:11434` model store.

## Chat Commands

- `/help` shows commands.
- `/context` or `/scope` prints the session context.
- `/sessions` lists saved sessions.
- `/plan [phase|all]` prints an offline assessment plan for the current scope.
- `/tools` checks availability of common local assessment tools.
- `/mode manual|assisted|automated` changes execution mode.
- `/timeout [seconds]` shows or updates the local command timeout.
- `/paste` accepts pasted command output until a line containing only `EOF`.
- `/exec <command>` runs a local command and stores the output.
- `/report [path]` exports a Markdown report.
- `/findings` lists stored findings.
- `/exit` quits.

## Execution Modes

- `manual`: default. The model proposes commands, you run them externally, then paste output back.
- `assisted`: model-proposed commands require a single confirmation before subprocess execution.
- `automated`: model-proposed commands are executed directly after proposal parsing.

## Local Model Setup

Start a project-local Ollama server in one terminal:

```bash
scripts/ollama-local.sh serve
```

Build the app's model into this repo from another terminal. The `deephat` tag is created locally
from `scripts/DeepHat.Modelfile`, which pins the model's full 32K native context window:

```bash
scripts/ollama-local.sh build
```

`build` downloads a Q6_K GGUF of DeepHat-V1-7B into `.penetration-llm/ollama/gguf/` and creates the
`deephat` model in the project-local store. It defaults to the
[mradermacher](https://huggingface.co/mradermacher/DeepHat-V1-7B-GGUF) Q6_K quant; override with
`DEEPHAT_GGUF_URL=<url>` (and optionally `DEEPHAT_GGUF_SHA256=<sha>` to verify) for a different
quant or mirror. The server runs with `OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q8_0` so
the 32K context stays cheap on a 16 GB GPU.

Then run the assistant:

```bash
penetration-llm
```

If this WSL/Linux environment does not have an `ollama` binary on `PATH`, place one at `.penetration-llm/bin/ollama` or run:

```bash
scripts/ollama-local.sh install
```

The local installer downloads Ollama into `.penetration-llm/runtime/` and links `.penetration-llm/bin/ollama`. If system `zstd` is unavailable, the script vendors Python `zstandard` into `.penetration-llm/python/` and still avoids writing to system paths.

## Lean Design

- no built-in scope matcher
- no output redaction layer
- no command denylist
- no remote LLM endpoints or API keys
- execution behavior is controlled by the selected mode

## Syntax Check

```bash
python -m compileall src
```
