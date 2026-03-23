#!/usr/bin/env python3
"""Validate or refresh the minimal debugger platform scaffold topology."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "common"
CONFIG_ROOT = COMMON / "config"
FORBIDDEN_DIRS = ("docs", "scripts")
PLATFORMS_WITH_GENERATED_HOOKS = {"code-buddy", "copilot-cli", "cursor"}
LEGACY_ENTRY_SKILL_DIRS = {"renderdoc-rdc-gpu-debug"}


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize(text), encoding="utf-8-sig")


def load_context(root: Path = ROOT) -> dict[str, Any]:
    return {
        "role_manifest": read_json(root / "common" / "config" / "role_manifest.json"),
        "platform_targets": read_json(root / "common" / "config" / "platform_targets.json"),
        "platform_capabilities": read_json(root / "common" / "config" / "platform_capabilities.json"),
        "framework_compliance": read_json(root / "common" / "config" / "framework_compliance.json"),
    }


def common_placeholder_text() -> str:
    return """# Platform Local Common Placeholder

当前目录是平台本地 `common/` 的最小占位目录，不是正式运行时内容。

使用方式：

1. 选择一个 `debugger/platforms/<platform>/` 模板。
2. 将仓库根目录 `debugger/common/` 整体拷贝到该平台根目录的 `common/`，覆盖当前目录。
3. 完成覆盖后，再在对应宿主中打开该平台根目录使用。

约束：

- 平台内所有 skill、hooks、agents、config 只允许引用当前平台根目录的 `common/`。
- 平台内运行时工作区固定为当前平台根目录同级的 `workspace/`。
- 未完成覆盖前，当前平台模板不可用。
- 不为未覆盖状态提供伪完整 placeholder 文件；正式共享正文只来自顶层 `debugger/common/`。
"""


def tools_placeholder_text() -> str:
    return """# Platform Local Tools Placeholder（本地 `tools/` 占位说明）

当前目录是平台本地 `tools/` 的最小占位目录，不是正式运行时内容。

使用方式：

1. 选择一个 `debugger/platforms/<platform>/` 模板。
2. 将 RDC-Agent-Tools 根目录整包拷贝到该平台根目录的 `tools/`，覆盖当前目录。
3. 完成覆盖后，运行 `python common/config/validate_binding.py --strict` 确认绑定有效。
4. 确认通过后，再在对应宿主中打开该平台根目录使用。

约束：

- 平台内所有 agent / skill / config 引用工具时，只允许引用当前平台根目录的 `tools/`。
- 未完成覆盖前，当前平台模板不可用。
- 不为未覆盖状态提供伪完整 placeholder 文件；正式工具真相只来自 RDC-Agent-Tools。
"""


def workspace_placeholder_text() -> str:
    return """# Platform Local Workspace Placeholder

当前目录是平台本地 `workspace/` 运行区骨架。

用途：

- 存放 capture-first 的 `case_id/run_id` 级运行现场
- 承载 case 级 `inputs/captures/`、run 级 `screenshots/`、`artifacts/`、`logs/`、`notes/`
- 承载第二层交付物 `reports/report.md` 与 `reports/visual_report.html`

约束：

- 这里不是共享真相；共享真相仍由同级 `common/` 提供。
- `common/` 中的 shared prompt / skill / docs 应通过 `../workspace` 引用当前目录。
- 原始 `.rdc` 只允许落在 `cases/<case_id>/inputs/captures/`，不得落在 `runs/<run_id>/`
- 模板仓库只保留占位骨架，不提交真实运行产物。
"""


def cases_placeholder_text() -> str:
    return """# Workspace Cases Placeholder

当前目录用于承载运行时 case。

目录约定：

```text
cases/
  <case_id>/
    case.yaml
    inputs/
      captures/
        manifest.yaml
        <capture_id>.rdc
    runs/
      <run_id>/
        run.yaml
        capture_refs.yaml
        artifacts/
        logs/
        notes/
        screenshots/
        reports/
```

规则：

