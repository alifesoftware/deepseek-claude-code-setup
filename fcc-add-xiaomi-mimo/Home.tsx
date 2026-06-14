import { useEffect, useRef, useState } from "react";

// ─── Section data ──────────────────────────────────────────────────────────────
const TOC = [
  { id: "overview", label: "Overview" },
  { id: "problem", label: "The Problem" },
  { id: "solution", label: "The Solution" },
  { id: "transport", label: "Transport Paths" },
  { id: "lifecycle", label: "Request Lifecycle" },
  { id: "router", label: "Model Router" },
  { id: "optimizations", label: "Optimization Pipeline" },
  { id: "converter", label: "Protocol Converter" },
  { id: "streaming", label: "SSE Re-streaming" },
  { id: "recovery", label: "Stream Recovery" },
  { id: "models", label: "/v1/models Endpoint" },
  { id: "providers", label: "Supported Providers" },
  { id: "mimo", label: "Xiaomi MiMo Spotlight" },
  { id: "summary", label: "Architecture Summary" },
];

// ─── Reusable components ───────────────────────────────────────────────────────
function Code({ children }: { children: React.ReactNode }) {
  return <code className="inline-code">{children}</code>;
}

function SectionHeading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2
      id={id}
      className="text-3xl font-bold mb-6 scroll-mt-24"
      style={{ fontFamily: "var(--font-display)", color: "oklch(0.94 0.005 265)" }}
    >
      {children}
    </h2>
  );
}

function SubHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3
      className="text-xl font-semibold mb-3 mt-8"
      style={{ fontFamily: "var(--font-display)", color: "oklch(0.83 0.15 200)" }}
    >
      {children}
    </h3>
  );
}

function Prose({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <p
      className={`text-base leading-relaxed mb-4 ${className}`}
      style={{ color: "oklch(0.75 0.01 265)", lineHeight: "1.75" }}
    >
      {children}
    </p>
  );
}

function Tag({ children, color = "orange" }: { children: React.ReactNode; color?: "orange" | "cyan" | "muted" }) {
  const colors = {
    orange: "oklch(0.62 0.21 38)",
    cyan: "oklch(0.83 0.15 200)",
    muted: "oklch(0.55 0.015 265)",
  };
  return (
    <span
      className="text-xs font-bold uppercase tracking-widest px-2 py-1 rounded"
      style={{
        fontFamily: "var(--font-mono)",
        color: colors[color],
        background: `${colors[color]}18`,
        border: `1px solid ${colors[color]}30`,
      }}
    >
      {children}
    </span>
  );
}

function FlowBox({
  number,
  title,
  description,
  accent = false,
}: {
  number: string;
  title: string;
  description: string;
  accent?: boolean;
}) {
  return (
    <div
      className="flex gap-4 p-5 rounded-lg"
      style={{
        background: accent ? "oklch(0.62 0.21 38 / 0.08)" : "oklch(0.14 0.015 265)",
        border: `1px solid ${accent ? "oklch(0.62 0.21 38 / 0.3)" : "oklch(0.22 0.015 265)"}`,
      }}
    >
      <div
        className="text-2xl font-bold shrink-0 w-10 h-10 flex items-center justify-center rounded"
        style={{
          fontFamily: "var(--font-mono)",
          color: "oklch(0.62 0.21 38)",
          background: "oklch(0.62 0.21 38 / 0.12)",
        }}
      >
        {number}
      </div>
      <div>
        <div
          className="font-semibold mb-1"
          style={{ fontFamily: "var(--font-display)", color: "oklch(0.94 0.005 265)" }}
        >
          {title}
        </div>
        <div className="text-sm leading-relaxed" style={{ color: "oklch(0.65 0.01 265)" }}>
          {description}
        </div>
      </div>
    </div>
  );
}

function DataRow({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div
      className="flex items-start gap-4 py-3 border-b"
      style={{ borderColor: "oklch(0.22 0.015 265)" }}
    >
      <div
        className="w-44 shrink-0 text-sm font-semibold"
        style={{ fontFamily: "var(--font-mono)", color: "oklch(0.62 0.21 38)" }}
      >
        {label}
      </div>
      <div className="flex-1">
        <div className="text-sm" style={{ color: "oklch(0.85 0.005 265)" }}>
          {value}
        </div>
        {note && (
          <div className="text-xs mt-0.5" style={{ color: "oklch(0.55 0.015 265)" }}>
            {note}
          </div>
        )}
      </div>
    </div>
  );
}

function MapRow({ from, to }: { from: string; to: string }) {
  return (
    <div
      className="grid gap-3 py-3 border-b items-center"
      style={{ borderColor: "oklch(0.22 0.015 265)", gridTemplateColumns: "1fr auto 1fr" }}
    >
      <div
        className="text-sm px-3 py-2 rounded font-medium"
        style={{
          fontFamily: "var(--font-mono)",
          background: "oklch(0.16 0.015 265)",
          color: "oklch(0.75 0.01 265)",
          border: "1px solid oklch(0.22 0.015 265)",
        }}
      >
        {from}
      </div>
      <div style={{ color: "oklch(0.62 0.21 38)", fontFamily: "var(--font-mono)", fontWeight: 700 }}>→</div>
      <div
        className="text-sm px-3 py-2 rounded font-medium"
        style={{
          fontFamily: "var(--font-mono)",
          background: "oklch(0.62 0.21 38 / 0.08)",
          color: "oklch(0.83 0.15 200)",
          border: "1px solid oklch(0.62 0.21 38 / 0.25)",
        }}
      >
        {to}
      </div>
    </div>
  );
}

