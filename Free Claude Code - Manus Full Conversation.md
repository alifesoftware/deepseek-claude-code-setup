# Free Claude Code — Full Conversation Backup

**Date:** June 14, 2026  
**Topic:** Analyzing free-claude-code, adding Xiaomi MiMo provider, tests, README, and PR guidance

---

## 1. How free-claude-code Works

**User:** Look at this code repo: https://github.com/Alishahryar1/free-claude-code. With free-claude-code, I can use DeepSeek and other model providers with Claude Code. I want to tell me precisely how it works, and why is it better than using DeepSeek's or other model's Anthropic style base URL directly in Claude Code settings?

**Assistant summary:**

The repository is a local Python proxy (FastAPI + uvicorn) that sits between Claude Code and any downstream LLM provider. It exposes a fully Anthropic-compatible API surface at `http://localhost:8082` so Claude Code never needs to know it is talking to anything other than Anthropic.

### Five-Layer Architecture

**Layer 1 — Anthropic-Compatible API Surface**  
FastAPI exposes `/v1/messages`, `/v1/messages/count_tokens`, and `/v1/models`. Claude Code connects to `http://localhost:8082` via `ANTHROPIC_BASE_URL`. The proxy accepts the full Anthropic Messages API schema including streaming, tool use, thinking blocks, and system prompts.

**Layer 2 — Request Optimization (Detection + Interception)**  
`api/detection.py` classifies every incoming request as one of several Claude Code internal probe types: `SYSTEM_PROMPT_DETECT`, `TOOL_CALL_DETECT`, `COMPACT_DETECT`, `SMALL_FAST_DETECT`, etc. Recognized probes are answered locally with pre-baked responses — no upstream call is made. This saves quota and latency for the dozens of background health-check and capability-detection requests Claude Code fires on startup.

**Layer 3 — Model Router**  
`api/model_router.py` maps the incoming Claude model name (e.g. `claude-opus-4-5`) to a configured provider slug (e.g. `deepseek/deepseek-r1`) using the `MODEL_OPUS`, `MODEL_SONNET`, `MODEL_HAIKU`, and `MODEL` environment variables. The router selects the correct provider transport from the registry.

**Layer 4 — Provider Transport**  
Two base transport classes handle the actual upstream call:
- `AnthropicMessagesTransport` — for providers with a native Anthropic-compatible endpoint (DeepSeek, Kimi, Fireworks, MiMo, etc.). Sends the request body almost as-is, with provider-specific header and URL adjustments.
- `OpenAIChatTransport` — for OpenAI-format providers (NVIDIA NIM, OpenRouter, Gemini, etc.). Converts the Anthropic request body to OpenAI chat completions format, calls the upstream, then converts the OpenAI SSE stream back to Anthropic SSE format.

**Layer 5 — SSE Re-streaming and Error Normalization**  
The proxy re-streams the upstream SSE response to Claude Code, normalizing thinking blocks, tool call deltas, token usage metadata, and provider error codes into the exact shape Claude Code expects.

### Why It Is Better Than a Direct Base URL Override

| Dimension | Direct base URL override | free-claude-code proxy |
|---|---|---|
| Request optimization | None — every probe hits the provider | Local interception saves quota and latency |
| Protocol translation | Only works if the provider is 100% Anthropic-compatible | Full conversion layer for OpenAI-format providers |
| Multi-provider routing | One provider only | Per-tier routing (Opus/Sonnet/Haiku to different providers) |
| Header normalization | Raw passthrough — auth header mismatches cause 401s | Provider-specific header builders per transport |
| Model list endpoint | Provider's `/models` path (often different from Anthropic's) | Unified `/v1/models` with per-provider path overrides |
| Thinking block handling | Provider must support it natively | Normalized across all providers |
| Error mapping | Raw provider errors reach Claude Code | Mapped to Anthropic error shapes |
| Admin UI | None | Web UI to configure keys, models, and smoke-test providers |

---

## 2. Presentation

**User:** Generate a presentation about the free-claude-code architecture.

