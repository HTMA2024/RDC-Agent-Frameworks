#!/usr/bin/env python3
"""Validate debugger platform template layout contracts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTS = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_SHARED_DIRS = (
    "common/agents",
    "common/config",
    "common/hooks",
    "common/knowledge",
    "common/project_plugin",
    "common/skills",
    "docs",
    "scripts",
)
FORBIDDEN_RUNTIME_REFS = (
    re.compile(r"(?<!common/)docs/cli-mode-reference\.md"),
    re.compile(r"(?<!common/)docs/model-routing\.md"),
    re.compile(r"(?<!common/)docs/platform-capability-matrix\.md"),
    re.compile(r"(?<!common/)docs/platform-capability-model\.md"),
    re.compile(r"(?<!common/)docs/runtime-coordination-model\.md"),
)


@dataclass(frozen=True)
class PlatformRule:
    key: str
    required_files: tuple[str, ...]


PLATFORM_RULES = (
    PlatformRule(
        key="claude-code",
        required_files=(
            ".claude/settings.json",
            ".claude/CLAUDE.md",
            ".claude/agents/01_team_lead.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
    PlatformRule(
        key="code-buddy",
        required_files=(
            ".codebuddy-plugin/plugin.json",
            ".mcp.json",
            "hooks/hooks.json",
            "agents/01_team_lead.md",
            "skills/renderdoc-rdc-gpu-debug/SKILL.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
    PlatformRule(
        key="copilot-cli",
        required_files=(
            ".copilot-plugin.json",
            ".mcp.json",
            "hooks/hooks.json",
            "agents/01_team_lead.agent.md",
            "skills/renderdoc-rdc-gpu-debug/SKILL.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
    PlatformRule(
        key="copilot-ide",
        required_files=(
            "agent-plugin.json",
            ".github/mcp.json",
            ".github/agents/orchestrator.md",
            ".github/skills/renderdoc-rdc-gpu-debug/SKILL.md",
            ".github/copilot-instructions.md",
            "references/entrypoints.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
    PlatformRule(
        key="claude-work",
        required_files=(
            "plugin.json",
            "agents/team_lead.md",
            "references/entrypoints.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
    PlatformRule(
        key="manus",
        required_files=(
            "workflows/00_debug_workflow.md",
            "references/entrypoints.md",
            "common/README.copy-common.md",
            "README.md",
        ),
    ),
)


def platform_root(rule: PlatformRule) -> Path:
    return ROOT / "platforms" / rule.key


def iter_text_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return [
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_EXTS
    ]


def validate_root_state() -> list[str]:
    findings: list[str] = []
    root_claude = ROOT / ".claude"
    if root_claude.exists():
        findings.append(f"source root must not contain host artifact: {root_claude}")
    return findings


def validate_platform(rule: PlatformRule) -> list[str]:
    findings: list[str] = []
    package_root = platform_root(rule)

    for rel_path in rule.required_files:
        full_path = package_root / rel_path
        if not full_path.exists():
            findings.append(f"{rule.key}: missing required file {full_path}")

    for rel_path in FORBIDDEN_SHARED_DIRS:
        full_path = package_root / rel_path
        if full_path.exists():
            findings.append(f"{rule.key}: forbidden copied shared content {full_path}")

    for file_path in iter_text_files(package_root):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        for marker in FORBIDDEN_RUNTIME_REFS:
            match = marker.search(text)
            if match:
                findings.append(
                    f"{rule.key}: forbidden maintainer-doc runtime reference in {file_path}: {match.group(0)}"
                )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate debugger platform layout")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on findings")
    args = parser.parse_args()

    findings = validate_root_state()
    for rule in PLATFORM_RULES:
        findings.extend(validate_platform(rule))

    if findings:
        print("[platform layout findings]")
        for row in findings:
            print(f"  - {row}")
        return 1 if args.strict else 0

    print("platform layout validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
