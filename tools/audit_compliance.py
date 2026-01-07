#!/usr/bin/env python3
"""
SpecKit Compliance Audit Script
Analyzes all MCP server specs for completion and constitution compliance.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class SpecAudit:
    spec_id: str
    spec_dir: Path
    total_tasks: int
    completed_tasks: int
    has_spec: bool
    has_plan: bool
    has_tasks: bool
    has_implementation: bool
    test_results: str = "Not run"
    constitution_notes: List[str] = None

    def __post_init__(self):
        if self.constitution_notes is None:
            self.constitution_notes = []

    @property
    def completion_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def is_complete(self) -> bool:
        return self.completed_tasks == self.total_tasks


def count_tasks(tasks_file: Path) -> tuple[int, int]:
    """Count total and completed tasks in tasks.md"""
    if not tasks_file.exists():
        return (0, 0)

    content = tasks_file.read_text()

    # Count checked and unchecked tasks (handle both [x] and [X])
    completed = len(re.findall(r'^\- \[[xX]\]', content, re.MULTILINE))
    total = len(re.findall(r'^\- \[[xX ]\]', content, re.MULTILINE))

    return (total, completed)


def check_implementation(spec_id: str) -> bool:
    """Check if server implementation exists"""
    # Extract API name from spec_id (e.g., "001-hgnc-mcp-server" -> "hgnc")
    api_name = spec_id.split('-')[1]
    server_file = Path(f"src/lifesciences_mcp/servers/{api_name}.py")
    return server_file.exists()


def audit_spec(spec_dir: Path) -> SpecAudit:
    """Audit a single spec directory"""
    spec_id = spec_dir.name

    # Check for SpecKit artifacts
    has_spec = (spec_dir / "spec.md").exists()
    has_plan = (spec_dir / "plan.md").exists()
    has_tasks = (spec_dir / "tasks.md").exists()

    # Count tasks
    total_tasks, completed_tasks = count_tasks(spec_dir / "tasks.md")

    # Check implementation
    has_implementation = check_implementation(spec_id)

    # Constitution compliance checks
    notes = []

    # Check if tasks.md has Platform Skills section
    if has_tasks:
        tasks_content = (spec_dir / "tasks.md").read_text()
        if "Platform Skills Usage" not in tasks_content:
            notes.append("❌ Missing Platform Skills section (Constitution VI)")
        if "Constitution Principle" not in tasks_content and "ADR-001" not in tasks_content:
            notes.append("⚠️ No explicit Constitution/ADR references in tasks")

    return SpecAudit(
        spec_id=spec_id,
        spec_dir=spec_dir,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        has_spec=has_spec,
        has_plan=has_plan,
        has_tasks=has_tasks,
        has_implementation=has_implementation,
        constitution_notes=notes
    )


def main():
    specs_dir = Path("specs")

    if not specs_dir.exists():
        print("❌ specs/ directory not found. Run from project root.")
        return

    # Get all spec directories
    spec_dirs = sorted([d for d in specs_dir.iterdir() if d.is_dir()])

    audits: List[SpecAudit] = []

    print("=" * 80)
    print("SpecKit Compliance Audit Report")
    print("=" * 80)
    print()

    # Audit each spec
    for spec_dir in spec_dirs:
        audit = audit_spec(spec_dir)
        audits.append(audit)

    # Summary table
    print(f"{'Spec ID':<30} {'Tasks':<12} {'Complete':<10} {'Impl':<6} {'SpecKit'}")
    print("-" * 80)

    for audit in audits:
        status_icon = "✅" if audit.is_complete else "⚠️" if audit.completion_rate > 0 else "❌"
        impl_icon = "✅" if audit.has_implementation else "❌"
        speckit = "✅" if (audit.has_spec and audit.has_plan and audit.has_tasks) else "❌"

        print(f"{status_icon} {audit.spec_id:<28} "
              f"{audit.completed_tasks:>2}/{audit.total_tasks:<2} ({audit.completion_rate:>5.1f}%)  "
              f"{impl_icon:>8}  "
              f"{speckit:>6}")

    print()
    print("=" * 80)
    print("Detailed Findings")
    print("=" * 80)
    print()

    # Detailed findings
    for audit in audits:
        print(f"\n### {audit.spec_id}")
        print(f"  Tasks: {audit.completed_tasks}/{audit.total_tasks} ({audit.completion_rate:.1f}%)")
        print(f"  SpecKit artifacts: {'✅' if audit.has_spec and audit.has_plan and audit.has_tasks else '❌'}")
        print(f"  Implementation: {'✅' if audit.has_implementation else '❌'}")

        if audit.constitution_notes:
            print(f"  Constitution compliance:")
            for note in audit.constitution_notes:
                print(f"    {note}")

    # Overall statistics
    print()
    print("=" * 80)
    print("Overall Statistics")
    print("=" * 80)
    print()

    total_specs = len(audits)
    complete_specs = sum(1 for a in audits if a.is_complete)
    implemented_specs = sum(1 for a in audits if a.has_implementation)
    total_all_tasks = sum(a.total_tasks for a in audits)
    completed_all_tasks = sum(a.completed_tasks for a in audits)

    print(f"Total specs: {total_specs}")
    print(f"Complete specs (tasks): {complete_specs}/{total_specs} ({complete_specs/total_specs*100:.1f}%)")
    print(f"Implemented servers: {implemented_specs}/{total_specs} ({implemented_specs/total_specs*100:.1f}%)")
    print(f"Total tasks: {completed_all_tasks}/{total_all_tasks} ({completed_all_tasks/total_all_tasks*100:.1f}%)")

    # Constitution violations
    specs_with_issues = [a for a in audits if a.constitution_notes]
    if specs_with_issues:
        print()
        print(f"⚠️ Constitution compliance issues: {len(specs_with_issues)}/{total_specs} specs")


if __name__ == "__main__":
    main()
