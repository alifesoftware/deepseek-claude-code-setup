# Free Claude Code: Architecture Deep Dive
## Slide Content Outline

---

### Slide 1 — Title Slide
**Title:** Free Claude Code
**Subtitle:** Architecture Deep Dive — How a Local Proxy Unlocks Any LLM for Claude Code
**Footer:** Based on github.com/Alishahryar1/free-claude-code · 34k+ Stars · 5.2k Forks

---

### Slide 2 — The Problem: Claude Code Is Locked to Anthropic
**Heading:** Claude Code Only Speaks Anthropic — And That's Expensive

**Body:**
Claude Code (Anthropic's agentic coding CLI) is hardwired to call the Anthropic Messages API. It sends structured JSON payloads with Anthropic-specific fields like `thinking`, `context_management`, and block-based content arrays. While many providers (DeepSeek, OpenRouter, Kimi, etc.) offer Anthropic-compatible endpoints, pointing Claude Code directly at them fails in practice because:
- Providers reject unknown fields like `context_management` with HTTP 400 errors
- Reasoning/thinking blocks are formatted differently across providers
- OpenAI-style providers don't support the Anthropic Messages protocol at all
- Claude Code makes many "background" API calls (quota probes, title generation) that waste tokens and hit rate limits

**Key Insight:** A direct base URL override is not enough — Claude Code needs a smart, protocol-aware intermediary.

---

### Slide 3 — The Solution: A Local Protocol-Aware Proxy
**Heading:** Free Claude Code Sits Between Claude Code and Any LLM Provider

**Body:**
Free Claude Code is a local FastAPI/Uvicorn ASGI server (default port 8082) that:
1. Presents a perfect Anthropic Messages API surface to Claude Code
2. Translates requests to the format required by 17 different upstream providers
3. Translates responses back into the exact SSE format Claude Code expects
4. Short-circuits wasteful background requests locally without hitting any provider

The proxy is installed as a Python tool (`uv tool install`) and exposes two commands: `fcc-server` (starts the proxy) and `fcc-claude` (launches the real `claude` binary with the proxy configured).

**Visual suggestion:** A simple left-to-right flow diagram: `Claude Code CLI → fcc-claude wrapper → Local Proxy (port 8082) → [Provider A / Provider B / Provider C]`

---

### Slide 4 — The Two Transport Paths
**Heading:** Providers Fall Into Two Transport Categories: Native Anthropic vs. OpenAI Chat

**Body:**
The `provider_catalog.py` defines every provider's transport type. This single field determines the entire translation pipeline for a request.

| Transport Type | Providers | Protocol |
|---|---|---|
| `anthropic_messages` | DeepSeek, OpenRouter, Kimi, Wafer, Z.ai, Fireworks, LM Studio, llama.cpp, Ollama | Native Anthropic `/v1/messages` |
| `openai_chat` | NVIDIA NIM, Mistral, Groq, Cerebras, Gemini, OpenCode Zen/Go | OpenAI `/v1/chat/completions` |

For `anthropic_messages` providers, the proxy acts as a thin relay — it sanitizes the request (stripping unsupported fields) and forwards it. For `openai_chat` providers, it performs a full bidirectional protocol translation.

---

### Slide 5 — Request Lifecycle: Step by Step
**Heading:** Every Request Passes Through Five Distinct Stages

**Body:**
1. **Ingress:** `fcc-claude` sets `ANTHROPIC_BASE_URL=http://127.0.0.1:8082` and launches `claude`. All Claude Code API calls land on the local FastAPI server.
2. **Model Routing:** The `ModelRouter` inspects the `model` field in the request. It resolves `claude-opus-*` → `MODEL_OPUS`, `claude-sonnet-*` → `MODEL_SONNET`, `claude-haiku-*` → `MODEL_HAIKU`, and everything else → `MODEL` (the fallback). Each tier can point to a different provider.
3. **Optimization Check:** Before touching any provider, the `optimization_handlers` pipeline runs. If the request matches a known background pattern (quota probe, title generation, etc.), a synthetic response is returned immediately — zero network calls.
4. **Provider Translation:** The resolved provider's adapter builds the upstream request body (either native Anthropic or OpenAI format) and opens a streaming HTTP connection to the provider.
5. **SSE Re-streaming:** The provider's streaming response is parsed and re-emitted as Anthropic-format SSE events back to Claude Code.

---

### Slide 6 — The Model Router: Per-Tier Provider Dispatch
**Heading:** Opus, Sonnet, and Haiku Can Each Route to a Different Provider

**Body:**
The `ModelRouter` in `api/model_router.py` resolves incoming Claude model names using a three-level lookup:

1. **Gateway Model ID Decode:** If the model string is a gateway-encoded ID (e.g., `anthropic/deepseek/deepseek-chat`), it is decoded directly to a provider ID and model name. This is how the `/model` picker in Claude Code works — the proxy advertises its own model list via `/v1/models`.
2. **Direct Provider Prefix:** If the model string contains a known provider prefix (e.g., `deepseek/deepseek-chat`), it is routed directly.
3. **Settings Fallback:** Otherwise, the model name is matched against the configured `MODEL_OPUS`, `MODEL_SONNET`, `MODEL_HAIKU`, or `MODEL` environment variables.

This means you can run DeepSeek for heavy reasoning (Opus), Groq for fast responses (Haiku), and NVIDIA NIM for standard coding (Sonnet) — all simultaneously.

---

### Slide 7 — The Optimization Pipeline: Saving Tokens on Background Noise
**Heading:** Five Fast-Path Handlers Short-Circuit Claude Code's Background API Calls

**Body:**
Claude Code makes many API calls that have nothing to do with actual coding. The `optimization_handlers.py` module intercepts these before they reach any provider:

| Handler | Detection Logic | Synthetic Response |
|---|---|---|
| **Quota Mock** | `max_tokens=1` + message contains "quota" | `"Quota check passed."` |
| **Title Skip** | System prompt contains "sentence-case title" or "return json" + "title" field | `"Conversation"` |
| **Prefix Detection** | Message contains `<policy_spec>` + `Command:` section | Regex-extracted command prefix |
| **Suggestion Skip** | Message contains `[SUGGESTION MODE:` | Empty string |
| **Filepath Mock** | Message contains `Command:` + `Output:` + filepath keywords | Regex-extracted file paths |

These optimizations are checked in order from cheapest to most expensive. A matched handler returns a fully-formed `MessagesResponse` object instantly, without any network I/O.

---

### Slide 8 — The Anthropic-to-OpenAI Converter: The Hardest Problem
**Heading:** Translating Anthropic's Block Format to OpenAI's Message Format Requires a State Machine

**Body:**
The `AnthropicToOpenAIConverter` in `core/anthropic/conversion.py` handles the most complex translation challenge: Anthropic and OpenAI have fundamentally different message schemas.

Key translation challenges solved:
- **Tool Use After Text:** Anthropic allows text blocks after `tool_use` blocks in a single assistant message. OpenAI does not. The converter uses a `_PendingAfterTools` state machine to defer post-tool text until the corresponding `role: tool` results have been replayed.
- **Reasoning Replay:** Anthropic thinking blocks are replayed to OpenAI providers either as `<think>...</think>` tags prepended to the assistant message, or as `reasoning_content` fields, depending on the provider.
- **Unknown Top-Level Fields:** Fields like `context_management` are silently stripped. Truly unknown extra fields raise an `OpenAIConversionError` before the request is sent.
- **Image Blocks in Assistant Messages:** These are rejected with a clear error, as OpenAI chat does not support them.

---

### Slide 9 — SSE Re-streaming: Translating the Response Back
**Heading:** The Proxy Re-Emits Every Provider's Response as Anthropic-Format SSE

**Body:**
Claude Code expects a very specific Server-Sent Events stream format. For OpenAI-style providers, the `OpenAIChatTransport` base class in `providers/openai_compat.py` handles the reverse translation:

- OpenAI's `delta.content` text chunks → Anthropic `content_block_delta` SSE events
- OpenAI's `delta.tool_calls` → Anthropic `content_block_start` (tool_use) + `content_block_delta` (input_json_delta) events
- OpenAI's `finish_reason` → Anthropic `stop_reason` (mapped via `map_stop_reason`)
- Provider-specific `reasoning_content` or `<think>` tags → Anthropic `thinking` content blocks

The `SSEBuilder` class manages block indices and ensures the event stream is well-formed. It also handles the `Task` tool specially — buffering its arguments and forcing `run_in_background: false` to prevent runaway background agents.

---

### Slide 10 — Stream Recovery: Handling Truncated Provider Responses
**Heading:** The Proxy Automatically Retries and Repairs Truncated or Malformed Streams

**Body:**
Real-world LLM APIs frequently truncate streams mid-response. Free Claude Code implements a multi-stage recovery system in `core/anthropic/stream_recovery.py`:

- **Early Transparent Retries:** If a stream fails before any content has been emitted to the client, the proxy transparently retries up to 3 times with the same request body.
- **Mid-stream Recovery:** If a stream truncates after content has been emitted, the proxy can attempt continuation by sending a follow-up request with a `continuation_suffix` appended to the last assistant message.
- **Tool JSON Repair:** If a tool call's JSON arguments are truncated, the proxy attempts to repair the JSON before emitting the `content_block_stop` event, preventing Claude Code from crashing on malformed tool input.

This recovery layer is invisible to Claude Code — it always receives a complete, well-formed response.

---

### Slide 11 — The `/v1/models` Endpoint: Native Model Picker Support
**Heading:** The Proxy Advertises a Dynamic Model List That Powers Claude Code's /model Command

**Body:**
Claude Code has an interactive `/model` picker. For this to work with non-Anthropic models, the proxy's `/v1/models` endpoint returns a carefully constructed list:

1. **Gateway-encoded provider models:** All configured models are advertised as `anthropic/{provider_id}/{model_id}` (with thinking enabled) and `claude-3-freecc-no-thinking/{provider_id}/{model_id}` (without thinking). The `claude-3-` prefix in the no-thinking variant exploits Claude Code's client-side heuristic that treats `claude-3-*` models as not supporting thinking.
2. **Provider-discovered models:** On startup, the proxy queries each configured provider's `/models` endpoint and caches the results. These are also added to the list with the same gateway encoding.
3. **Standard Claude models:** The canonical Claude model IDs (e.g., `claude-3-5-sonnet-20241022`) are always included as fallback entries.

---

### Slide 12 — Architecture Summary
**Heading:** Free Claude Code Is a Full Protocol Translation Layer, Not Just a URL Forwarder

**Body:**
The complete architecture can be summarized in four layers:

| Layer | Component | Responsibility |
|---|---|---|
| **Entry** | `fcc-claude` wrapper | Sets env vars, launches `claude` binary |
| **Gateway** | FastAPI ASGI server | Exposes Anthropic API surface, auth, routing |
| **Intelligence** | ModelRouter + OptimizationHandlers | Per-tier routing, token-saving short-circuits |
| **Translation** | AnthropicToOpenAI / AnthropicMessages transports | Bidirectional protocol conversion, SSE re-streaming, stream recovery |

**Why this matters:** Every layer adds value that a raw base URL override cannot provide. The proxy is not a simple forwarder — it is a stateful, protocol-aware translation engine that makes Claude Code's full feature set (thinking, tool use, model picker, token counting) work correctly with any LLM provider.

---

### Slide 13 — Supported Providers at a Glance
**Heading:** 17 Providers Span Free Tiers, Paid APIs, and Local Models

**Body:**
| Provider | Transport | Notable Feature |
|---|---|---|
| NVIDIA NIM | OpenAI Chat | Default provider; Nemotron-3-Super-120B |
| OpenRouter | Anthropic Messages | Access to 300+ models via one key |
| Google Gemini | OpenAI Chat | Free tier via AI Studio |
| DeepSeek | Anthropic Messages | Native Anthropic endpoint |
| Mistral / Codestral | OpenAI Chat | Free "Experiment" tier |
| OpenCode Zen / Go | OpenAI Chat | Curated multi-vendor gateway |
| Wafer | Anthropic Messages | Native Anthropic endpoint |
| Kimi (Moonshot) | Anthropic Messages | Native Anthropic endpoint |
| Cerebras | OpenAI Chat | Ultra-fast inference |
| Groq | OpenAI Chat | Ultra-fast inference |
| Fireworks AI | Anthropic Messages | Native Anthropic endpoint |
| Z.ai | Anthropic Messages | Native Anthropic endpoint |
| LM Studio / llama.cpp / Ollama | Anthropic Messages | Fully local, no API key needed |

---

### Slide 14 — Conclusion
**Heading:** Free Claude Code Makes Claude Code Provider-Agnostic Without Sacrificing Functionality

**Body:**
Free Claude Code is not a simple reverse proxy. It is a purpose-built protocol translation engine that:
- Maintains a stable Anthropic API surface for Claude Code regardless of the upstream provider
- Eliminates wasted API calls through intelligent request detection and local short-circuiting
- Handles the full complexity of Anthropic ↔ OpenAI format conversion including tool use, reasoning blocks, and streaming
- Provides automatic stream recovery and JSON repair for resilient operation
- Supports 17 providers across free, paid, and local tiers with per-model routing

The result is that Claude Code's full feature set — thinking, tool use, the `/model` picker, token counting, and streaming — works correctly with any supported LLM, not just Anthropic's own models.

**Repository:** github.com/Alishahryar1/free-claude-code
