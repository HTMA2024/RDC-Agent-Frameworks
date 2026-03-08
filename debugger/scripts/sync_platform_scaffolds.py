#!/usr/bin/env python3
"""Sync thin platform scaffolds from debugger/common/."""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "common"
COMMON_AGENTS = COMMON / "agents"
SHARED_SKILL = COMMON / "skills" / "renderdoc-rdc-gpu-debug" / "SKILL.md"

COMMON_AGENT_ORDER = [
    "01_team_lead.md",
    "02_triage_taxonomy.md",
    "03_capture_repro.md",
    "04_pass_graph_pipeline.md",
    "05_pixel_value_forensics.md",
    "06_shader_ir.md",
    "07_driver_device.md",
    "08_skeptic.md",
    "09_report_knowledge_curator.md",
]

NAME_MAPS = {
    "claude-work": {
        "01_team_lead.md": "team_lead.md",
        "02_triage_taxonomy.md": "triage.md",
        "03_capture_repro.md": "capture.md",
        "04_pass_graph_pipeline.md": "pipeline.md",
        "05_pixel_value_forensics.md": "forensics.md",
        "06_shader_ir.md": "shader.md",
        "07_driver_device.md": "driver.md",
        "08_skeptic.md": "skeptic.md",
        "09_report_knowledge_curator.md": "curator.md",
    },
    "copilot-ide": {
        "01_team_lead.md": "orchestrator.md",
        "02_triage_taxonomy.md": "triage.md",
        "03_capture_repro.md": "capture.md",
        "04_pass_graph_pipeline.md": "pipeline.md",
        "05_pixel_value_forensics.md": "forensics.md",
        "06_shader_ir.md": "shader.md",
        "07_driver_device.md": "driver.md",
        "08_skeptic.md": "verifier.md",
        "09_report_knowledge_curator.md": "report-curator.md",
    },
}


@dataclass(frozen=True)
class PlatformSpec:
    key: str
    agent_dir: str | None
    skill_dir: str | None
    extra_files: tuple[str, ...] = ()
    managed_dirs: tuple[str, ...] = ()


SPECS = (
    PlatformSpec(
        key="claude-code",
        agent_dir=".claude/agents",
        skill_dir=None,
        extra_files=(".claude/CLAUDE.md",),
        managed_dirs=(".claude/agents",),
    ),
    PlatformSpec(
        key="code-buddy",
        agent_dir="agents",
        skill_dir="skills/renderdoc-rdc-gpu-debug",
        managed_dirs=("agents", "skills/renderdoc-rdc-gpu-debug"),
    ),
    PlatformSpec(
        key="copilot-cli",
        agent_dir="agents",
        skill_dir="skills/renderdoc-rdc-gpu-debug",
        managed_dirs=("agents", "skills/renderdoc-rdc-gpu-debug"),
    ),
    PlatformSpec(
        key="copilot-ide",
        agent_dir=".github/agents",
        skill_dir=".github/skills/renderdoc-rdc-gpu-debug",
        extra_files=(".github/copilot-instructions.md",),
        managed_dirs=(".github/agents", ".github/skills/renderdoc-rdc-gpu-debug"),
    ),
    PlatformSpec(
        key="claude-work",
        agent_dir="agents",
        skill_dir=None,
        managed_dirs=("agents",),
    ),
    PlatformSpec(
        key="manus",
        agent_dir=None,
        skill_dir=None,
        managed_dirs=(),
    ),
)


def normalize(text: str) -> str:
    return text.rstrip() + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize(text), encoding="utf-8")


def rel_path(from_file: Path, target: Path) -> str:
    return Path(shutil.os.path.relpath(target, start=from_file.parent)).as_posix()


def agent_name(platform_key: str, source_name: str) -> str:
    mapped = NAME_MAPS.get(platform_key, {}).get(source_name, source_name)
    if platform_key == "copilot-cli":
        return mapped.replace(".md", ".agent.md")
    return mapped


def common_copy_readme() -> str:
    return """# Common Copy Contract

此目录必须放置从根目录 `debugger/common/` 复制来的共享运行时内容。

使用方式：

1. 将根目录 `debugger/common/` 整体复制到当前模板根的 `common/`。
2. 通过 `common/AGENT_CORE.md`、`common/agents/*.md`、`common/skills/renderdoc-rdc-gpu-debug/SKILL.md` 与 `common/docs/*.md` 进入共享运行时文档。

注意：

- 当前平台目录只是宿主薄包装模板，不是自包含运行包。
- Agent 的目标始终是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。
"""


def agent_wrapper(core_ref: str, role_ref: str) -> str:
    return f"""# RenderDoc/RDC Agent Wrapper

当前文件是宿主薄包装 agent。Agent 的目标是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。

使用前先将根目录 `debugger/common/` 复制到当前模板根的 `common/`。

按顺序阅读：

1. `{core_ref}`
2. `{role_ref}`
"""


def skill_wrapper(skill_ref: str) -> str:
    return f"""# RenderDoc/RDC GPU Debug Skill Wrapper

当前文件是宿主薄包装 skill。Agent 的目标是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。

使用前先将根目录 `debugger/common/` 复制到当前模板根的 `common/`。

共享 skill 入口：

- `{skill_ref}`
"""


