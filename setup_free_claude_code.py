#!/usr/bin/env python3
"""
Automated setup script for free-claude-code with multi-provider support.

Supported providers:
  1. DeepSeek          — fast, cheap, OpenAI-compatible
  2. Xiaomi MiMo       — native Anthropic Messages, strong reasoning
  3. W&B Inference     — open-source models (DeepSeek, Qwen3, Llama 4) via CoreWeave
  4. Mix by tier       — route Opus/Sonnet/Haiku to different providers

This script:
  1. Checks prerequisites (git, uv, Claude Code)
  2. Asks which provider(s) to use
  3. Clones the free-claude-code repository
  4. Installs dependencies via uv sync
  5. Writes .env and ~/.fcc/.env with the chosen provider config
  6. Creates launcher scripts for dual workflows (cheap + pro)
  7. Optionally adds shell aliases to ~/.zshrc or ~/.bashrc
  8. Optionally starts the proxy server

Run it:
    python3 setup_free_claude_code.py
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Colour / formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

def _print_step(num: int | str, title: str) -> None:
    print(f"\n  [{num}] {title}")
    print(f"  {'─' * (len(title) + 4)}")


def _print_ok(text: str) -> None:
    print(f"  ✓ {text}")


def _print_info(text: str) -> None:
    print(f"  · {text}")


def _print_warn(text: str) -> None:
    print(f"  ! {text}")


def _print_fail(text: str) -> None:
    print(f"  ✗ {text}")


# ──────────────────────────────────────────────────────────────────────────────
# User prompts
# ──────────────────────────────────────────────────────────────────────────────

def _ask(question: str, default: str | None = None) -> str:
    """Prompt the user for text input."""
    suffix = f" [{default}]" if default else ""
    val = input(f"  ? {question}{suffix}: ").strip()
    if not val and default is not None:
        return default
    return val


def _ask_yes_no(question: str, default: bool = True) -> bool:
    """Prompt for a yes/no answer."""
    indicator = "Y/n" if default else "y/N"
    val = input(f"  ? {question} ({indicator}): ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


def _ask_choice(question: str, choices: list[tuple[str, str]], default: int = 1) -> int:
    """Present a numbered menu and return the chosen index (1-based)."""
    print(f"\n  ? {question}")
    for i, (label, desc) in enumerate(choices, 1):
        marker = " ◀ default" if i == default else ""
        print(f"    {i}) {label:<22} {desc}{marker}")
    while True:
        raw = input(f"\n  Enter choice [1-{len(choices)}] [{default}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return int(raw)
        _print_warn(f"Please enter a number between 1 and {len(choices)}.")


# ──────────────────────────────────────────────────────────────────────────────
# Shell helpers
# ──────────────────────────────────────────────────────────────────────────────

def _run(
    cmd: list[str],
    cwd: str | None = None,
    *,
    check: bool = True,
    timeout: int | None = None,
    stream: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command and print output."""
    print(f"  · Running: {' '.join(cmd)}")
    try:
        if stream:
            result = subprocess.run(cmd, cwd=cwd, timeout=timeout)
        else:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
            )
            if result.stdout:
                for line in result.stdout.strip().splitlines():
                    print(f"    {line}")
        if result.returncode != 0 and check:
            _print_fail(f"Command failed: {' '.join(cmd)}")
            if hasattr(result, "stderr") and result.stderr:
                for line in result.stderr.strip().splitlines():
                    print(f"    {line}")
            sys.exit(1)
        return result
    except FileNotFoundError:
        _print_fail(f"Command not found: {cmd[0]}. Is it installed?")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        _print_fail(f"Command timed out: {' '.join(cmd)}")
        sys.exit(1)


def _which(name: str) -> Path | None:
    """Return the path to an executable, or None."""
    path = shutil.which(name)
    return Path(path) if path else None


# ──────────────────────────────────────────────────────────────────────────────
# Prerequisite checks
# ──────────────────────────────────────────────────────────────────────────────

