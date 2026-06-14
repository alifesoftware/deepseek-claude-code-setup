# Technical Analysis: Free Claude Code vs. Direct Anthropic Base URL

The [free-claude-code](https://github.com/Alishahryar1/free-claude-code) repository by Alishahryar1 provides a sophisticated drop-in proxy designed specifically for Anthropic's new "Claude Code" CLI. While many model providers (like DeepSeek, OpenRouter, or Kimi) offer Anthropic-compatible endpoints that could theoretically be plugged directly into Claude Code, doing so directly often leads to broken functionality, rejected requests, or suboptimal behavior.

Free Claude Code solves this by acting as a middleman that understands the exact client-side protocol of Claude Code and translates it dynamically for 17 different model providers.

Here is a precise technical breakdown of how it works and why it is superior to using a direct base URL override.

## How Free Claude Code Works

Free Claude Code operates as a local ASGI web server (built with FastAPI and Uvicorn) running on your machine (default port 8082). It intercepts traffic from the `claude` CLI and routes it to upstream LLM providers. 

The architecture consists of three main components:

### 1. The Interceptor (`fcc-claude` wrapper)
Instead of running `claude` directly, users run `fcc-claude`. This script reads the proxy's configuration, sets up the necessary environment variables (like `ANTHROPIC_BASE_URL` and custom auth tokens), and then launches the real `claude` binary. It forces Claude Code to send all its Anthropic Messages API traffic to the local proxy [1].

### 2. The Model Router & API Gateway
The FastAPI application exposes standard Anthropic endpoints (`/v1/messages`, `/v1/models`, `/v1/messages/count_tokens`). 
When Claude Code queries `/v1/models` to populate its interactive model picker, the proxy dynamically generates a list of models combining the configured fallback models, provider-specific models (e.g., `deepseek/deepseek-chat`), and standard Claude models [2].

When a chat request arrives, the `ModelRouter` inspects the requested model string. It supports per-model routing, meaning you can configure it to send Opus-tier tasks to one provider, Sonnet-tier tasks to another, and Haiku-tier tasks to a third [3].

### 3. The Provider Translation Layer
The core of the proxy is its provider registry. It categorizes providers into two transport types [4]:
* **`anthropic_messages`**: Providers that natively support the Anthropic API (e.g., DeepSeek, OpenRouter, Kimi).
* **`openai_chat`**: Providers that only support the OpenAI `/v1/chat/completions` API (e.g., NVIDIA NIM, Mistral, Groq).

For OpenAI-style providers, the proxy uses a sophisticated `AnthropicToOpenAIConverter` [5]. It translates Anthropic's block-based content format, tool schemas, and tool-use blocks into OpenAI's format. Crucially, it handles the complex state machine of translating Anthropic's Server-Sent Events (SSE) stream back into the exact chunk format Claude Code expects.

## Why It Is Better Than Direct Base URL Overrides

Simply pointing Claude Code's `ANTHROPIC_BASE_URL` to a provider like `https://api.deepseek.com/anthropic` often fails in subtle ways. Free Claude Code fixes these protocol mismatches.

### 1. Handling "Thinking" and Reasoning Blocks
Claude Code relies heavily on Claude 3.7's "thinking" capabilities. However, different providers implement reasoning differently:
* Anthropic expects reasoning in a specific SSE block format.
* OpenAI-compatible providers might use a `reasoning_content` field or wrap reasoning in `<think>` tags.
* Some providers reject requests if the `thinking` parameter is passed but not supported by the model.

The proxy's `AnthropicToOpenAIConverter` intercepts reasoning blocks. Depending on the provider, it strips unsupported thinking parameters, translates `<think>` tags into proper Anthropic thinking blocks, or maps `reasoning_content` correctly so Claude Code can display the thinking process natively [5].

### 2. Fast-Path Optimizations (Short-Circuiting)
Claude Code makes many rapid, "hidden" API calls that consume tokens and rate limits. Free Claude Code implements specific `optimization_handlers` [6] to intercept and mock these requests without ever hitting the upstream provider:
* **Quota Probes:** Claude Code sends dummy requests to check if the API is alive. The proxy intercepts these and instantly returns a 200 OK.
* **Title Generation:** Claude Code asks the LLM to generate a title for the session. The proxy skips the LLM call and instantly returns "Conversation".
* **Prefix Detection & Filepath Extraction:** Claude Code uses the LLM to parse command outputs for file paths. The proxy uses local regex/heuristics to extract filepaths instantly, saving tokens and latency.

### 3. Strict Top-Level Field Stripping
Claude Code sends internal, first-class fields (like `context_management`) in its JSON payload. If you send these directly to DeepSeek or OpenRouter, their API gateways will often reject the request with a `400 Bad Request` because they don't recognize the extra fields. Free Claude Code sanitizes the payload, stripping out Claude-specific internal fields before forwarding the request to the provider [5].

### 4. Tool Use and "Pending After Tools" State Machine
OpenAI's `chat.completions` API has strict rules about message ordering: it cannot place assistant text after `tool_calls` in the same message. Anthropic allows this. If Claude Code sends an Anthropic-style message with text after a tool call, a direct OpenAI adapter will crash. The proxy implements a `_PendingAfterTools` state machine [5] that defers the post-tool text until the corresponding `role: tool` results have been replayed in order, preventing the session from getting stuck.

### 5. Multi-Provider Routing and Fallbacks
Direct base URLs lock you into a single provider. Free Claude Code allows you to mix and match. You can use DeepSeek for heavy coding (Sonnet tier), Groq for fast, cheap autocomplete (Haiku tier), and NVIDIA NIM for specific reasoning tasks, all seamlessly routed behind the scenes [3].

## Summary

While you *can* point Claude Code directly at an Anthropic-compatible provider, you will likely encounter broken tool calls, rejected payloads due to unknown fields, and wasted tokens on background tasks. Free Claude Code acts as a protocol-aware firewall that translates dialects, mocks background noise, and keeps the Claude Code CLI stable while utilizing alternative LLMs.

---
### References
[1] `README.md`: fcc-claude CLI wrapper usage.
[2] `api/routes.py`: `/v1/models` endpoint implementation.
[3] `api/model_router.py`: Model routing and resolution logic.
[4] `config/provider_catalog.py`: Provider transport definitions.
[5] `core/anthropic/conversion.py`: AnthropicToOpenAIConverter implementation.
[6] `api/optimization_handlers.py`: Fast-path optimizations for quota, titles, and prefix detection.
