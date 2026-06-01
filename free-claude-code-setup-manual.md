# Free Claude Code + DeepSeek: Complete Setup

Set up an Anthropic-compatible proxy server that routes Claude Code traffic through DeepSeek, with dual workflows for cheap (DeepSeek) and expensive (native Claude) tasks.

## 1. Overview

[free-claude-code](https://github.com/Alishahryar1/free-claude-code) is a FastAPI-based proxy that intercepts Claude Code's Anthropic Messages API calls and routes them to alternative providers. We configure it to use **DeepSeek** as the backend, giving you a free/cheap coding assistant for routine tasks while keeping native Claude available for complex work.

**Note:** [free-claude-code](https://github.com/Alishahryar1/free-claude-code) is mirrored at [free-claude-code](https://github.com/alifesoftware/free-claude-code)

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│                  Your Terminal                       │
│                                                      │
│  claude-cheap ───> ANTHROPIC_BASE_URL=localhost:8082 │
│                         │                            │
│                         ▼                            │
│              Proxy (free-claude-code)                │
│                         │                            │
│                         ▼                            │
│              DeepSeek API (deepseek-chat)            │
│                                                      │
│  claude-pro ───> ANTHROPIC_API_KEY (native Claude)   │
└─────────────────────────────────────────────────────┘
```
---

## Table of Contents

1. [1-Click Setup](#1-one-click-setup)
2. [Prerequisites](#2-prerequisites)
3. [Clone the Repository](#3-clone-the-repository)
4. [Install Dependencies](#4-install-dependencies)
5. [Configure DeepSeek as the Default Provider](#5-configure-deepseek-as-the-default-provider)
   - [5.1 Project-Level `.env` File](#51-project-level-env-file)
   - [5.2 Managed Config at `~/.fcc/.env`](#52-managed-config-at-fccenv)
6. [Create the Dual Workflow Launcher Scripts](#6-create-the-dual-workflow-launcher-scripts)
   - [6.1 DeepSeek Launcher: `start-deepseek.sh`](#61-deepseek-launcher-start-deepseeksh)
   - [6.2 Native Claude Launcher: `start-native-claude.sh`](#62-native-claude-launcher-start-native-claudesh)
7. [Add Shell Aliases](#7-add-shell-aliases)
8. [Start the Proxy Server](#8-start-the-proxy-server)
9. [Verify Everything Works](#9-verify-everything-works)
10. [Usage Guide](#10-usage-guide)
    - [10.1 Cheap Tasks (DeepSeek via Proxy)](#101-cheap-tasks-deepseek-via-proxy)
    - [10.2 Expensive Tasks (Native Claude)](#102-expensive-tasks-native-claude)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. One-Click Setup
Run the script
```bash
python3 setup_free_claude_code.py
```

## 2. Prerequisites

Before starting, ensure you have:

- **Git** — to clone the repository
- **uv** (>= 0.11.0) — Python package manager that handles Python version management
- A **DeepSeek API key** — get one at [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
- **Claude Code CLI** installed on your system

Check uv is installed:

```bash
uv --version
```

If uv is not installed, install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **Note on Python:** The project requires Python >= 3.14. `uv` will automatically download and manage the correct Python version during `uv sync` — you do not need to install it manually.

---

## 3. Clone the Repository

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
```

or use the mirror

```bash
git clone https://github.com/alifesoftware/free-claude-code.git
cd free-claude-code
```

---

## 4. Install Dependencies

Run `uv sync` inside the repository. This creates a virtual environment (`.venv/`) with Python 3.14 and installs all project dependencies:

```bash
uv sync
```

This will:
- Auto-download Python 3.14 if not already installed
- Create `.venv/` with all dependencies from `uv.lock`
- Install CLI entry points (`fcc-server`, `fcc-claude`, `fcc-init`)

---

## 5. Configure DeepSeek as the Default Provider

There are two configuration files to set up:

### 5.1 Project-Level `.env` File

Create or edit `free-claude-code/.env`:

```bash
# free-claude-code/.env

# DeepSeek Configuration
# Get your API key from: https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"

# Set DeepSeek as the default model
# Common options: deepseek-chat, deepseek-coder, deepseek-v4-flash, deepseek-v4-pro
MODEL=deepseek/deepseek-v4-flash

# Optional: Route specific Claude model tiers to different DeepSeek models
# Opus tier → more capable (and expensive) model
# Sonnet/Haiku tiers → inherit MODEL if not set
MODEL_OPUS=deepseek/deepseek-v4-pro
# MODEL_SONNET=deepseek/deepseek-chat
# MODEL_HAIKU=deepseek/deepseek-chat

# Server Configuration
HOST=0.0.0.0
PORT=8082

# Enable model thinking (DeepSeek supports this)
ENABLE_MODEL_THINKING=true
```

The key fields:

| Field | Value | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | `sk-...` | Your DeepSeek API key |
| `MODEL` | `deepseek/deepseek-v4-flash` | Default model for all tiers |
| `MODEL_OPUS` | `deepseek/deepseek-v4-pro` | Override for Opus-tier requests |
| `PORT` | `8082` | Port the proxy listens on |

### 5.2 Managed Config at `~/.fcc/.env`

The proxy also reads from `~/.fcc/.env` (the managed config path). Create this file:

```bash
mkdir -p ~/.fcc
```

```bash
# ~/.fcc/.env

# Disable optional features (not needed for CLI-only use)
MESSAGING_PLATFORM="none"
VOICE_NOTE_ENABLED=false

# DeepSeek Configuration
DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"

# Default model
MODEL=deepseek/deepseek-v4-flash

# Auth token Claude Code sends to the proxy
ANTHROPIC_AUTH_TOKEN="freecc"

# Route Opus tier to a more capable model
MODEL_OPUS=deepseek/deepseek-v4-pro

# Server Configuration
HOST=0.0.0.0
PORT=8082

# Enable model thinking
ENABLE_MODEL_THINKING=true
```

> **Important:** Replace `sk-your-deepseek-api-key-here` with your actual DeepSeek API key in both files. The managed config at `~/.fcc/.env` takes precedence when the proxy loads settings at runtime.

---

## 6. Create the Dual Workflow Launcher Scripts

Create two shell scripts in the repository root to switch between DeepSeek (via proxy) and native Claude.

### 6.1 DeepSeek Launcher: `start-deepseek.sh`

This script launches Claude Code pointed at the local proxy, routing all traffic through DeepSeek.

**File:** `free-claude-code/start-deepseek.sh`

```bash
#!/bin/bash
# DeepSeek instance — cheap tasks (scripts, tests, tool calling, automations)

export ANTHROPIC_BASE_URL="http://localhost:8082"
export ANTHROPIC_AUTH_TOKEN="freecc"
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="190000"

claude "$@"
```

Environment variables explained:

| Variable | Value | Purpose |
|---|---|---|
| `ANTHROPIC_BASE_URL` | `http://localhost:8082` | Point Claude Code at the local proxy |
| `ANTHROPIC_AUTH_TOKEN` | `freecc` | Auth token matching the proxy's config |
| `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` | `1` | Enable proxy model listing in Claude's `/model` picker |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | `190000` | 190k-token auto-compaction window for larger context |

Make it executable:

```bash
chmod +x start-deepseek.sh
```

### 6.2 Native Claude Launcher: `start-native-claude.sh`

This script strips proxy environment variables so Claude Code connects directly to Anthropic using your real `ANTHROPIC_API_KEY`.

**File:** `free-claude-code/start-native-claude.sh`

```bash
#!/bin/bash
# Native Claude instance — expensive tasks (reasoning, web dev, architecture, reviews)
# Uses your real ANTHROPIC_API_KEY from the environment

unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY

claude "$@"
```

Make it executable:

```bash
chmod +x start-native-claude.sh
```

---

## 7. Add Shell Aliases

Add convenience aliases to your shell profile (`~/.zshrc` for Zsh, `~/.bashrc` for Bash) so you can switch workflows easily:

```bash
# FreeClaudeCode aliases
alias fcc-run='uv run python server.py'
alias fcc-run-god-mode='sudo uv run python server.py'
alias claude-cheap="source /path/to/free-claude-code/start-deepseek.sh"
alias claude-pro="source /path/to/free-claude-code/start-native-claude.sh"
```

Replace `/path/to/free-claude-code/` with the absolute path to your cloned repository.

**Example using `echo` to append:**

```bash
cat >> ~/.zshrc << 'EOF'

# FreeClaudeCode aliases
alias fcc-run='uv run python server.py'
alias fcc-run-god-mode='sudo uv run python server.py'
alias claude-cheap="source $HOME/Development/FreeClaudeCodeGodMode/free-claude-code/start-deepseek.sh"
alias claude-pro="source $HOME/Development/FreeClaudeCodeGodMode/free-claude-code/start-native-claude.sh"
EOF
```

Reload your shell to activate the aliases:

```bash
source ~/.zshrc
```

Alias reference:

| Alias | Command | What it does |
|---|---|---|
| `fcc-run` | `uv run python server.py` | Start the proxy server |
| `fcc-run-god-mode` | `sudo uv run python server.py` | Start proxy with sudo |
| `claude-cheap` | sources `start-deepseek.sh` | Launch Claude Code → proxy → DeepSeek |
| `claude-pro` | sources `start-native-claude.sh` | Launch native Claude Code (no proxy) |

> **Note:** The `source` keyword in the aliases is critical — it runs the script in the current shell, so the environment variables (or `unset` commands) affect your current session. Using `bash start-deepseek.sh` would spawn a subshell and the exports would not apply.

---

## 8. Start the Proxy Server

From the `free-claude-code/` directory, start the server:

```bash
cd free-claude-code
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

Or using the alias (if you set it up):

```bash
fcc-run
```

Expected output:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8082 (Press CTRL+C to quit)
INFO:     Admin UI: http://127.0.0.1:8082/admin (local-only)
```

Keep this terminal running while you work. The proxy must be running for `claude-cheap` to work.

---

## 9. Verify Everything Works

### 9.1 Health Check

Test that the proxy server responds:

```bash
curl http://localhost:8082/health
```

Expected response:

```json
{"status":"healthy"}
```

### 9.2 Admin UI

Open [http://localhost:8082/admin](http://localhost:8082/admin) in a browser. You should see the Free Claude Code Admin UI where you can view and edit proxy settings.

### 9.3 Model Listing

Verify the proxy exposes available models:

```bash
curl http://localhost:8082/v1/models
```

### 9.4 Run Project Tests (Optional)

```bash
uv run pytest
```

---

## 10. Usage Guide

With the proxy running, open a **new terminal** and use the aliases.

### 10.1 Cheap Tasks (DeepSeek via Proxy)

For scripts, unit tests, tool calling, automations, and simple coding tasks:

```bash
claude-cheap
```

This launches Claude Code with:
- `ANTHROPIC_BASE_URL=http://localhost:8082` → all API calls go to the proxy
- Proxy forwards them to DeepSeek using your DeepSeek API key
- All Claude Code features (tool use, file editing, bash commands) work normally

### 10.2 Expensive Tasks (Native Claude)

For complex reasoning, web development, architecture, and code reviews:

```bash
claude-pro
```

This launches Claude Code with:
- `ANTHROPIC_BASE_URL` unset → connects directly to `api.anthropic.com`
- Uses your real `ANTHROPIC_API_KEY` from your environment
- No proxy involvement — full native Claude capabilities

---

## 11. Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `claude-cheap` says "Connection refused" | Proxy server not running | Start the proxy with `fcc-run` in another terminal |
| "401 Unauthorized" from proxy | Auth token mismatch | Check `ANTHROPIC_AUTH_TOKEN` matches in `~/.fcc/.env` and `start-deepseek.sh` |
| "402 Payment Required" from DeepSeek | API key invalid or out of credits | Verify your DeepSeek API key at [platform.deepseek.com](https://platform.deepseek.com) |
| `uv sync` fails | uv version too old | Update uv: `uv self update` |
| `claude: command not found` | Claude Code not installed | Install Claude Code CLI first |
| Proxy starts but DeepSeek calls fail | Wrong model slug format | Use `deepseek/deepseek-v4-flash` (provider prefix is required) |
| Aliases not found | Shell not reloaded | Run `source ~/.zshrc` or open a new terminal |
| `fcc-run` not found | Alias not in shell profile | Check `~/.zshrc` contains the alias line, then `source ~/.zshrc` |

---

## Summary of Files Created

| File | Purpose |
|---|---|
| `free-claude-code/.env` | Project-level environment config (DeepSeek key, model, port) |
| `~/.fcc/.env` | Managed proxy config (same settings, loaded at runtime) |
| `free-claude-code/start-deepseek.sh` | Launcher for Claude Code → proxy → DeepSeek |
| `free-claude-code/start-native-claude.sh` | Launcher for native Claude Code (no proxy) |
| `~/.zshrc` (appended) | Shell aliases for `fcc-run`, `claude-cheap`, `claude-pro` |

## Dual Workflow — Quick Reference

```
┌───────────────────────────────────────────────────────┐
│  Task Type              │  Command       │  Backend   │
├──────────────────────────┼────────────────┼────────────┤
│  Scripts, tests,         │  claude-cheap  │  DeepSeek  │
│  automations, simple     │                │  (cheap)   │
│  coding                  │                │            │
├──────────────────────────┼────────────────┼────────────┤
│  Architecture, code      │  claude-pro    │  Claude    │
│  review, complex         │                │  (native)  │
│  reasoning, web dev      │                │            │
└───────────────────────────────────────────────────────┘
```

**Workflow checklist:**

1. Start proxy: `fcc-run` (keep running)
2. Cheap work: `claude-cheap` in a new terminal
3. Expensive work: `claude-pro` in a different terminal
4. Stop proxy: `Ctrl+C` in the proxy terminal when done
