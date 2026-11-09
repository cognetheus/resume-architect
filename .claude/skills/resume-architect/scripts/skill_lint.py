#!/usr/bin/env python3
"""Lightweight skill packaging linter without external YAML dependencies."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def lint(skill_dir: Path) -> list[str]:
    problems = []
    p = skill_dir / "SKILL.md"
    if not p.exists():
        return ["SKILL.md missing"]
    s = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        return ["SKILL.md requires YAML frontmatter as first bytes"]
    fm = m.group(1)
    name_match = re.search(r"^name:\s*([a-z][a-z0-9-]*)\s*$", fm, re.M)
    if not name_match or name_match.group(1) != skill_dir.name:
        problems.append("Skill name must be kebab-case and match folder")
    if not re.search(r"^description:\s*\S+", fm, re.M):
        problems.append("Skill description missing")
    if len(s) > 30000:
        problems.append("SKILL.md exceeds 30KB; move detail into references")
    if "§" in s:
        problems.append("Unexpected placeholder character in SKILL.md")
    for relative in re.findall(r"(?:references|templates|scripts)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", s):
        if not (skill_dir / relative).exists():
            problems.append(f"Missing referenced file: {relative}")
    return sorted(set(problems))


def main():
    root = Path(__file__).resolve().parents[1]
    issues = lint(root)
    if issues:
        print("\n".join(issues))
        return 1
    print("PASS: skill structure and references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