- `.rdc` 是创建 case 的硬前置条件；未提供 capture 时不得初始化 case/run
- `case_id` 是问题实例/需求线程的稳定标识。
- `run_id` 承担 debug version。
- 原始 `.rdc` 只允许落在 `inputs/captures/`；run 只保留 capture 引用与派生产物。
- 第一层 session artifacts 仍写入同级 `common/knowledge/library/sessions/`；`workspace/` 不复制 gate 真相。
"""


def validate_source_tree(ctx: dict[str, Any]) -> list[str]:
    public_entry_skill = str(
        ((ctx.get("framework_compliance") or {}).get("entry_model") or {}).get("public_entry_skill", "")
    ).strip()
    required = [
        COMMON,
        COMMON / "README.md",
        COMMON / "agents",
        COMMON / "skills" / public_entry_skill / "SKILL.md",
        COMMON / "docs" / "workspace-layout.md",
        COMMON / "knowledge" / "proposals" / "README.md",
        CONFIG_ROOT / "role_manifest.json",
        CONFIG_ROOT / "role_policy.json",
        CONFIG_ROOT / "model_routing.json",
        CONFIG_ROOT / "mcp_servers.json",
        CONFIG_ROOT / "platform_adapter.json",
        CONFIG_ROOT / "platform_capabilities.json",
        CONFIG_ROOT / "platform_targets.json",
        CONFIG_ROOT / "framework_compliance.json",
        CONFIG_ROOT / "tool_catalog.snapshot.json",
    ]
    findings: list[str] = []
    for path in required:
        if not path.exists():
            findings.append(f"missing shared source: {path}")
    for role in ctx["role_manifest"]["roles"]:
        source = COMMON / role["source_prompt"]
        if not source.exists():
            findings.append(f"missing shared agent source: {source}")
        skill = COMMON / role["role_skill_path"]
        if not skill.exists():
            findings.append(f"missing shared role skill: {skill}")
    return findings


def expected_files(ctx: dict[str, Any], platform_key: str) -> set[Path]:
    package = ROOT / "platforms" / platform_key
    capabilities = ctx["platform_capabilities"]["platforms"][platform_key]
    target = ctx["platform_targets"]["platforms"][platform_key]
    public_entry_skill = str(
        ((ctx.get("framework_compliance") or {}).get("entry_model") or {}).get("public_entry_skill", "")
    ).strip()
    expected = {
        package / "README.md",
        package / "AGENTS.md",
        package / "common" / "README.md",
        package / "tools" / "README.md",
        package / "workspace" / "README.md",
        package / "workspace" / "cases" / "README.md",
    }

    for rel in capabilities.get("required_paths") or []:
        expected.add(ROOT / rel)

    agent_dir = target.get("agent_dir")
    if agent_dir:
        for role in ctx["role_manifest"]["roles"]:
            file_name = (role.get("platform_files") or {}).get(platform_key)
            if file_name:
                expected.add(package / agent_dir / file_name)

    role_config_dir = target.get("role_config_dir")
    if role_config_dir:
        for role in ctx["role_manifest"]["roles"]:
            file_name = (role.get("platform_files") or {}).get(platform_key)
            if file_name:
                expected.add(package / role_config_dir / f"{file_name}.toml")

    skill_dir = target.get("skill_dir")
    if skill_dir:
        expected.add(package / skill_dir / "SKILL.md")
        skill_root = package / Path(skill_dir).parent
        for role in ctx["role_manifest"]["roles"]:
            expected.add(skill_root / Path(role["role_skill_path"]).parent.name / "SKILL.md")
        expected.add(skill_root / public_entry_skill / "SKILL.md")

    if platform_key in PLATFORMS_WITH_GENERATED_HOOKS:
        expected.add(package / "hooks" / "hooks.json")

    return expected


def compare_placeholder(package: Path, rel_path: str, expected_text: str) -> list[str]:
    path = package / rel_path
    if not path.is_file():
        return [f"missing file: {path}"]
    current = normalize(path.read_text(encoding="utf-8-sig"))
    if current != normalize(expected_text):
        return [f"content drift: {path}"]
    return []


def compare_common_and_workspace(package: Path) -> list[str]:
    findings: list[str] = []
    findings.extend(compare_placeholder(package, "common/README.md", common_placeholder_text()))
    findings.extend(compare_placeholder(package, "tools/README.md", tools_placeholder_text()))
    findings.extend(compare_placeholder(package, "workspace/README.md", workspace_placeholder_text()))
    findings.extend(compare_placeholder(package, "workspace/cases/README.md", cases_placeholder_text()))

    common_dir = package / "common"
    if common_dir.exists():
        children = {child.name for child in common_dir.iterdir()}
        for name in sorted(children - {"README.md"}):
            findings.append(f"unexpected platform-common content: {common_dir / name}")

    tools_dir = package / "tools"
    if tools_dir.exists():
        children = {child.name for child in tools_dir.iterdir()}
        for name in sorted(children - {"README.md"}):
            findings.append(f"unexpected platform-tools content: {tools_dir / name}")

    workspace_dir = package / "workspace"
    if workspace_dir.exists():
        children = {child.name for child in workspace_dir.iterdir()}
        for name in sorted(children - {"README.md", "cases"}):
            findings.append(f"unexpected workspace placeholder content: {workspace_dir / name}")

    cases_dir = workspace_dir / "cases"
    if cases_dir.exists():
        children = {child.name for child in cases_dir.iterdir()}
        for name in sorted(children - {"README.md"}):
            findings.append(f"unexpected cases placeholder content: {cases_dir / name}")

    return findings


def stale_findings(platform_key: str) -> list[str]:
    package = ROOT / "platforms" / platform_key
    findings: list[str] = []
    for rel in FORBIDDEN_DIRS:
        target = package / rel
        if target.exists():
            findings.append(f"forbidden copied shared directory: {target}")
    for path in package.rglob("README.copy-common.md"):
        findings.append(f"forbidden copy-common artifact: {path}")
    for path in package.rglob("renderdoc-rdc-gpu-debug"):
        findings.append(f"legacy entry skill directory must not exist: {path}")
    return findings


def _rel_from(source_dir: Path, target: Path) -> str:
    return os.path.relpath(target, source_dir).replace("\\", "/")


def _public_entry_skill(ctx: dict[str, Any]) -> str:
    return str(((ctx.get("framework_compliance") or {}).get("entry_model") or {}).get("public_entry_skill", "")).strip()


def _orchestration_role(ctx: dict[str, Any]) -> str:
    return str(((ctx.get("framework_compliance") or {}).get("entry_model") or {}).get("orchestration_role", "")).strip()


def main_skill_wrapper_text(ctx: dict[str, Any], platform_key: str) -> str:
    package = ROOT / "platforms" / platform_key
    target = ctx["platform_targets"]["platforms"][platform_key]
    wrapper_dir = package / str(target.get("skill_dir", "")).strip()
    display_name = str((ctx["platform_capabilities"]["platforms"][platform_key] or {}).get("display_name", platform_key)).strip()
    public_entry_skill = _public_entry_skill(ctx)
    local_common = package / "common"
    common_skill = _rel_from(wrapper_dir, local_common / "skills" / public_entry_skill / "SKILL.md")
    caps = _rel_from(wrapper_dir, local_common / "config" / "platform_capabilities.json")
    adapter = _rel_from(wrapper_dir, local_common / "config" / "platform_adapter.json")
    return f"""# RDC Debugger Main Skill Wrapper

