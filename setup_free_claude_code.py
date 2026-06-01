#!/usr/bin/env python3
"""
Automated setup script for free-claude-code with DeepSeek + dual Claude Code workflows.

This script:
  1. Checks prerequisites (git, uv, Claude Code)
  2. Clones the free-claude-code repository
  3. Installs dependencies via uv sync
  4. Configures DeepSeek as the default provider
  5. Creates launcher scripts for dual workflows (cheap + pro)
  6. Optionally adds shell aliases to ~/.zshrc or ~/.bashrc
  7. Optionally starts the proxy server

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

def _print_step(num: int, title: str) -> None:
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
    if not val and default:
        return default
    return val


def _ask_yes_no(question: str, default: bool = True) -> bool:
    """Prompt for a yes/no answer."""
    indicator = "Y/n" if default else "y/N"
    val = input(f"  ? {question} ({indicator}): ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


# ──────────────────────────────────────────────────────────────────────────────
# Shell helpers
# ──────────────────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: str | None = None, *, check: bool = True, timeout: int | None = None, stream: bool = False) -> subprocess.CompletedProcess:
    """Run a command and print output."""
    print(f"  · Running: {' '.join(cmd)}")
    try:
        if stream:
            result = subprocess.run(cmd, cwd=cwd, timeout=timeout)
        else:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            if result.stdout:
                for line in result.stdout.strip().splitlines():
                    print(f"    {line}")
        if result.returncode != 0 and check:
            _print_fail(f"Command failed: {' '.join(cmd)}")
            if result.stderr:
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

    # git
    git_path = _which("git")
    if git_path:
        _print_ok(f"git found at {git_path}")
    else:
        _print_fail("git is not installed. Install it first: https://git-scm.com/downloads")
        sys.exit(1)

    # uv
    uv_path = _which("uv")
    if uv_path:
        result = subprocess.run([str(uv_path), "--version"], capture_output=True, text=True)
        _print_ok(f"uv found: {result.stdout.strip()}")
    else:
        _print_fail("uv is not installed.")
        _print_info("Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        if _ask_yes_no("  Install uv now?", default=True):
            _run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"], stream=True, check=False)
            uv_path = _which("uv")
            if not uv_path:
                _print_fail("uv installation failed. Install it manually and re-run.")
                sys.exit(1)
        else:
            sys.exit(1)

    # claude (optional — warn only)
    claude_path = _which("claude")
    if claude_path:
        _print_ok(f"Claude Code CLI found at {claude_path}")
    else:
        _print_warn("Claude Code CLI not found. Install it after setup: https://docs.anthropic.com/en/docs/claude-code/overview")

    print()


# ──────────────────────────────────────────────────────────────────────────────
# Gather configuration
# ──────────────────────────────────────────────────────────────────────────────

def gather_config() -> dict:
    _print_step(2, "Configuration")
    print()

    config: dict = {}

    config["api_key"] = _ask("Enter your DeepSeek API key (sk-...)")
    if not config["api_key"].startswith("sk-"):
        _print_warn("API key doesn't start with 'sk-'. Make sure it's correct.")

    default_dir = str(Path.home() / "Development" / "free-claude-code")
    install_dir = _ask("Installation directory", default=default_dir)
    config["install_dir"] = Path(install_dir)

    config["port"] = _ask("Proxy server port", default="8082")
    config["model"] = _ask("Default DeepSeek model", default="deepseek/deepseek-v4-flash")
    config["model_opus"] = _ask("Model for Opus-tier requests (leave blank to inherit default model)", default="")

    config["add_aliases"] = _ask_yes_no("Add shell aliases to quickly switch between workflows", default=True)
    if config["add_aliases"]:
        shell = Path.home() / (".zshrc" if platform.system() == "Darwin" else ".bashrc")
        if not shell.exists():
            shell = Path.home() / ".bashrc"
        config["shell_rc"] = _ask("Shell config file to modify", default=str(shell))
        config["alias_cheap"] = _ask("Alias name for DeepSeek workflow (cheap tasks)", default="claude-cheap")
        config["alias_pro"] = _ask("Alias name for native Claude workflow (expensive tasks)", default="claude-pro")

    config["start_proxy"] = _ask_yes_no("Start the proxy server after setup", default=False)

    print()
    return config


# ──────────────────────────────────────────────────────────────────────────────
# Clone repository
# ──────────────────────────────────────────────────────────────────────────────

def clone_repo(install_dir: Path) -> None:
    _print_step(3, "Cloning repository")

    # Check write permission on parent directory
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

    _run(["git", "clone", "https://github.com/Alishahryar1/free-claude-code.git", str(install_dir)])
    _print_ok("Repository cloned.")

    # Store the canonical path (resolving any symlinks)
    config["repo_dir"] = install_dir.resolve()
    print()


# We'll store config as a mutable module-level dict for convenience in functions
config: dict = {}


# ──────────────────────────────────────────────────────────────────────────────
# Install dependencies
# ──────────────────────────────────────────────────────────────────────────────

def install_dependencies() -> None:
    _print_step(4, "Installing dependencies (uv sync)")

    repo_dir = config["repo_dir"] = config["repo_dir"].resolve()
    _print_info("This will download Python 3.14 (if needed) and all project dependencies.")
    print()

    _run(["uv", "sync"], cwd=str(repo_dir))
    _print_ok("Dependencies installed.")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Write env files
# ──────────────────────────────────────────────────────────────────────────────

def write_env_files() -> None:
    _print_step(5, "Writing configuration files")

    repo_dir = config["repo_dir"]

    # 5a. Project-level .env
    env_lines = textwrap.dedent(f"""\
        # DeepSeek Configuration
        DEEPSEEK_API_KEY="{config["api_key"]}"

        MODEL={config["model"]}
    """)

    if config.get("model_opus"):
        env_lines += f'MODEL_OPUS={config["model_opus"]}\n'

    env_lines += textwrap.dedent(f"""\
        HOST=0.0.0.0
        PORT={config["port"]}
        ENABLE_MODEL_THINKING=true
    """)

    env_file = repo_dir / ".env"
    env_file.write_text(env_lines.strip() + "\n")
    _print_ok(f"Created project .env: {env_file}")

    # 5b. Managed config at ~/.fcc/.env
    fcc_dir = Path.home() / ".fcc"
    fcc_dir.mkdir(parents=True, exist_ok=True)

    fcc_env_lines = textwrap.dedent(f"""\
        MESSAGING_PLATFORM="none"
        VOICE_NOTE_ENABLED=false

        DEEPSEEK_API_KEY="{config["api_key"]}"

        MODEL={config["model"]}
        ANTHROPIC_AUTH_TOKEN="freecc"
    """)

    if config.get("model_opus"):
        fcc_env_lines += f'MODEL_OPUS={config["model_opus"]}\n'

    fcc_env_lines += textwrap.dedent(f"""\
        HOST=0.0.0.0
        PORT={config["port"]}
        ENABLE_MODEL_THINKING=true
    """)

    fcc_env_file = fcc_dir / ".env"
    fcc_env_file.write_text(fcc_env_lines.strip() + "\n")
    _print_ok(f"Created managed config: {fcc_env_file}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Create launcher scripts
# ──────────────────────────────────────────────────────────────────────────────

def create_launcher_scripts() -> None:
    _print_step(6, "Creating launcher scripts")

    repo_dir = config["repo_dir"]

    # start-deepseek.sh
    deepseek_script = repo_dir / "start-deepseek.sh"
    deepseek_script.write_text(textwrap.dedent(f"""\
        #!/bin/bash
        # DeepSeek instance — cheap tasks (scripts, tests, tool calling, automations)

        export ANTHROPIC_BASE_URL="http://localhost:{config["port"]}"
        export ANTHROPIC_AUTH_TOKEN="freecc"
        export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1"
        export CLAUDE_CODE_AUTO_COMPACT_WINDOW="190000"

        claude "$@"
    """))
    deepseek_script.chmod(0o755)
    _print_ok(f"Created: {deepseek_script}")

    # start-native-claude.sh
    native_script = repo_dir / "start-native-claude.sh"
    native_script.write_text(textwrap.dedent("""\
        #!/bin/bash
        # Native Claude instance — expensive tasks (reasoning, web dev, architecture, reviews)
        # Uses your real ANTHROPIC_API_KEY from the environment

        unset ANTHROPIC_BASE_URL
        unset ANTHROPIC_AUTH_TOKEN
        unset CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY

        claude "$@"
    """))
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

    shell_rc = Path(config["shell_rc"])
    repo_dir = config["repo_dir"]

    alias_cheap = config.get("alias_cheap", "claude-cheap")
    alias_pro = config.get("alias_pro", "claude-pro")

    alias_lines = textwrap.dedent(f"""\

        # FreeClaudeCode aliases
        alias fcc-run='uv run python server.py'
        alias fcc-run-god-mode='sudo uv run python server.py'
        alias {alias_cheap}="source {repo_dir}/start-deepseek.sh"
        alias {alias_pro}="source {repo_dir}/start-native-claude.sh"
    """)

    with open(shell_rc, "a") as f:
        f.write(alias_lines)

    _print_ok(f"Aliases appended to {shell_rc}")
    _print_info("Run 'source {0}' or open a new terminal to activate.".format(shell_rc))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Start proxy (optional)
# ──────────────────────────────────────────────────────────────────────────────

def start_proxy() -> None:
    _print_step(8, "Starting proxy server")

    if not config.get("start_proxy"):
        _print_info("Skipped (user opted out). Start it later with:")
        _print_info(f"  cd {config['repo_dir']} && uv run uvicorn server:app --host 0.0.0.0 --port {config['port']}")
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
            ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=str(repo_dir),
        )
    except KeyboardInterrupt:
        _print_info("Proxy server stopped.")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────

def print_summary() -> None:
    _print_step("Done", "Setup complete!")
    print()

    repo_dir = config["repo_dir"]
    port = config["port"]

    print(f"  ├─ Repository: {repo_dir}")
    print(f"  ├─ Proxy URL:  http://localhost:{port}")
    print(f"  ├─ Admin UI:   http://localhost:{port}/admin")
    print(f"  ├─ Model:      {config['model']}")
    if config.get("model_opus"):
        print(f"  ├─ Opus tier:  {config['model_opus']}")
    print()

    alias_cheap = config.get("alias_cheap", "claude-cheap")
    alias_pro = config.get("alias_pro", "claude-pro")

    print("  ── How to use ──────────────────────────────────────")
    print()
    print(f"  1. Start the proxy:")
    print(f"     cd {repo_dir} && uv run uvicorn server:app --host 0.0.0.0 --port {port}")
    print(f"     Or: fcc-run")
    print()
    print(f"  2. For cheap tasks (DeepSeek via proxy):")
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
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║     Free Claude Code + DeepSeek — Automated Setup       ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
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