def check_prerequisites() -> None:
    _print_step(1, "Checking prerequisites")

    git_path = _which("git")
    if git_path:
        _print_ok(f"git found at {git_path}")
    else:
        _print_fail("git is not installed. Install it first: https://git-scm.com/downloads")
        sys.exit(1)

    uv_path = _which("uv")
    if uv_path:
        result = subprocess.run([str(uv_path), "--version"], capture_output=True, text=True)
        _print_ok(f"uv found: {result.stdout.strip()}")
    else:
        _print_fail("uv is not installed.")
        _print_info("Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        if _ask_yes_no("  Install uv now?", default=True):
            _run(
                ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
                stream=True,
                check=False,
            )
            uv_path = _which("uv")
            if not uv_path:
                _print_fail("uv installation failed. Install it manually and re-run.")
                sys.exit(1)
        else:
            sys.exit(1)

    claude_path = _which("claude")
    if claude_path:
        _print_ok(f"Claude Code CLI found at {claude_path}")
    else:
        _print_warn(
            "Claude Code CLI not found. "
            "Install it after setup: https://docs.anthropic.com/en/docs/claude-code/overview"
        )
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Provider-specific key gathering
# ──────────────────────────────────────────────────────────────────────────────

PROVIDER_CHOICES = [
    ("DeepSeek",       "Fast, cheap — platform.deepseek.com"),
    ("Xiaomi MiMo",    "Native Anthropic Messages, strong reasoning"),
    ("W&B Inference",  "Open-source models via CoreWeave (wandb.ai)"),
    ("Mix by tier",    "Route Opus/Sonnet/Haiku to different providers"),
]

DEEPSEEK_MODELS = [
    ("deepseek/deepseek-v4-flash", "Fast & cheap (recommended default)"),
    ("deepseek/deepseek-v4-pro",   "Stronger, higher cost"),
    ("deepseek/deepseek-chat",     "Stable chat model"),
    ("deepseek/deepseek-reasoner", "Extended reasoning (R1)"),
]

MIMO_MODELS = [
    ("xiaomimimo/MiMo-72B-RL", "72B reasoning model (recommended)"),
    ("xiaomimimo/MiMo-7B-RL",  "7B reasoning model, very fast"),
]

WANDB_MODELS = [
    ("wandb_inference/deepseek-ai/DeepSeek-V3.1",                   "DeepSeek V3.1 via CoreWeave"),
    ("wandb_inference/Qwen/Qwen3-Coder-480B-A35B-Instruct",         "Qwen3 480B coder"),
    ("wandb_inference/meta-llama/Llama-4-Scout-17B-16E-Instruct",   "Llama 4 Scout"),
    ("wandb_inference/openai/gpt-oss-120b",                         "GPT OSS 120B"),
]


def _gather_deepseek() -> dict:
    """Gather DeepSeek-specific config."""
    api_key = _ask("Enter your DeepSeek API key (sk-...)")
    if not api_key.startswith("sk-"):
        _print_warn("API key doesn't start with 'sk-'. Make sure it's correct.")

    model_idx = _ask_choice("Default DeepSeek model", DEEPSEEK_MODELS, default=1)
    model = DEEPSEEK_MODELS[model_idx - 1][0]

    opus_idx = _ask_choice(
        "Model for Opus-tier requests",
        DEEPSEEK_MODELS + [("(same as default)", "")],
        default=len(DEEPSEEK_MODELS) + 1,
    )
    model_opus = "" if opus_idx == len(DEEPSEEK_MODELS) + 1 else DEEPSEEK_MODELS[opus_idx - 1][0]

    return {
        "provider": "deepseek",
        "deepseek_api_key": api_key,
        "model": model,
        "model_opus": model_opus,
        "enable_thinking": True,
    }


def _gather_mimo() -> dict:
    """Gather Xiaomi MiMo-specific config."""
    _print_info("Get your API key at: https://platform.xiaomimimo.com/console/api-keys")
    api_key = _ask("Enter your Xiaomi MiMo API key")

    token_plan = _ask_yes_no(
        "Are you on the MiMo Token Plan subscription?", default=False
    )
    base_url = (
        "https://token-plan-cn.xiaomimimo.com/anthropic/v1" if token_plan else ""
    )

    model_idx = _ask_choice("Default MiMo model", MIMO_MODELS, default=1)
    model = MIMO_MODELS[model_idx - 1][0]

    return {
        "provider": "xiaomimimo",
        "xiaomimimo_api_key": api_key,
        "xiaomimimo_base_url": base_url,
        "model": model,
        "model_opus": "",
        "enable_thinking": True,
    }


def _gather_wandb() -> dict:
    """Gather W&B Inference-specific config."""
    _print_info("Get your API key at: https://wandb.ai/settings")
    _print_info("The same key you use for W&B Weave tracing works here.")
    api_key = _ask("Enter your W&B API key")

    model_idx = _ask_choice("Default W&B Inference model", WANDB_MODELS, default=1)
    model = WANDB_MODELS[model_idx - 1][0]

    opus_idx = _ask_choice(
        "Model for Opus-tier requests",
        WANDB_MODELS + [("(same as default)", "")],
        default=len(WANDB_MODELS) + 1,
    )
    model_opus = "" if opus_idx == len(WANDB_MODELS) + 1 else WANDB_MODELS[opus_idx - 1][0]

    return {
        "provider": "wandb_inference",
        "wandb_api_key": api_key,
        "model": model,
        "model_opus": model_opus,
        "enable_thinking": False,
    }


def _gather_mix() -> dict:
    """Gather config for mixing providers by tier."""
    print()
    _print_info("You will configure each Claude model tier independently.")
    _print_info("You only need API keys for the providers you actually use.")
    print()

    TIER_PROVIDERS = [
        ("DeepSeek",      "platform.deepseek.com"),
        ("Xiaomi MiMo",   "platform.xiaomimimo.com"),
        ("W&B Inference", "wandb.ai"),
    ]

    result: dict = {"provider": "mix", "enable_thinking": True}

    # Collect keys for providers the user wants to use
    use_deepseek = _ask_yes_no("Use DeepSeek for any tier?", default=True)
    if use_deepseek:
        result["deepseek_api_key"] = _ask("  DeepSeek API key (sk-...)")

    use_mimo = _ask_yes_no("Use Xiaomi MiMo for any tier?", default=False)
    if use_mimo:
        result["xiaomimimo_api_key"] = _ask("  Xiaomi MiMo API key")
        token_plan = _ask_yes_no("  On MiMo Token Plan?", default=False)
        result["xiaomimimo_base_url"] = (
            "https://token-plan-cn.xiaomimimo.com/anthropic/v1" if token_plan else ""
        )

    use_wandb = _ask_yes_no("Use W&B Inference for any tier?", default=False)
    if use_wandb:
        result["wandb_api_key"] = _ask("  W&B API key")

    # Build available model list based on keys provided
    available: list[tuple[str, str]] = []
    if use_deepseek:
        available += DEEPSEEK_MODELS
    if use_mimo:
        available += MIMO_MODELS
    if use_wandb:
        available += WANDB_MODELS

    if not available:
        _print_fail("No providers selected. Please re-run and select at least one.")
        sys.exit(1)

    print()
    _print_info("Now assign a model to each Claude tier.")

    default_idx = _ask_choice("Default model (fallback for all tiers)", available, default=1)
    result["model"] = available[default_idx - 1][0]

    opus_choices = available + [("(same as default)", "")]
    opus_idx = _ask_choice("Opus-tier model", opus_choices, default=len(opus_choices))
    result["model_opus"] = "" if opus_idx == len(opus_choices) else available[opus_idx - 1][0]

    sonnet_choices = available + [("(same as default)", "")]
    sonnet_idx = _ask_choice("Sonnet-tier model", sonnet_choices, default=len(sonnet_choices))
    result["model_sonnet"] = "" if sonnet_idx == len(sonnet_choices) else available[sonnet_idx - 1][0]

    haiku_choices = available + [("(same as default)", "")]
    haiku_idx = _ask_choice("Haiku-tier model", haiku_choices, default=len(haiku_choices))
    result["model_haiku"] = "" if haiku_idx == len(haiku_choices) else available[haiku_idx - 1][0]

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Gather configuration
# ──────────────────────────────────────────────────────────────────────────────

def gather_config() -> dict:
    _print_step(2, "Configuration")
    print()

    cfg: dict = {}

    # Provider selection
    provider_idx = _ask_choice("Which provider do you want to use?", PROVIDER_CHOICES, default=1)

    if provider_idx == 1:
        cfg.update(_gather_deepseek())
    elif provider_idx == 2:
        cfg.update(_gather_mimo())
    elif provider_idx == 3:
        cfg.update(_gather_wandb())
    else:
        cfg.update(_gather_mix())

    print()

    # Installation directory
    default_dir = str(Path.home() / "Development" / "free-claude-code")
    install_dir = _ask("Installation directory", default=default_dir)
    cfg["install_dir"] = Path(install_dir)

    # Port
    cfg["port"] = _ask("Proxy server port", default="8082")

    # Shell aliases
    cfg["add_aliases"] = _ask_yes_no(
        "Add shell aliases to quickly switch between workflows", default=True
    )
    if cfg["add_aliases"]:
        shell = Path.home() / (".zshrc" if platform.system() == "Darwin" else ".bashrc")
        if not shell.exists():
            shell = Path.home() / ".bashrc"
        cfg["shell_rc"] = _ask("Shell config file to modify", default=str(shell))
        cfg["alias_cheap"] = _ask(
            "Alias name for proxy workflow (cheap tasks)", default="claude-cheap"
        )
        cfg["alias_pro"] = _ask(
            "Alias name for native Claude workflow (expensive tasks)", default="claude-pro"
        )

    cfg["start_proxy"] = _ask_yes_no("Start the proxy server after setup", default=False)

    print()
    return cfg


# ──────────────────────────────────────────────────────────────────────────────
# Clone repository
# ──────────────────────────────────────────────────────────────────────────────

def clone_repo(install_dir: Path) -> None:
    _print_step(3, "Cloning repository")

    parent = install_dir.parent
    if not parent.exists():
        _print_info(f"Creating parent directory: {parent}")
        parent.mkdir(parents=True, exist_ok=True)
    elif not os.access(str(parent), os.W_OK):
        _print_fail(f"No write permission: {parent}")
        sys.exit(1)

    if install_dir.exists():
        _print_warn(f"Directory already exists: {install_dir}")
        if not _ask_yes_no("  Remove it and re-clone?", default=False):
            _print_info("Using existing directory.")
            config["repo_dir"] = install_dir.resolve()
            return
        shutil.rmtree(install_dir)

    _run(
        ["git", "clone", "https://github.com/alifesoftware/free-claude-code.git", str(install_dir)]
    )
    _print_ok("Repository cloned.")
    config["repo_dir"] = install_dir.resolve()
    print()


# We store config as a mutable module-level dict for convenience
config: dict = {}


# ──────────────────────────────────────────────────────────────────────────────
# Install dependencies
# ──────────────────────────────────────────────────────────────────────────────

def install_dependencies() -> None:
    _print_step(4, "Installing dependencies (uv sync)")
    repo_dir = config["repo_dir"] = config["repo_dir"].resolve()
    _print_info("This will download Python and all project dependencies.")
    print()
    _run(["uv", "sync"], cwd=str(repo_dir))
    _print_ok("Dependencies installed.")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Build env content
# ──────────────────────────────────────────────────────────────────────────────

def _build_env_lines(include_auth_token: bool = False) -> str:
    """Build the .env content from config."""
    lines: list[str] = []

    provider = config.get("provider", "deepseek")

    # Provider-specific keys
    if provider in ("deepseek", "mix") and config.get("deepseek_api_key"):
        lines.append(f'DEEPSEEK_API_KEY="{config["deepseek_api_key"]}"')

    if provider in ("xiaomimimo", "mix") and config.get("xiaomimimo_api_key"):
        lines.append(f'XIAOMIMIMO_API_KEY="{config["xiaomimimo_api_key"]}"')
        base = config.get("xiaomimimo_base_url", "")
        if base:
            lines.append(f'XIAOMIMIMO_BASE_URL="{base}"')

    if provider in ("wandb_inference", "mix") and config.get("wandb_api_key"):
        lines.append(f'WANDB_API_KEY="{config["wandb_api_key"]}"')

    lines.append("")

    # Model routing
    lines.append(f'MODEL={config["model"]}')
    if config.get("model_opus"):
        lines.append(f'MODEL_OPUS={config["model_opus"]}')
    if config.get("model_sonnet"):
        lines.append(f'MODEL_SONNET={config["model_sonnet"]}')
    if config.get("model_haiku"):
        lines.append(f'MODEL_HAIKU={config["model_haiku"]}')

    lines.append("")

    # Proxy settings
    lines.append(f'HOST=0.0.0.0')
    lines.append(f'PORT={config["port"]}')
    enable_thinking = "true" if config.get("enable_thinking", True) else "false"
    lines.append(f'ENABLE_MODEL_THINKING={enable_thinking}')

    if include_auth_token:
        lines.insert(0, 'MESSAGING_PLATFORM="none"')
        lines.insert(1, 'VOICE_NOTE_ENABLED=false')
        lines.append('ANTHROPIC_AUTH_TOKEN="freecc"')

    return "\n".join(lines).strip() + "\n"


# ──────────────────────────────────────────────────────────────────────────────
# Write env files
# ──────────────────────────────────────────────────────────────────────────────

def write_env_files() -> None:
    _print_step(5, "Writing configuration files")
    repo_dir = config["repo_dir"]

    # 5a. Project-level .env
    env_file = repo_dir / ".env"
    env_file.write_text(_build_env_lines(include_auth_token=False))
    _print_ok(f"Created project .env: {env_file}")

    # 5b. Managed config at ~/.fcc/.env
    fcc_dir = Path.home() / ".fcc"
    fcc_dir.mkdir(parents=True, exist_ok=True)
    fcc_env_file = fcc_dir / ".env"
    fcc_env_file.write_text(_build_env_lines(include_auth_token=True))
    _print_ok(f"Created managed config: {fcc_env_file}")

    print()


# ──────────────────────────────────────────────────────────────────────────────
# Create launcher scripts
# ──────────────────────────────────────────────────────────────────────────────

def create_launcher_scripts() -> None:
    _print_step(6, "Creating launcher scripts")
    repo_dir = config["repo_dir"]
    port = config["port"]

    # start-cheap.sh (was start-deepseek.sh)
    cheap_script = repo_dir / "start-cheap.sh"
    cheap_script.write_text(
        textwrap.dedent(f"""\
            #!/bin/bash
            # Proxy instance — cheap tasks (scripts, tests, tool calling, automations)
            # Provider: {config.get("provider", "deepseek")}
            export ANTHROPIC_BASE_URL="http://localhost:{port}"
            export ANTHROPIC_AUTH_TOKEN="freecc"
            export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1"
            export CLAUDE_CODE_AUTO_COMPACT_WINDOW="190000"
            claude "$@"
        """)
    )
    cheap_script.chmod(0o755)
    _print_ok(f"Created: {cheap_script}")

    # Keep backward-compat alias for existing users
    compat_script = repo_dir / "start-deepseek.sh"
    compat_script.write_text(
        textwrap.dedent(f"""\
            #!/bin/bash
            # Backward-compatible alias — delegates to start-cheap.sh
            exec "$(dirname "$0")/start-cheap.sh" "$@"
        """)
    )
    compat_script.chmod(0o755)
    _print_ok(f"Created: {compat_script} (backward-compat alias)")

    # start-native-claude.sh
    native_script = repo_dir / "start-native-claude.sh"
    native_script.write_text(
        textwrap.dedent("""\
            #!/bin/bash
            # Native Claude instance — expensive tasks (reasoning, web dev, architecture, reviews)
            # Uses your real ANTHROPIC_API_KEY from the environment
            unset ANTHROPIC_BASE_URL
            unset ANTHROPIC_AUTH_TOKEN
            unset CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY
            claude "$@"
        """)
    )
    native_script.chmod(0o755)
    _print_ok(f"Created: {native_script}")

    print()


# ──────────────────────────────────────────────────────────────────────────────
# Add shell aliases
# ──────────────────────────────────────────────────────────────────────────────

def add_shell_aliases() -> None:
    _print_step(7, "Adding shell aliases")

    if not config.get("add_aliases"):
        _print_info("Skipped (user opted out).")
        print()
        return

    repo_dir = config["repo_dir"]
    shell_rc = Path(config["shell_rc"])
    alias_cheap = config.get("alias_cheap", "claude-cheap")
    alias_pro = config.get("alias_pro", "claude-pro")

    alias_lines = textwrap.dedent(f"""
        # Free Claude Code aliases (added by setup_free_claude_code.py)
        alias fcc-run="cd {repo_dir} && uv run fcc-server"
        alias {alias_cheap}="source {repo_dir}/start-cheap.sh"
        alias {alias_pro}="source {repo_dir}/start-native-claude.sh"
    """)

    with open(shell_rc, "a") as f:
        f.write(alias_lines)

    _print_ok(f"Aliases appended to {shell_rc}")
    _print_info(f"Run 'source {shell_rc}' or open a new terminal to activate.")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Start proxy (optional)
# ──────────────────────────────────────────────────────────────────────────────

def start_proxy() -> None:
    _print_step(8, "Starting proxy server")

    if not config.get("start_proxy"):
        _print_info("Skipped (user opted out). Start it later with:")
        _print_info(f"  cd {config['repo_dir']} && uv run fcc-server")
        _print_info("  or just: fcc-run (if you added aliases)")
        print()
        return

    repo_dir = config["repo_dir"]
    port = config["port"]
    _print_info(f"Starting proxy on http://localhost:{port} ...")
    _print_info("Press Ctrl+C to stop the server.")
    print()

    try:
        subprocess.run(
            ["uv", "run", "fcc-server"],
            cwd=str(repo_dir),
        )
    except KeyboardInterrupt:
        _print_info("Proxy server stopped.")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────

PROVIDER_LABELS = {
    "deepseek":       "DeepSeek",
    "xiaomimimo":     "Xiaomi MiMo",
    "wandb_inference": "W&B Inference",
    "mix":            "Mixed (multi-provider)",
}


def print_summary() -> None:
    _print_step("Done", "Setup complete!")
    print()

    repo_dir = config["repo_dir"]
    port = config["port"]
    provider_label = PROVIDER_LABELS.get(config.get("provider", "deepseek"), "Unknown")

    print(f"  ├─ Repository:  {repo_dir}")
    print(f"  ├─ Proxy URL:   http://localhost:{port}")
    print(f"  ├─ Admin UI:    http://localhost:{port}/admin")
    print(f"  ├─ Provider:    {provider_label}")
    print(f"  ├─ Model:       {config['model']}")
    if config.get("model_opus"):
        print(f"  ├─ Opus tier:   {config['model_opus']}")
    if config.get("model_sonnet"):
        print(f"  ├─ Sonnet tier: {config['model_sonnet']}")
    if config.get("model_haiku"):
        print(f"  ├─ Haiku tier:  {config['model_haiku']}")
    print()

    alias_cheap = config.get("alias_cheap", "claude-cheap")
    alias_pro = config.get("alias_pro", "claude-pro")

    print("  ── How to use ──────────────────────────────────────")
    print()
    print(f"  1. Start the proxy:")
    print(f"     cd {repo_dir} && uv run fcc-server")
    print(f"     Or: fcc-run")
    print()
    print(f"  2. For cheap tasks ({provider_label} via proxy):")
    print(f"     {alias_cheap}")
    print()
    print(f"  3. For expensive tasks (native Claude):")
    print(f"     {alias_pro}")
    print()
    print("  ── Open a new terminal (or source your shell rc) ───")
    if "shell_rc" in config:
        print(f"     source {config['shell_rc']}")
    print("  ────────────────────────────────────────────────────")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║     Free Claude Code — Multi-Provider Automated Setup       ║")
    print("  ║     DeepSeek · Xiaomi MiMo · W&B Inference · Mix            ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()

    global config
    config = gather_config()
    check_prerequisites()
    clone_repo(Path(config["install_dir"]))
    install_dependencies()
    write_env_files()
    create_launcher_scripts()
    add_shell_aliases()
    print_summary()
    start_proxy()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled.")
        sys.exit(0)
