# Set Up Free Claude Code Proxy with DeepSeek + Dual Workflow

## Background

[free-claude-code](file://~/Development/FreeClaudeCodeGodMode/free-claude-code) is an Anthropic-compatible proxy that routes Claude Code API calls to alternative providers. We'll configure it with DeepSeek and create two separate Claude Code workflows.

## Proposed Changes

### Phase 1 — Install Dependencies (Python 3.14 + uv sync)

The project requires **Python 3.14** ([.python-version](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/.python-version)), but the system has Python 3.9.6. `uv` (v0.11.17, already installed) can auto-download and manage Python 3.14.

- Run `uv sync` in the repo — `uv` will automatically download Python 3.14 and install all dependencies from [uv.lock](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/uv.lock).

---

### Phase 2 — Configure Environment for DeepSeek

The managed env file lives at `~/.fcc/.env` ([paths.py](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/config/paths.py#L20-L23)). Settings are loaded from both `.env` (in project dir) and `~/.fcc/.env` (managed path).

> [!IMPORTANT]
> **I need your DeepSeek API key** to complete this step. You mentioned "using my API key" — please provide it, or I'll create the config file with a placeholder you can fill in.

#### [NEW] `~/.fcc/.env`
Create the managed config with:
```env
DEEPSEEK_API_KEY="your-deepseek-api-key-here"
MODEL="deepseek/deepseek-chat"
ANTHROPIC_AUTH_TOKEN="freecc"
MESSAGING_PLATFORM="none"
VOICE_NOTE_ENABLED=false
```

Key decisions:
- **Default model**: `deepseek/deepseek-chat` — routes all Claude model tiers (Opus/Sonnet/Haiku) to DeepSeek's chat model via their Anthropic-compatible endpoint
- **Auth token**: `freecc` (default) — used by Claude Code to authenticate with the proxy
- **Messaging/voice**: disabled (not needed for this use case)

---

### Phase 3 — Verify Proxy Server Starts

Run `uv run uvicorn server:app --host 0.0.0.0 --port 8082` and confirm:
- Server binds to `http://localhost:8082`
- Admin UI accessible at `http://localhost:8082/admin`
- `/health` endpoint returns 200

---

### Phase 4 — Create Dual Workflow Shell Scripts

Two launcher scripts in the repo root for easy switching:

#### [NEW] [start-deepseek.sh](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/start-deepseek.sh)
Launches Claude Code routed through the proxy → DeepSeek:
```bash
#!/bin/bash
# DeepSeek instance — cheap tasks (scripts, tests, tool calling, automations)
export ANTHROPIC_BASE_URL="http://localhost:8082"
export ANTHROPIC_AUTH_TOKEN="freecc"
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="190000"
claude "$@"
```

#### [NEW] [start-native-claude.sh](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/start-native-claude.sh)
Launches Claude Code with your normal Anthropic API key (no proxy):
```bash
#!/bin/bash
# Native Claude instance — expensive tasks (reasoning, web dev, architecture, reviews)
# Uses your real ANTHROPIC_API_KEY from the environment
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY
claude "$@"
```

---

### Phase 5 — Add Shell Aliases (Optional Convenience)

#### [NEW] [setup-aliases.sh](file://~/Development/FreeClaudeCodeGodMode/free-claude-code/setup-aliases.sh)
Adds aliases to `~/.zshrc`:
```bash
alias claude-cheap="source /path/to/start-deepseek.sh"
alias claude-pro="source /path/to/start-native-claude.sh"
```

## Open Questions

> [!IMPORTANT]
> 1. **DeepSeek API Key**: Please provide your DeepSeek API key, or should I leave a placeholder?
> 2. **Shell aliases**: Do you want me to add `claude-cheap` / `claude-pro` aliases to your `~/.zshrc`, or do you prefer just the scripts?
> 3. **Port**: The default is `8082`. Is that fine, or do you have a preference?

## Verification Plan

### Automated Tests
1. `uv sync` completes without errors
2. `uv run python -c "import fastapi; print('OK')"` — confirms dependencies
3. Start the proxy server and hit `curl http://localhost:8082/health` — expect 200
4. Run `uv run pytest` for project test suite (optional)

### Manual Verification
- Start the proxy → run `start-deepseek.sh` → send a test message in Claude Code → confirm response comes from DeepSeek
- Run `start-native-claude.sh` → confirm it uses your native Anthropic API