function ProviderRow({
  name,
  transport,
  note,
}: {
  name: string;
  transport: "anthropic_messages" | "openai_chat";
  note: string;
}) {
  const isAnthropic = transport === "anthropic_messages";
  return (
    <div
      className="flex items-center gap-3 py-3 border-b"
      style={{ borderColor: "oklch(0.22 0.015 265)" }}
    >
      <div className="flex-1 text-sm font-medium" style={{ color: "oklch(0.85 0.005 265)" }}>
        {name}
      </div>
      <Tag color={isAnthropic ? "orange" : "cyan"}>{transport}</Tag>
      <div className="w-56 text-xs text-right" style={{ color: "oklch(0.55 0.015 265)" }}>
        {note}
      </div>
    </div>
  );
}

function Section({ children, id }: { children: React.ReactNode; id?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("visible");
          observer.disconnect();
        }
      },
      { threshold: 0.05 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section id={id} ref={ref} className="fade-in-up mb-16">
      {children}
    </section>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────────
export default function Home() {
  const [activeSection, setActiveSection] = useActiveSection(TOC.map((t) => t.id));

  return (
    <div className="min-h-screen" style={{ background: "oklch(0.09 0.015 265)" }}>
      {/* ── Top nav ── */}
      <header
        className="sticky top-0 z-50 border-b"
        style={{
          background: "oklch(0.09 0.015 265 / 0.92)",
          backdropFilter: "blur(12px)",
          borderColor: "oklch(0.22 0.015 265)",
        }}
      >
        <div className="container flex items-center justify-between h-14">
          <a
            href="https://github.com/Alishahryar1/free-claude-code"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 no-underline"
          >
            <span
              className="text-lg font-bold"
              style={{ fontFamily: "var(--font-mono)", color: "oklch(0.62 0.21 38)" }}
            >
              &gt;_
            </span>
            <span
              className="text-base font-semibold"
              style={{ fontFamily: "var(--font-display)", color: "oklch(0.94 0.005 265)" }}
            >
              free-claude-code
            </span>
          </a>
          <a
            href="https://github.com/Alishahryar1/free-claude-code"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-md transition-colors"
            style={{
              fontFamily: "var(--font-mono)",
              color: "oklch(0.75 0.01 265)",
              border: "1px solid oklch(0.22 0.015 265)",
            }}
          >
            <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            View on GitHub
          </a>
        </div>
      </header>

      <div className="container">
        <div className="flex gap-12 pt-12">
          {/* ── Sticky TOC ── */}
          <aside className="hidden lg:block w-56 shrink-0">
            <div className="sticky top-24">
              <div
                className="text-xs font-bold uppercase tracking-widest mb-4"
                style={{ fontFamily: "var(--font-mono)", color: "oklch(0.45 0.015 265)" }}
              >
                On this page
              </div>
              <nav className="flex flex-col gap-0.5">
                {TOC.map((item) => (
                  <a
                    key={item.id}
                    href={`#${item.id}`}
                    className="text-sm py-1.5 px-3 rounded transition-all duration-200 no-underline"
                    style={{
                      fontFamily: "var(--font-body)",
                      color: activeSection === item.id ? "oklch(0.62 0.21 38)" : "oklch(0.55 0.015 265)",
                      background: activeSection === item.id ? "oklch(0.62 0.21 38 / 0.1)" : "transparent",
                      borderLeft: `2px solid ${activeSection === item.id ? "oklch(0.62 0.21 38)" : "transparent"}`,
                    }}
                  >
                    {item.label}
                  </a>
                ))}
              </nav>
            </div>
          </aside>

          {/* ── Main content ── */}
          <main className="flex-1 min-w-0 pb-24">
            {/* Hero */}
            <div className="mb-16">
              <div className="flex items-center gap-3 mb-6">
                <Tag color="orange">Architecture Deep Dive</Tag>
                <Tag color="muted">v1 · June 2026</Tag>
              </div>
              <h1
                className="text-5xl font-bold mb-6 leading-tight"
                style={{ fontFamily: "var(--font-display)", color: "oklch(0.97 0.005 265)" }}
              >
                How Free Claude Code Works
              </h1>
              <p
                className="text-xl leading-relaxed max-w-2xl"
                style={{ color: "oklch(0.65 0.01 265)", lineHeight: "1.7" }}
              >
                Claude Code speaks Anthropic. Every other LLM doesn't. Free Claude Code is a local
                protocol-aware proxy that bridges the gap — translating requests, optimizing background
                noise, and recovering broken streams so you can use any LLM with Claude Code's full
                feature set.
              </p>
              <div className="glow-divider mt-10" />
            </div>

            {/* Overview */}
            <Section id="overview">
              <SectionHeading id="overview">Overview</SectionHeading>
              <Prose>
                <strong style={{ color: "oklch(0.94 0.005 265)" }}>Free Claude Code</strong> is an
                open-source project by{" "}
                <a
                  href="https://github.com/Alishahryar1/free-claude-code"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "oklch(0.62 0.21 38)" }}
                >
                  Alishahryar1
                </a>{" "}
                with over 34,000 GitHub stars. It runs as a local ASGI web server (FastAPI + Uvicorn,
                default port 8082) that intercepts all traffic from the <Code>claude</Code> CLI and
                routes it to one of 17 supported upstream LLM providers.
              </Prose>
              <Prose>
                The project exposes two commands: <Code>fcc-server</Code> starts the proxy, and{" "}
                <Code>fcc-claude</Code> launches the real <Code>claude</Code> binary with the proxy
                pre-configured. From Claude Code's perspective, it is always talking to Anthropic's
                servers — the proxy is completely transparent.
              </Prose>
              <div
                className="rounded-lg p-5 my-6"
                style={{
                  background: "oklch(0.12 0.015 265)",
                  border: "1px solid oklch(0.22 0.015 265)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.875rem",
                  color: "oklch(0.75 0.01 265)",
                }}
              >
                <div style={{ color: "oklch(0.55 0.015 265)", marginBottom: "8px" }}># Install</div>
                <div>
                  <span style={{ color: "oklch(0.62 0.21 38)" }}>$</span> uv tool install free-claude-code
                </div>
                <div style={{ marginTop: "12px", color: "oklch(0.55 0.015 265)" }}># Start the proxy and Claude Code</div>
                <div>
                  <span style={{ color: "oklch(0.62 0.21 38)" }}>$</span> fcc-claude
                </div>
              </div>
            </Section>

            {/* The Problem */}
            <Section id="problem">
              <SectionHeading id="problem">The Problem</SectionHeading>
              <Prose>
                Claude Code is hardwired to call the Anthropic Messages API. It sends structured JSON
                payloads containing Anthropic-specific fields like <Code>thinking</Code>,{" "}
                <Code>context_management</Code>, and block-based content arrays. While many providers
                offer Anthropic-compatible endpoints, pointing Claude Code directly at them fails in
                practice for several reasons:
              </Prose>
              <div className="grid gap-3 my-6">
                {[
                  {
                    title: "Unknown field rejection",
                    desc: "Providers reject internal fields like context_management with HTTP 400 errors because they don't recognize them.",
                  },
                  {
                    title: "Reasoning block incompatibility",
                    desc: "Thinking blocks are formatted differently across providers — some use <think> tags, others use reasoning_content fields.",
                  },
                  {
                    title: "OpenAI-only providers",
                    desc: "Many fast, cheap providers (Groq, NVIDIA NIM, Mistral) only support the OpenAI /v1/chat/completions API, not Anthropic's protocol at all.",
                  },
                  {
                    title: "Background API call waste",
                    desc: "Claude Code makes many hidden calls for quota checks, title generation, and prefix detection that consume tokens and hit rate limits.",
                  },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="flex gap-4 p-4 rounded-lg"
                    style={{
                      background: "oklch(0.14 0.015 265)",
                      border: "1px solid oklch(0.22 0.015 265)",
                    }}
                  >
                    <div
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                      style={{
                        background: "oklch(0.62 0.21 38 / 0.15)",
                        color: "oklch(0.62 0.21 38)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {i + 1}
                    </div>
                    <div>
                      <div
                        className="font-semibold text-sm mb-1"
                        style={{ fontFamily: "var(--font-display)", color: "oklch(0.94 0.005 265)" }}
                      >
                        {item.title}
                      </div>
                      <div className="text-sm" style={{ color: "oklch(0.65 0.01 265)" }}>
                        {item.desc}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div
                className="rounded-lg p-4 mt-4"
                style={{
                  background: "oklch(0.62 0.21 38 / 0.06)",
                  border: "1px solid oklch(0.62 0.21 38 / 0.25)",
                }}
              >
                <div className="text-sm font-semibold mb-1" style={{ color: "oklch(0.62 0.21 38)", fontFamily: "var(--font-display)" }}>
                  Key Insight
                </div>
                <div className="text-sm" style={{ color: "oklch(0.75 0.01 265)" }}>
                  A direct base URL override is not enough. Claude Code needs a smart, protocol-aware
                  intermediary that understands the exact client-side protocol and translates it
                  correctly for each upstream provider.
                </div>
              </div>
            </Section>

            {/* The Solution */}
            <Section id="solution">
              <SectionHeading id="solution">The Solution: A Local Proxy</SectionHeading>
              <Prose>
                Free Claude Code runs as a local ASGI server that presents a perfect Anthropic API
                surface to Claude Code while routing requests to any of 17 supported upstream
                providers. The architecture has three main entry points:
              </Prose>
              <div className="grid gap-3 my-6">
                <FlowBox
                  number="1"
                  title="fcc-claude wrapper"
                  description="Sets ANTHROPIC_BASE_URL=http://127.0.0.1:8082 and launches the real claude binary. Claude Code believes it is communicating directly with Anthropic."
                  accent
                />
                <FlowBox
                  number="2"
                  title="Local Proxy (port 8082)"
                  description="A FastAPI/Uvicorn ASGI server that translates requests to 17 different upstream formats, translates responses back into Anthropic SSE format, and short-circuits wasteful background requests locally."
                />
                <FlowBox
                  number="3"
                  title="Upstream Providers"
                  description="The proxy routes sanitized, translated requests to external LLM providers over the internet — DeepSeek, OpenRouter, NVIDIA NIM, Groq, and many more."
                />
              </div>
            </Section>

            {/* Transport Paths */}
            <Section id="transport">
              <SectionHeading id="transport">The Two Transport Paths</SectionHeading>
              <Prose>
                The <Code>provider_catalog.py</Code> defines every provider's transport type. This
                single field determines the entire translation pipeline for a request.
              </Prose>
              <div className="grid md:grid-cols-2 gap-4 my-6">
                {[
                  {
                    type: "anthropic_messages",
                    protocol: "Native Anthropic /v1/messages",
                    providers: ["DeepSeek", "OpenRouter", "Kimi (Moonshot)", "Wafer, Z.ai, Fireworks", "LM Studio, llama.cpp, Ollama"],
                    behavior: "Proxy acts as a thin relay — sanitizes the request (stripping unsupported fields) and forwards it.",
                    color: "orange" as const,
                  },
                  {
                    type: "openai_chat",
                    protocol: "OpenAI /v1/chat/completions",
                    providers: ["NVIDIA NIM", "Mistral / Codestral", "Groq, Cerebras", "Google Gemini", "OpenCode Zen / Go"],
                    behavior: "Proxy performs a full bidirectional protocol translation — Anthropic ↔ OpenAI format conversion.",
                    color: "cyan" as const,
                  },
                ].map((t) => (
                  <div
                    key={t.type}
                    className="rounded-lg p-5"
                    style={{
                      background: "oklch(0.12 0.015 265)",
                      border: "1px solid oklch(0.22 0.015 265)",
                    }}
                  >
                    <Tag color={t.color}>{t.type}</Tag>
                    <div
                      className="text-xs mt-3 mb-4"
                      style={{ fontFamily: "var(--font-mono)", color: "oklch(0.55 0.015 265)" }}
                    >
                      {t.protocol}
                    </div>
                    <ul className="space-y-1.5 mb-4">
                      {t.providers.map((p) => (
                        <li key={p} className="flex items-center gap-2 text-sm" style={{ color: "oklch(0.75 0.01 265)" }}>
                          <span style={{ color: t.color === "orange" ? "oklch(0.62 0.21 38)" : "oklch(0.83 0.15 200)" }}>›</span>
                          {p}
                        </li>
                      ))}
                    </ul>
                    <div
                      className="text-xs leading-relaxed pt-3"
                      style={{
                        color: "oklch(0.55 0.015 265)",
                        borderTop: "1px solid oklch(0.22 0.015 265)",
                      }}
                    >
                      {t.behavior}
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            {/* Request Lifecycle */}
            <Section id="lifecycle">
              <SectionHeading id="lifecycle">Request Lifecycle</SectionHeading>
              <Prose>
                Every request from Claude Code passes through five distinct stages before a response is
                returned:
              </Prose>
              <div className="space-y-3 my-6">
                {[
                  {
                    n: "01",
                    title: "Ingress",
                    desc: "fcc-claude sets ANTHROPIC_BASE_URL=http://127.0.0.1:8082 and launches claude. All Claude Code API calls land on the local FastAPI server.",
                  },
                  {
                    n: "02",
                    title: "Model Routing",
                    desc: "The ModelRouter inspects the model field. It resolves claude-opus-* to MODEL_OPUS, claude-sonnet-* to MODEL_SONNET, etc. Each tier can point to a different provider.",
                  },
                  {
                    n: "03",
                    title: "Optimization Check",
                    desc: "Before touching any provider, the optimization_handlers pipeline runs. If the request matches a known background pattern (quota probe, title generation), a synthetic response is returned immediately — zero network calls.",
                  },
                  {
                    n: "04",
                    title: "Provider Translation",
                    desc: "The resolved provider's adapter builds the upstream request body (either native Anthropic or OpenAI format) and opens a streaming HTTP connection to the provider.",
                  },
                  {
                    n: "05",
                    title: "SSE Re-streaming",
                    desc: "The provider's streaming response is parsed and re-emitted as Anthropic-format Server-Sent Events back to Claude Code, ensuring perfect protocol compatibility.",
                  },
                ].map((step) => (
                  <FlowBox key={step.n} number={step.n} title={step.title} description={step.desc} />
                ))}
              </div>
            </Section>

            {/* Model Router */}
            <Section id="router">
              <SectionHeading id="router">The Model Router</SectionHeading>
              <Prose>
                The <Code>ModelRouter</Code> in <Code>api/model_router.py</Code> resolves incoming
                Claude model names using a three-level lookup strategy. This allows you to route
                different tiers (Opus, Sonnet, Haiku) to completely different providers simultaneously.
              </Prose>
              <div className="space-y-3 my-6">
                <DataRow
                  label="Level 1"
                  value="Gateway Model ID Decode"
                  note="If the model string is a gateway-encoded ID (e.g., anthropic/deepseek/deepseek-chat), it is decoded directly. This powers the interactive /model picker."
                />
                <DataRow
                  label="Level 2"
                  value="Direct Provider Prefix"
                  note="If the model string contains a known provider prefix (e.g., deepseek/deepseek-chat), it is routed directly to that provider."
                />
                <DataRow
                  label="Level 3"
                  value="Settings Fallback"
                  note="Otherwise, the model name is matched against the configured MODEL_OPUS, MODEL_SONNET, MODEL_HAIKU, or MODEL environment variables."
                />
              </div>
              <SubHeading>Example: Simultaneous Tier Routing</SubHeading>
              <div
                className="rounded-lg p-5 my-4"
                style={{
                  background: "oklch(0.12 0.015 265)",
                  border: "1px solid oklch(0.22 0.015 265)",
                }}
              >
                <DataRow label="MODEL_OPUS" value="deepseek/deepseek-chat" note="Heavy reasoning tasks" />
                <DataRow label="MODEL_SONNET" value="nvidia/llama-3.1-nemotron-ultra-253b-v1" note="Standard coding" />
                <DataRow label="MODEL_HAIKU" value="groq/llama-3.3-70b-versatile" note="Fast, cheap responses" />
              </div>
            </Section>

            {/* Optimization Pipeline */}
            <Section id="optimizations">
              <SectionHeading id="optimizations">The Optimization Pipeline</SectionHeading>
              <Prose>
                Claude Code makes many API calls that have nothing to do with actual coding. The{" "}
                <Code>optimization_handlers.py</Code> module intercepts these requests before they
                reach any upstream provider, returning synthetic responses instantly with zero network
                I/O.
              </Prose>
              <div className="my-6 rounded-lg overflow-hidden" style={{ border: "1px solid oklch(0.22 0.015 265)" }}>
                <div
                  className="grid text-xs font-bold uppercase tracking-widest px-5 py-3"
                  style={{
                    background: "oklch(0.14 0.015 265)",
                    color: "oklch(0.45 0.015 265)",
                    fontFamily: "var(--font-mono)",
                    gridTemplateColumns: "160px 1fr 1fr",
                    borderBottom: "1px solid oklch(0.22 0.015 265)",
                  }}
                >
                  <span>Handler</span>
                  <span>Detection Logic</span>
                  <span>Synthetic Response</span>
                </div>
                {[
                  {
                    name: "Quota Mock",
                    detect: 'max_tokens=1 + message contains "quota"',
                    response: '"Quota check passed."',
                  },
                  {
                    name: "Title Skip",
                    detect: 'System prompt contains "sentence-case title" or "return json" + "title"',
                    response: '"Conversation"',
                  },
                  {
                    name: "Prefix Detection",
                    detect: "Message contains <policy_spec> + Command: section",
                    response: "Regex-extracted command prefix",
                  },
                  {
                    name: "Suggestion Skip",
                    detect: "Message contains [SUGGESTION MODE:",
                    response: "(Empty string)",
                  },
                  {
                    name: "Filepath Mock",
                    detect: "Message contains Command: + Output: + filepath keywords",
                    response: "Regex-extracted file paths",
                  },
                ].map((row, i) => (
                  <div
                    key={i}
                    className="grid px-5 py-3 text-sm"
                    style={{
                      gridTemplateColumns: "160px 1fr 1fr",
                      background: i % 2 === 0 ? "oklch(0.10 0.015 265)" : "oklch(0.12 0.015 265)",
                      borderBottom: i < 4 ? "1px solid oklch(0.18 0.015 265)" : "none",
                      color: "oklch(0.75 0.01 265)",
                    }}
                  >
                    <span style={{ fontFamily: "var(--font-mono)", color: "oklch(0.62 0.21 38)", fontWeight: 600 }}>
                      {row.name}
                    </span>
                    <span style={{ paddingRight: "16px" }}>{row.detect}</span>
                    <span style={{ fontFamily: "var(--font-mono)", color: "oklch(0.83 0.15 200)", fontSize: "0.8rem" }}>
                      {row.response}
                    </span>
                  </div>
                ))}
              </div>
            </Section>

            {/* Protocol Converter */}
            <Section id="converter">
              <SectionHeading id="converter">The Anthropic-to-OpenAI Converter</SectionHeading>
              <Prose>
                The <Code>AnthropicToOpenAIConverter</Code> in <Code>core/anthropic/conversion.py</Code>{" "}
                handles the most complex translation challenge in the proxy. Anthropic and OpenAI have
                fundamentally different message schemas, and a simple 1:1 mapping is impossible.
              </Prose>
              <div className="grid md:grid-cols-2 gap-4 my-6">
                {[
                  {
                    title: "Tool Use After Text",
                    desc: "Anthropic allows text blocks after tool_use blocks in a single assistant message. OpenAI does not. The converter uses a _PendingAfterTools state machine to defer post-tool text until the corresponding role: tool results have been replayed.",
                  },
                  {
                    title: "Reasoning Replay",
                    desc: "Anthropic thinking blocks are replayed to OpenAI providers either as <think>...</think> tags prepended to the assistant message, or as reasoning_content fields, depending on the provider's capabilities.",
                  },
                  {
                    title: "Unknown Top-Level Fields",
                    desc: "Internal fields like context_management are silently stripped. Truly unknown extra fields raise an OpenAIConversionError before the request is sent, preventing upstream 400 errors.",
                  },
                  {
                    title: "Image Block Rejection",
                    desc: "Image blocks in assistant messages are rejected with a clear error, as OpenAI chat completions do not support assistant-generated images in the same format.",
                  },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg"
                    style={{
                      background: "oklch(0.12 0.015 265)",
                      border: "1px solid oklch(0.22 0.015 265)",
                    }}
                  >
                    <div
                      className="font-semibold text-sm mb-2"
                      style={{ fontFamily: "var(--font-display)", color: "oklch(0.83 0.15 200)" }}
                    >
                      {item.title}
                    </div>
                    <div className="text-sm leading-relaxed" style={{ color: "oklch(0.65 0.01 265)" }}>
                      {item.desc}
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            {/* SSE Re-streaming */}
            <Section id="streaming">
              <SectionHeading id="streaming">SSE Re-streaming</SectionHeading>
              <Prose>
                Claude Code expects a very specific Server-Sent Events (SSE) stream format. For
                OpenAI-style providers, the <Code>OpenAIChatTransport</Code> base class handles the
                reverse translation on the fly:
              </Prose>
              <div className="my-6 space-y-1">
                <div
                  className="grid text-xs font-bold uppercase tracking-widest px-4 py-3 rounded-t-lg"
                  style={{
                    background: "oklch(0.14 0.015 265)",
                    color: "oklch(0.45 0.015 265)",
                    fontFamily: "var(--font-mono)",
                    gridTemplateColumns: "1fr auto 1fr",
                    border: "1px solid oklch(0.22 0.015 265)",
                    borderBottom: "none",
                  }}
                >
                  <span>OpenAI Format</span>
                  <span />
                  <span>Anthropic SSE Format</span>
                </div>
                <div className="rounded-b-lg overflow-hidden" style={{ border: "1px solid oklch(0.22 0.015 265)" }}>
                  <MapRow from="delta.content text chunks" to="content_block_delta events" />
                  <MapRow from="delta.tool_calls" to="content_block_start + input_json_delta" />
                  <MapRow from="finish_reason" to="stop_reason (via map_stop_reason)" />
                  <MapRow from="reasoning_content or <think> tags" to="thinking content blocks" />
                </div>
              </div>
              <Prose>
                The <Code>SSEBuilder</Code> class manages block indices and ensures the event stream is
                well-formed. It also handles the <Code>Task</Code> tool specially — buffering its
                arguments and forcing <Code>run_in_background: false</Code> to prevent runaway
                background agents.
              </Prose>
            </Section>

            {/* Stream Recovery */}
            <Section id="recovery">
              <SectionHeading id="recovery">Stream Recovery</SectionHeading>
              <Prose>
                Real-world LLM APIs frequently truncate streams mid-response. Free Claude Code
                implements a multi-stage recovery system in{" "}
                <Code>core/anthropic/stream_recovery.py</Code> that is completely invisible to Claude
                Code:
              </Prose>
              <div className="grid md:grid-cols-3 gap-4 my-6">
                {[
                  {
                    title: "Early Transparent Retries",
                    desc: "If a stream fails before any content has been emitted to the client, the proxy transparently retries up to 3 times with the same request body.",
                    icon: "↺",
                  },
                  {
                    title: "Mid-stream Recovery",
                    desc: "If a stream truncates after content has been emitted, the proxy can attempt continuation by sending a follow-up request with a continuation_suffix appended to the last assistant message.",
                    icon: "⟶",
                  },
                  {
                    title: "Tool JSON Repair",
                    desc: "If a tool call's JSON arguments are truncated, the proxy attempts to repair the JSON before emitting the content_block_stop event, preventing Claude Code from crashing on malformed tool input.",
                    icon: "⚙",
                  },
                ].map((item) => (
                  <div
                    key={item.title}
                    className="p-5 rounded-lg"
                    style={{
                      background: "oklch(0.12 0.015 265)",
                      border: "1px solid oklch(0.22 0.015 265)",
                    }}
                  >
                    <div
                      className="text-3xl mb-3"
                      style={{ color: "oklch(0.62 0.21 38)" }}
                    >
                      {item.icon}
                    </div>
                    <div
                      className="font-semibold text-sm mb-2"
                      style={{ fontFamily: "var(--font-display)", color: "oklch(0.94 0.005 265)" }}
                    >
                      {item.title}
                    </div>
                    <div className="text-sm leading-relaxed" style={{ color: "oklch(0.65 0.01 265)" }}>
                      {item.desc}
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            {/* /v1/models */}
            <Section id="models">
              <SectionHeading id="models">The /v1/models Endpoint</SectionHeading>
              <Prose>
                Claude Code has an interactive <Code>/model</Code> picker. For this to work with
                non-Anthropic models, the proxy's <Code>/v1/models</Code> endpoint returns a carefully
                constructed list of available models in three categories:
              </Prose>
              <div className="space-y-3 my-6">
                <DataRow
                  label="Category 1"
                  value="Gateway-Encoded Provider Models"
                  note="Configured models are advertised as anthropic/{provider}/{model} (thinking enabled) and claude-3-freecc-no-thinking/{provider}/{model} (no thinking). The claude-3- prefix exploits a client-side heuristic."
                />
                <DataRow
                  label="Category 2"
                  value="Provider-Discovered Models"
                  note="On startup, the proxy queries each configured provider's /models endpoint and caches the results. These are dynamically added to the list with the same gateway encoding."
                />
                <DataRow
                  label="Category 3"
                  value="Standard Claude Models"
                  note="The canonical Claude model IDs (e.g., claude-3-5-sonnet-20241022) are always included as fallback entries to ensure the client never fails to find a default model."
                />
              </div>
            </Section>

            {/* Supported Providers */}
            <Section id="providers">
              <SectionHeading id="providers">Supported Providers</SectionHeading>
              <Prose>
                18 providers are supported across free tiers, paid APIs, and fully local models. This includes
                the newly added <strong style={{ color: "oklch(0.94 0.005 265)" }}>Xiaomi MiMo</strong>, which
                exposes a native Anthropic-compatible endpoint for its Pay-As-You-Go API.
              </Prose>
              <div className="my-6 rounded-lg overflow-hidden" style={{ border: "1px solid oklch(0.22 0.015 265)" }}>
                <div
                  className="grid text-xs font-bold uppercase tracking-widest px-5 py-3"
                  style={{
                    background: "oklch(0.14 0.015 265)",
                    color: "oklch(0.45 0.015 265)",
                    fontFamily: "var(--font-mono)",
                    gridTemplateColumns: "1fr auto 1fr",
                    borderBottom: "1px solid oklch(0.22 0.015 265)",
                  }}
                >
                  <span>Provider</span>
                  <span>Transport</span>
                  <span className="text-right">Notable Feature</span>
                </div>
                <div className="divide-y" style={{ borderColor: "oklch(0.18 0.015 265)" }}>
                  {[
                    { name: "NVIDIA NIM", transport: "openai_chat", note: "Default provider; Nemotron-3-Super-120B" },
                    { name: "OpenRouter", transport: "anthropic_messages", note: "Access to 300+ models via one key" },
                    { name: "Google Gemini", transport: "openai_chat", note: "Free tier via AI Studio" },
                    { name: "DeepSeek", transport: "anthropic_messages", note: "Native Anthropic endpoint" },
                    { name: "Mistral / Codestral", transport: "openai_chat", note: 'Free "Experiment" tier' },
                    { name: "OpenCode Zen / Go", transport: "openai_chat", note: "Curated multi-vendor gateway" },
                    { name: "Wafer", transport: "anthropic_messages", note: "Native Anthropic endpoint" },
                    { name: "Kimi (Moonshot)", transport: "anthropic_messages", note: "Native Anthropic endpoint" },
                    { name: "Cerebras", transport: "openai_chat", note: "Ultra-fast inference" },
                    { name: "Groq", transport: "openai_chat", note: "Ultra-fast inference" },
                    { name: "Fireworks AI", transport: "anthropic_messages", note: "Native Anthropic endpoint" },
                    { name: "Z.ai", transport: "anthropic_messages", note: "Native Anthropic endpoint" },
                    { name: "LM Studio / llama.cpp / Ollama", transport: "anthropic_messages", note: "Fully local, no API key needed" },
                    { name: "Xiaomi MiMo", transport: "anthropic_messages", note: "Pay-As-You-Go; native Anthropic endpoint" },
                  ].map((p) => (
                    <ProviderRow
                      key={p.name}
                      name={p.name}
                      transport={p.transport as "anthropic_messages" | "openai_chat"}
                      note={p.note}
                    />
                  ))}
                </div>
              </div>
            </Section>

            {/* Xiaomi MiMo Spotlight */}
            <Section id="mimo">
              <SectionHeading id="mimo">Xiaomi MiMo — Provider Spotlight</SectionHeading>
              <Prose>
                <a
                  href="https://mimo.mi.com/docs/en-US/tokenplan/integration/tools-overview"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "oklch(0.62 0.21 38)" }}
                >
                  Xiaomi MiMo
                </a>{" "}
                is Xiaomi's large-model API platform. It exposes a native Anthropic-compatible endpoint
                at <Code>https://api.xiaomimimo.com/anthropic</Code>, making it a first-class
                <Code>anthropic_messages</Code> transport provider in free-claude-code — no protocol
                translation required.
              </Prose>

              <SubHeading>Connection Details</SubHeading>
              <div className="space-y-3 my-4">
                <DataRow
                  label="Transport"
                  value="anthropic_messages"
                  note="Native Anthropic /v1/messages protocol — no OpenAI conversion needed"
                />
                <DataRow
                  label="Base URL"
                  value="https://api.xiaomimimo.com/anthropic"
                  note="Pay-As-You-Go plan; also available at token-plan-cn.xiaomimimo.com/anthropic for Token Plan subscribers"
                />
                <DataRow
                  label="API Key format"
                  value="sk-xxxxx"
                  note="Obtained from platform.xiaomimimo.com/console/api-keys"
                />
                <DataRow
                  label="OpenAI Base URL"
                  value="https://api.xiaomimimo.com/v1"
                  note="Alternative OpenAI-compatible endpoint if preferred"
                />
              </div>

              <SubHeading>Available Text Generation Models</SubHeading>
              <div className="my-4 rounded-lg overflow-hidden" style={{ border: "1px solid oklch(0.22 0.015 265)" }}>
                <div
                  className="grid text-xs font-bold uppercase tracking-widest px-5 py-3"
                  style={{
                    background: "oklch(0.14 0.015 265)",
                    color: "oklch(0.45 0.015 265)",
                    fontFamily: "var(--font-mono)",
                    gridTemplateColumns: "180px 1fr 120px 120px 120px",
                    borderBottom: "1px solid oklch(0.22 0.015 265)",
                    gap: "8px",
                  }}
                >
                  <span>Model ID</span>
                  <span>Capabilities</span>
                  <span>Context</span>
                  <span>Input / 1M</span>
                  <span>Output / 1M</span>
                </div>
                {[
                  {
                    id: "mimo-v2.5-pro",
                    caps: "Text, Deep Thinking, Function Call, Web Search",
                    ctx: "1M tokens",
                    input: "$0.435",
                    output: "$0.87",
                  },
                  {
                    id: "mimo-v2.5",
                    caps: "Text, Full-modal (image/audio/video), Deep Thinking, Function Call",
                    ctx: "1M tokens",
                    input: "$0.14",
                    output: "$0.28",
                  },
                  {
                    id: "mimo-v2-flash",
                    caps: "Text, Deep Thinking, Function Call, Web Search",
                    ctx: "256K tokens",
                    input: "$0.10",
                    output: "$0.30",
                  },
                ].map((m, i) => (
                  <div
                    key={m.id}
                    className="grid px-5 py-3 text-sm"
                    style={{
                      gridTemplateColumns: "180px 1fr 120px 120px 120px",
                      background: i % 2 === 0 ? "oklch(0.10 0.015 265)" : "oklch(0.12 0.015 265)",
                      borderBottom: i < 2 ? "1px solid oklch(0.18 0.015 265)" : "none",
                      color: "oklch(0.75 0.01 265)",
                      gap: "8px",
                      alignItems: "start",
                    }}
                  >
                    <span style={{ fontFamily: "var(--font-mono)", color: "oklch(0.62 0.21 38)", fontWeight: 600, fontSize: "0.8rem" }}>
                      {m.id}
                    </span>
                    <span style={{ fontSize: "0.8rem" }}>{m.caps}</span>
                    <span style={{ fontFamily: "var(--font-mono)", color: "oklch(0.83 0.15 200)", fontSize: "0.8rem" }}>{m.ctx}</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{m.input}</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{m.output}</span>
                  </div>
                ))}
              </div>
              <Prose>
                Pricing is per million tokens (overseas rates). Cache-hit input pricing is significantly
                lower: <Code>$0.0036/M</Code> for mimo-v2.5-pro and <Code>$0.0028/M</Code> for
                mimo-v2.5. Cache writes are free (limited-time). Rates as of June 2026.
              </Prose>

              <SubHeading>Configuring free-claude-code to use MiMo</SubHeading>
              <div
                className="rounded-lg p-5 my-4"
                style={{
                  background: "oklch(0.12 0.015 265)",
                  border: "1px solid oklch(0.22 0.015 265)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.875rem",
                  color: "oklch(0.75 0.01 265)",
                }}
              >
                <div style={{ color: "oklch(0.55 0.015 265)", marginBottom: "8px" }}># .env or environment variables</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>PROVIDER</span>=xiaomimimo</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>XIAOMIMIMO_API_KEY</span>=sk-xxxxx</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>MODEL</span>=mimo-v2.5-pro</div>
                <div style={{ marginTop: "12px", color: "oklch(0.55 0.015 265)" }}># Or route individual tiers to MiMo</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>MODEL_OPUS</span>=xiaomimimo/mimo-v2.5-pro</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>MODEL_SONNET</span>=xiaomimimo/mimo-v2.5</div>
                <div><span style={{ color: "oklch(0.62 0.21 38)" }}>MODEL_HAIKU</span>=xiaomimimo/mimo-v2-flash</div>
              </div>
              <div
                className="rounded-lg p-4 mt-4"
                style={{
                  background: "oklch(0.62 0.21 38 / 0.06)",
                  border: "1px solid oklch(0.62 0.21 38 / 0.25)",
                }}
              >
                <div className="text-sm font-semibold mb-1" style={{ color: "oklch(0.62 0.21 38)", fontFamily: "var(--font-display)" }}>
                  Note on Deprecations
                </div>
                <div className="text-sm" style={{ color: "oklch(0.75 0.01 265)" }}>
                  As of June 18, 2026, <Code>mimo-v2-flash</Code> and <Code>mimo-v2-tts</Code> auto-route
                  to V2.5 pricing and will be fully deprecated by June 30, 2026. Use{" "}
                  <Code>mimo-v2.5-pro</Code> or <Code>mimo-v2.5</Code> directly to avoid unexpected
                  pricing changes.
                </div>
              </div>
            </Section>

            {/* Architecture Summary */}
            <Section id="summary">
              <SectionHeading id="summary">Architecture Summary</SectionHeading>
              <Prose>
                The complete architecture can be understood as four distinct layers, each adding value
                that a raw base URL override cannot provide:
              </Prose>
              <div className="my-6 space-y-0 rounded-lg overflow-hidden" style={{ border: "1px solid oklch(0.22 0.015 265)" }}>
                {[
                  {
                    layer: "Entry",
                    component: "fcc-claude wrapper",
                    responsibility: "Sets environment variables and launches the real claude binary.",
                  },
                  {
                    layer: "Gateway",
                    component: "FastAPI ASGI server",
                    responsibility: "Exposes the Anthropic API surface, handles authentication, and manages routing.",
                  },
                  {
                    layer: "Intelligence",
                    component: "ModelRouter + OptimizationHandlers",
                    responsibility: "Performs per-tier routing and executes token-saving short-circuits for background tasks.",
                  },
                  {
                    layer: "Translation",
                    component: "AnthropicToOpenAI / AnthropicMessages transports",
                    responsibility: "Handles bidirectional protocol conversion, SSE re-streaming, and automatic stream recovery.",
                  },
                ].map((row, i) => (
                  <div
                    key={row.layer}
                    className="grid px-5 py-4"
                    style={{
                      gridTemplateColumns: "100px 220px 1fr",
                      background: i % 2 === 0 ? "oklch(0.10 0.015 265)" : "oklch(0.12 0.015 265)",
                      borderBottom: i < 3 ? "1px solid oklch(0.18 0.015 265)" : "none",
                      alignItems: "start",
                      gap: "16px",
                    }}
                  >
                    <div
                      className="text-sm font-bold uppercase tracking-wider"
                      style={{ fontFamily: "var(--font-mono)", color: "oklch(0.62 0.21 38)" }}
                    >
                      {row.layer}
                    </div>
                    <div
                      className="text-sm font-medium"
                      style={{ fontFamily: "var(--font-mono)", color: "oklch(0.83 0.15 200)" }}
                    >
                      {row.component}
                    </div>
                    <div className="text-sm" style={{ color: "oklch(0.65 0.01 265)" }}>
                      {row.responsibility}
                    </div>
                  </div>
                ))}
              </div>
              <div
                className="rounded-lg p-5 mt-6"
                style={{
                  background: "oklch(0.62 0.21 38 / 0.06)",
                  border: "1px solid oklch(0.62 0.21 38 / 0.25)",
                }}
              >
                <div
                  className="font-semibold mb-2"
                  style={{ fontFamily: "var(--font-display)", color: "oklch(0.62 0.21 38)" }}
                >
                  The Bottom Line
                </div>
                <div className="text-sm leading-relaxed" style={{ color: "oklch(0.75 0.01 265)" }}>
                  Free Claude Code is not a simple forwarder. It is a stateful, protocol-aware
                  translation engine that makes Claude Code's full feature set — thinking, tool use,
                  the /model picker, token counting, and streaming — work correctly with any supported
                  LLM provider, not just Anthropic's own models.
                </div>
              </div>
            </Section>

            {/* Footer */}
            <div className="glow-divider mb-8" />
            <div className="flex items-center justify-between text-sm" style={{ color: "oklch(0.45 0.015 265)" }}>
              <span style={{ fontFamily: "var(--font-mono)" }}>
                Based on{" "}
                <a
                  href="https://github.com/Alishahryar1/free-claude-code"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "oklch(0.62 0.21 38)" }}
                >
                  github.com/Alishahryar1/free-claude-code
                </a>
              </span>
              <span>Architecture analysis by Manus AI</span>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

// ─── Hook: active section tracking ────────────────────────────────────────────

function useActiveSection(ids: string[]): [string, React.Dispatch<React.SetStateAction<string>>] {
  const [active, setActive] = useState(ids[0] ?? "");

  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) setActive(id);
        },
        { rootMargin: "-20% 0px -70% 0px" }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, [ids]);

  return [active, setActive];
}