def claude_code_entry() -> str:
    return """# Claude Code Template

当前目录是 Claude Code 薄包装模板。Agent 的目标是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。

使用前先将根目录 `debugger/common/` 复制到当前模板根的 `common/`。

@../common/AGENT_CORE.md
@../common/skills/renderdoc-rdc-gpu-debug/SKILL.md
"""


def copilot_instructions() -> str:
    return """# Copilot IDE Instructions

当前目录是 Copilot IDE / VS Code 薄包装模板。Agent 的目标是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。

使用前先将根目录 `debugger/common/` 复制到当前模板根的 `common/`。

先阅读：

1. `../common/AGENT_CORE.md`
2. `../common/skills/renderdoc-rdc-gpu-debug/SKILL.md`
"""


def spec_root(spec: PlatformSpec) -> Path:
    return ROOT / "platforms" / spec.key


def expected_files(spec: PlatformSpec) -> dict[Path, str]:
    package_root = spec_root(spec)
    expected: dict[Path, str] = {
        package_root / "common" / "README.copy-common.md": common_copy_readme(),
    }

    if spec.agent_dir is not None:
        for source_name in COMMON_AGENT_ORDER:
            target = package_root / spec.agent_dir / agent_name(spec.key, source_name)
            expected[target] = agent_wrapper(
                rel_path(target, COMMON / "AGENT_CORE.md"),
                rel_path(target, COMMON_AGENTS / source_name),
            )

    if spec.skill_dir is not None:
        target = package_root / spec.skill_dir / "SKILL.md"
        expected[target] = skill_wrapper(rel_path(target, SHARED_SKILL))

    if spec.key == "claude-code":
        expected[package_root / ".claude" / "CLAUDE.md"] = claude_code_entry()

    if spec.key == "copilot-ide":
        expected[package_root / ".github" / "copilot-instructions.md"] = copilot_instructions()

    return expected


def managed_dir_expectations(spec: PlatformSpec) -> dict[Path, set[str]]:
    package_root = spec_root(spec)
    dirs: dict[Path, set[str]] = {}
    expected = expected_files(spec)
    dirs[package_root / "common"] = {"README.copy-common.md"}
    for rel_path in spec.managed_dirs:
        dirs[package_root / rel_path] = set()
    for file_path in expected:
        parent = file_path.parent
        if parent in dirs:
            dirs[parent].add(file_path.name)
    return dirs


def compare_files(expected: dict[Path, str]) -> list[str]:
    findings: list[str] = []
    for path, content in sorted(expected.items()):
        if not path.exists():
            findings.append(f"missing file: {path}")
            continue
        current = path.read_text(encoding="utf-8-sig", errors="ignore")
        if normalize(current) != normalize(content):
            findings.append(f"content drift: {path}")
    return findings


def compare_managed_dirs(spec: PlatformSpec) -> list[str]:
    findings: list[str] = []
    for directory, expected_names in sorted(managed_dir_expectations(spec).items()):
        if not directory.exists():
            if expected_names:
                findings.append(f"missing directory: {directory}")
            continue
        actual_names = {child.name for child in directory.iterdir()}
        extras = sorted(actual_names - expected_names)
        for name in extras:
            findings.append(f"unexpected scaffold output: {directory / name}")
    return findings


def stale_shared_dirs(spec: PlatformSpec) -> list[str]:
    package_root = spec_root(spec)
    findings: list[str] = []
    for rel_path in ("docs", "scripts"):
        stale_path = package_root / rel_path
        if stale_path.exists():
            findings.append(f"forbidden copied shared directory: {stale_path}")
    return findings


def collect_findings(spec: PlatformSpec) -> list[str]:
    expected = expected_files(spec)
    findings = []
    findings.extend(compare_files(expected))
    findings.extend(compare_managed_dirs(spec))
    findings.extend(stale_shared_dirs(spec))
    return findings


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def sync_spec(spec: PlatformSpec) -> None:
    package_root = spec_root(spec)
    for rel_path in spec.managed_dirs:
        remove_path(package_root / rel_path)
    remove_path(package_root / "common" / "README.copy-common.md")
    for rel_path in spec.extra_files:
        remove_path(package_root / rel_path)
    for rel_path in ("docs", "scripts"):
        remove_path(package_root / rel_path)

    for path, content in expected_files(spec).items():
        write_text(path, content)


def validate_source_tree() -> list[str]:
    findings: list[str] = []
    if not COMMON.is_dir():
        findings.append(f"missing shared common root: {COMMON}")
    if not COMMON_AGENTS.is_dir():
        findings.append(f"missing shared agent root: {COMMON_AGENTS}")
    if not SHARED_SKILL.is_file():
        findings.append(f"missing shared skill entry: {SHARED_SKILL}")
    for name in COMMON_AGENT_ORDER:
        agent_file = COMMON_AGENTS / name
        if not agent_file.is_file():
            findings.append(f"missing shared agent source: {agent_file}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync debugger platform scaffolds")
    parser.add_argument("--check", action="store_true", help="Only validate scaffold outputs")
    args = parser.parse_args()

    source_findings = validate_source_tree()
    if source_findings:
        print("[platform scaffold findings]")
        for row in source_findings:
            print(f"  - {row}")
        return 1

    findings = [row for spec in SPECS for row in collect_findings(spec)]
    if args.check:
        if findings:
            print("[platform scaffold findings]")
            for row in findings:
                print(f"  - {row}")
            return 1
        print("platform scaffold check passed")
        return 0

    for spec in SPECS:
        sync_spec(spec)
    print("platform scaffold sync complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