当前文件是 {display_name} 的 public main skill 入口。

正常用户请求先进入 `{public_entry_skill}`。本 skill 负责 preflight、补料、intake 规范化，并在条件满足后把任务交给 `team_lead`。

本 skill 只引用当前平台根目录的 `common/`：

- {common_skill}
- 进入任何平台真相相关工作前，必须先校验 {adapter}
- coordination_mode 与降级边界以 {caps} 的当前平台定义为准。

未先将顶层 `debugger/common/` 拷入当前平台根目录的 `common/` 之前，不允许在宿主中使用当前平台模板。

运行时 case/run 现场与第二层报告统一写入：`../workspace`
"""


def role_skill_wrapper_text(ctx: dict[str, Any], platform_key: str, role: dict[str, Any]) -> str:
    package = ROOT / "platforms" / platform_key
    target = ctx["platform_targets"]["platforms"][platform_key]
    skill_root = package / Path(str(target.get("skill_dir", "")).strip()).parent
    wrapper_dir = skill_root / Path(role["role_skill_path"]).parent.name
    display_name = str((ctx["platform_capabilities"]["platforms"][platform_key] or {}).get("display_name", platform_key)).strip()
    public_entry_skill = _public_entry_skill(ctx)
    orchestration_role = _orchestration_role(ctx)
    local_common = package / "common"
    main_skill = _rel_from(wrapper_dir, local_common / "skills" / public_entry_skill / "SKILL.md")
    role_skill = _rel_from(wrapper_dir, local_common / role["role_skill_path"])
    caps = _rel_from(wrapper_dir, local_common / "config" / "platform_capabilities.json")
    agent_id = str(role.get("agent_id", "")).strip()

    if agent_id == orchestration_role:
        role_intro = "该角色只负责 orchestration，不是 public main skill。正常用户请求应先从 `rdc-debugger` 发起，当前 role 只接收 normalized intake / task handoff。"
        title = "Team Lead Skill Wrapper（角色技能入口）"
        extra = "在 `run_compliance.yaml(status=passed)` 生成前，你只能输出阶段性 brief，不得宣称最终裁决。"
    else:
        role_intro = "该角色默认是 internal/debug-only specialist。正常用户请求应先交给 `rdc-debugger`，只有调试 framework 本身时才直接使用该角色。"
        title = "Role Skill Wrapper"
        extra = ""

    tail = "\n" + extra if extra else ""
    return f"""# {title}

