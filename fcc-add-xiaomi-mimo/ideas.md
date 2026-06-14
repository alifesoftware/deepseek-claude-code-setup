# Free Claude Code Architecture — Design Ideas

## Three Stylistic Approaches

### 1. Terminal Brutalism
A raw, monospaced, terminal-inspired aesthetic. Dark background with green/amber phosphor text. Strict grid lines, visible borders, and code-block-heavy layouts that feel like reading a technical manual inside a terminal. Probability: **0.04**

### 2. Dark Technical Documentation
A premium dark-mode documentation site inspired by Vercel/Linear. Deep navy/slate backgrounds, crisp white typography, subtle gradient accents, and generous whitespace. Feels authoritative and modern — like the docs for a serious developer tool. Probability: **0.07**

### 3. Illuminated Blueprint
A light-mode, architectural/blueprint-inspired design. Off-white paper texture, ink-blue technical typography, orange accent highlights, and subtle grid-paper backgrounds. Feels like a hand-annotated technical spec sheet — precise, intellectual, and distinctive. Probability: **0.02**

---

## Selected Approach: **Dark Technical Documentation**

### Design Movement
Post-brutalist developer tooling UI — inspired by Linear, Vercel, and Raycast docs. Serious, dense, and purposeful without being cold.

### Core Principles
1. **Information density without clutter** — every pixel earns its place; no decorative noise.
2. **Typographic hierarchy as navigation** — font weight and size guide the reader through complex technical content.
3. **Dark depth with luminous accents** — deep backgrounds make accent colors pop like neon on asphalt.
4. **Code is content** — inline code snippets and monospaced labels are first-class design elements, not afterthoughts.

### Color Philosophy
- Background: `#0a0e1a` (deep navy-black — feels like a terminal at night)
- Surface: `#111827` (slightly lighter for cards/sections)
- Border: `#1f2937` (subtle grid lines)
- Foreground: `#f1f5f9` (near-white, readable)
- Muted: `#64748b` (secondary text)
- Accent: `#ff5722` (deep orange — matches the existing FCC brand from the slides)
- Code accent: `#22d3ee` (cyan — for code tokens and technical labels)

### Layout Paradigm
Asymmetric single-column with a sticky left-rail table of contents on desktop. Content sections are full-width but use a max-width container. Architecture diagrams use horizontal flow boxes with connecting lines. Sections alternate between full-bleed dark and slightly lighter surfaces to create rhythm without cards.

### Signature Elements
1. **Glowing section dividers** — thin horizontal lines with a subtle orange glow, separating major sections.
2. **Annotated code/flow blocks** — dark code boxes with numbered callouts and inline color-coded labels.
3. **Sticky nav rail** — a left-side table of contents that highlights the active section as the user scrolls.

### Interaction Philosophy
Smooth scroll-linked animations: section headings fade in from below, code blocks reveal line by line. The TOC highlights the active section. Hover states on interactive elements use a subtle orange underline or glow.

### Animation
- Section entrance: `opacity: 0 → 1` + `translateY(20px → 0)` over 400ms ease-out, staggered by 80ms.
- TOC active indicator: smooth `translateY` transition following scroll position.
- Code block reveal: lines appear sequentially with a 30ms stagger.
- All animations gated behind `prefers-reduced-motion`.

### Typography System
- Display: **Space Grotesk** 700 — for section headings and the hero title.
- Body: **Inter** 400/500 — for prose content, readable at 16–18px.
- Code: **JetBrains Mono** 400 — for all code snippets, labels, and technical identifiers.
- Hierarchy: Hero 64px → Section H2 36px → Subsection H3 24px → Body 17px → Caption 14px.

### Brand Essence
Free Claude Code: the protocol translator that makes Claude Code work with any LLM. For developers who want power without vendor lock-in. Different because it's not a workaround — it's a full protocol engine.

### Brand Voice
Precise, confident, and slightly irreverent. Headlines state facts, not promises.
- Example headline: "Claude Code speaks Anthropic. Every other LLM doesn't. We fix that."
- Example CTA: "Read the architecture →"

### Wordmark & Logo
A stylized `>_` terminal prompt mark in orange, followed by `fcc` in JetBrains Mono bold.

### Signature Brand Color
`#ff5722` — deep orange, the same accent used in the slides.