**Assistant:** Generated a 12-slide presentation covering the full architecture. Slides include: title, problem statement, the five transport layers, request lifecycle, model router, optimization pipeline, Anthropic↔OpenAI converter, SSE re-streaming, stream recovery, `/v1/models` endpoint, supported providers (17), and architecture summary.

**Slide deck URI:** `manus-slides://31amnl9CccKQeYgh549AX5`

---

## 3. Architecture Webpage

**User:** Create a webpage explaining the Free Claude Code architecture.

**Assistant:** Built a static React + Tailwind 4 single-page site (`fcc-architecture-web`) with a dark technical documentation aesthetic (Space Grotesk headings, JetBrains Mono code, `#ff5722` orange accent). The page has a sticky table of contents and 13 content sections covering every layer of the proxy.

**Checkpoint:** `manus-webdev://fc921710`

---

## 4. Adding Xiaomi MiMo Provider

**User:** I want to add Xiaomi MiMo, Pay-As-You-Go Plan, link: https://mimo.mi.com/docs/en-US/tokenplan/integration/tools-overview

### Files Changed (8 existing + 3 new)

**New files — `providers/xiaomimimo/`**

| File | Purpose |
|---|---|
| `__init__.py` | Package export — re-exports `XiaomiMiMoProvider` and `XIAOMIMIMO_DEFAULT_BASE` |
| `client.py` | `XiaomiMiMoProvider` — subclasses `AnthropicMessagesTransport`, sets base URL `https://api.xiaomimimo.com/anthropic/v1`, sends `Authorization: Bearer` + `anthropic-version: 2023-06-01` headers; overrides `_send_model_list_request` to call `/v1/models` via `copy_with` |
| `request.py` | Request body builder — delegates to `build_base_native_anthropic_request_body`, respects thinking toggle, forces `stream: true`, passes `extra_body` through |

**Modified files**

| File | What changed |
|---|---|
| `config/provider_catalog.py` | Added `XIAOMIMIMO_DEFAULT_BASE` constant and full `ProviderDescriptor` entry |
| `config/settings.py` | Added `xiaomimimo_api_key` and `xiaomimimo_proxy` fields |
| `providers/defaults.py` | Added `XIAOMIMIMO_DEFAULT_BASE` to re-export |
| `providers/registry.py` | Added `_create_xiaomimimo` factory and registered it in `PROVIDER_FACTORIES` |
| `api/admin_config.py` | Added `XIAOMIMIMO_API_KEY`, `XIAOMIMIMO_PROXY`, and `FCC_SMOKE_MODEL_XIAOMIMIMO` fields |
| `api/admin_static/admin.js` | Added `xiaomimimo: "Xiaomi MiMo"` to `providerName()` display map |
| `tests/providers/test_registry.py` | Added MiMo mock attrs, import, and test case |

**Patch v1:** `fcc-mimo-patch.zip`

---

## 5. DeepSeek Comparison

**User:** Does this architecture and changes kinda sorta mirror what we have for Deepseek? Can you verify.

**Assistant:** MiMo mirrors **Fireworks and Kimi**, not DeepSeek. DeepSeek is a special case.

**Where MiMo mirrors DeepSeek:**
- Both use `AnthropicMessagesTransport`
- Both have `transport_type = "anthropic_messages"`
- Both have identical capabilities tuple
- Both use the same registry factory pattern and settings field style

**Where MiMo correctly diverges from DeepSeek:**

1. **Auth header** — DeepSeek uses `x-api-key` (non-standard, no `anthropic-version`). MiMo uses `Authorization: Bearer` + `anthropic-version: 2023-06-01` (standard Anthropic convention, same as Kimi and Fireworks).