当前文件是 {display_name} 的 role skill 入口。

{role_intro}

先阅读：

1. {main_skill}
2. {role_skill}
3. {caps}

未先将顶层 `debugger/common/` 拷入当前平台根目录的 `common/` 之前，不允许在宿主中使用当前平台模板。{tail}
运行时 case/run 现场与第二层报告统一写入：`../workspace`
"""


def collect_findings(ctx: dict[str, Any], platform_key: str) -> list[str]:
    package = ROOT / "platforms" / platform_key
    findings: list[str] = []
    for path in sorted(expected_files(ctx, platform_key)):
        if not path.exists():
            findings.append(f"missing file: {path}")
    findings.extend(compare_common_and_workspace(package))
    findings.extend(stale_findings(platform_key))
    return findings


def sync_placeholders(platform_key: str) -> None:
    package = ROOT / "platforms" / platform_key
    for rel in FORBIDDEN_DIRS:
        target = package / rel
        if target.exists():
            shutil.rmtree(target)
    write_text(package / "common" / "README.md", common_placeholder_text())
    write_text(package / "tools" / "README.md", tools_placeholder_text())
    write_text(package / "workspace" / "README.md", workspace_placeholder_text())
    write_text(package / "workspace" / "cases" / "README.md", cases_placeholder_text())


def sync_skill_wrappers(ctx: dict[str, Any], platform_key: str) -> None:
    package = ROOT / "platforms" / platform_key
    target = ctx["platform_targets"]["platforms"][platform_key]
    skill_dir = target.get("skill_dir")
    if not skill_dir:
        return

    skill_root = package / Path(skill_dir).parent
    public_entry_skill = _public_entry_skill(ctx)
    desired_names = {public_entry_skill}

    write_text(skill_root / public_entry_skill / "SKILL.md", main_skill_wrapper_text(ctx, platform_key))
    for role in ctx["role_manifest"]["roles"]:
        role_name = Path(role["role_skill_path"]).parent.name
        desired_names.add(role_name)
        write_text(skill_root / role_name / "SKILL.md", role_skill_wrapper_text(ctx, platform_key, role))

    if skill_root.is_dir():
        for child in skill_root.iterdir():
            if not child.is_dir():
                continue
            if child.name in LEGACY_ENTRY_SKILL_DIRS or child.name not in desired_names:
                shutil.rmtree(child)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or refresh minimal debugger platform scaffolds")
    parser.add_argument("--check", action="store_true", help="Validate scaffold topology without rewriting placeholders")
    args = parser.parse_args(argv)

    ctx = load_context(ROOT)
    findings = validate_source_tree(ctx)
    for platform_key in ctx["platform_capabilities"]["platforms"]:
        findings.extend(collect_findings(ctx, platform_key))

    if args.check:
        if findings:
            print("[platform scaffold findings]")
            for row in findings:
                print(f" - {row}")
            return 1
        print("platform scaffold check passed")
        return 0

    for platform_key in ctx["platform_capabilities"]["platforms"]:
        sync_placeholders(platform_key)
        sync_skill_wrappers(ctx, platform_key)
    if findings:
        print("[platform scaffold findings]")
        for row in findings:
            print(f" - {row}")
        return 1
    print("platform scaffold sync complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