2. **Base URL** — DeepSeek uses `/anthropic` (no `/v1`). MiMo uses `/anthropic/v1` (same as Kimi's `api.moonshot.ai/anthropic/v1`).

3. **Request builder** — DeepSeek has a 475-line builder with complex thinking/tool_choice downgrade logic. MiMo uses a 48-line builder delegating to `build_base_native_anthropic_request_body` (same as Fireworks and Kimi).

4. **Proxy support** — DeepSeek has no proxy field. MiMo has `proxy_attr="xiaomimimo_proxy"` (consistent with Kimi and Fireworks).

**The correct reference model for MiMo is Fireworks, not DeepSeek.**

---

## 6. Models Endpoint Investigation

**User:** Investigate if MiMo's /models endpoint is at `https://api.xiaomimimo.com/v1/models` and if a `_send_model_list_request` override is needed.

**Finding:**

```
GET https://api.xiaomimimo.com/anthropic/v1/models  →  HTTP 404
GET https://api.xiaomimimo.com/v1/models            →  HTTP 401 (auth-gated, path exists)
```

The `/anthropic/v1` prefix is a routing namespace for the Messages API only. The model list lives at the OpenAI-format root `/v1/models`, exactly like DeepSeek (`/models` vs `/anthropic`).

**Fix applied to `client.py`:**

```python
async def _send_model_list_request(self) -> httpx.Response:
    """MiMo lists models from the OpenAI-format root (/v1/models), not /anthropic/v1/models."""
    url = str(
        httpx.URL(self._base_url).copy_with(
            path="/v1/models", query=None, fragment=None
        )
    )
    return await self._client.get(url, headers=self._model_list_headers())
```

**Patch v2:** `fcc-mimo-patch-v2.zip`

---

## 7. Base URL Bug Fix (HTTP 404 on Messages)

**User reported error:**
```
XIAOMIMIMO_ERROR: HTTP 404 error_body_bytes_read=150
Upstream error: <html><head><title>404 Not Found</title></head>...openresty
```

**Root cause:** Base URL was `https://api.xiaomimimo.com/anthropic`. httpx resolved `POST /messages` to `https://api.xiaomimimo.com/anthropic/messages` — HTTP 404. The correct messages endpoint is `https://api.xiaomimimo.com/anthropic/v1/messages`.

**Fix — one constant change in `config/provider_catalog.py`:**

```python
# Before (broken)
XIAOMIMIMO_DEFAULT_BASE = "https://api.xiaomimimo.com/anthropic"

# After (correct)
XIAOMIMIMO_DEFAULT_BASE = "https://api.xiaomimimo.com/anthropic/v1"
```

With `/anthropic/v1` as the base:
- `POST /messages` → `https://api.xiaomimimo.com/anthropic/v1/messages` ✓
- `GET /v1/models` (via `copy_with` override) → `https://api.xiaomimimo.com/v1/models` ✓

**Patch v3:** `fcc-mimo-patch-v3.zip`

---

## 8. README Update

**User:** I think it would be good if we can update the README.MD as well.

**Four changes applied:**

| # | Location | Change |
|---|---|---|
| 1 | Line 46 — "What You Get" | `17` → `18`, `Xiaomi MiMo` added before LM Studio |
| 2 | After Ollama (§17) | New `### 18. [Xiaomi MiMo]` section with key setup, model slugs, endpoint note, Token Plan note, and docs link |
| 3 | Former §18 heading | `### 18. Mix Providers By Model Tier` → `### 19. Mix Providers By Model Tier` |
| 4 | Line 472 — "How It Works" | `Xiaomi MiMo` added to the Anthropic Messages transport list |

---

## 9. Provider Tests

**User:** /tests/providers has tests for all providers, but we do not have one for xiaomi.

**Created:** `tests/providers/test_xiaomimimo.py` — 13 tests, all passing.

| Test | What it verifies |
|---|---|
| `test_default_base_url_constant` | Constant is exactly `https://api.xiaomimimo.com/anthropic/v1` |
| `test_init` | Provider stores API key and base URL correctly |
| `test_request_headers_bearer_auth` | Auth is `Authorization: Bearer`, `anthropic-version` present, `x-api-key` absent |
| `test_model_list_headers` | Model list call uses `Authorization: Bearer` |
| `test_build_request_body_native_shape` | Model, stream, max_tokens, system, messages round-trip correctly |
| `test_build_request_body_default_max_tokens` | Falls back to `ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS` when omitted |
| `test_build_request_body_thinking_enabled` | Thinking block passes through; no `extra_body` leaks |
| `test_build_request_body_global_disable_blocks_thinking` | `enable_thinking=False` strips thinking even if request asks for it |
| `test_build_request_body_merges_safe_extra_body` | `extra_body` is merged (pass-through like Fireworks) |
| `test_build_request_body_rejects_reserved_extra_body_keys` | Reserved keys in `extra_body` raise `InvalidRequestError` |
| `test_stream_uses_post_messages_path` | Streaming POST resolves to `/anthropic/v1/messages` |
| `test_model_list_uses_v1_models_root_url` | Model list GET resolves to `https://api.xiaomimimo.com/v1/models` |
| `test_cleanup_aclose` | `cleanup()` calls `aclose()` on httpx client |

---

## 10. How to Test Locally

```bash
# 1. Clone and enter the repo
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code

# 2. Apply the patch (unzip fcc-mimo-patch-v4.zip into repo root)
unzip -o /path/to/fcc-mimo-patch-v4.zip -d .

# 3. Create venv with Python 3.14
uv sync

# 4. Run MiMo tests only
uv run pytest tests/providers/test_xiaomimimo.py -v
# Expected: 13 passed

# 5. Run full test suite
uv run pytest tests/providers/ -v
# Expected: 534 passed

# 6. Full check sequence (before PR)
uv run ruff format
uv run ruff check
uv run ty check
uv run pytest
```

---

## 11. Contract Test Fix

**User reported failure:**
```
FAILED tests/contracts/test_provider_catalog_order.py::test_provider_catalog_key_order_matches_canonical_plan
AssertionError: Left contains one more item: 'xiaomimimo'
```

**Fix:** Added `"xiaomimimo"` to `_EXPECTED_PROVIDER_ORDER` tuple in `tests/contracts/test_provider_catalog_order.py`.

```python
# before
    "ollama",
)

# after
    "ollama",
    "xiaomimimo",
)
```

Result: **28/28 targeted tests pass. 1498/1498 total tests pass.**

---

## 12. PR Submission Guide

**User:** How can I submit a PR to this repository?

**Steps:**

1. Fork `https://github.com/Alishahryar1/free-claude-code` on GitHub
2. Clone your fork: `git clone https://github.com/<your-username>/free-claude-code.git`
3. Add upstream: `git remote add upstream https://github.com/Alishahryar1/free-claude-code.git`
4. Create branch: `git checkout -b feat/xiaomimimo-provider`
5. Apply patch files from `fcc-mimo-patch-v4.zip`
6. Run full check sequence: `uv run ruff format && uv run ruff check && uv run ty check && uv run pytest`
7. Commit and push, then open PR on GitHub

**PR title:** `feat: add Xiaomi MiMo Pay-As-You-Go provider`

**Note from repo contributing guide:** Do not open README-only change PRs. Since the README change is part of a functional provider addition, it is appropriate to include it. If the maintainer asks to drop it, revert those lines and push to the same branch.

---

## 13. Patch Version History

| Version | Contents | Key change |
|---|---|---|
| `fcc-mimo-patch.zip` (v1) | Initial provider implementation | First working implementation |
| `fcc-mimo-patch-v2.zip` | + `_send_model_list_request` override | Fixed `/v1/models` path |
| `fcc-mimo-patch-v3.zip` | + Base URL fix to `/anthropic/v1` | Fixed HTTP 404 on messages |
| `fcc-mimo-patch-v4.zip` | + `test_xiaomimimo.py` + README + contract test fix | Complete, all tests passing |

---

## 14. Environment Variable Reference

| Variable | Required | Default | Notes |
|---|---|---|---|
| `XIAOMIMIMO_API_KEY` | Yes | — | Pay-As-You-Go key from `platform.xiaomimimo.com/console/api-keys` |
| `XIAOMIMIMO_PROXY` | No | (empty) | HTTP/SOCKS proxy; leave blank if accessing from outside China via Pay-As-You-Go |
| `MODEL` / `MODEL_SONNET` etc. | Yes | — | Set to e.g. `xiaomimimo/mimo-v2.5-pro` |

**Token Plan subscribers:** The base URL must be overridden to `https://token-plan-cn.xiaomimimo.com/anthropic/v1`.

---

*End of conversation backup — June 14, 2026*
