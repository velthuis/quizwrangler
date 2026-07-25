#!/usr/bin/env python3
"""Build upload-ready skill ZIPs for Claude Desktop / claude.ai.

Claude's skill uploader wants a ZIP whose root is a single folder named after
the skill, with SKILL.md inside it. GitHub's "Download ZIP" does not produce
that shape -- it wraps everything in a <repo>-<branch>/ folder -- so these are
built here and attached to each GitHub Release.

Usage:
    python3 tools/build_skill_zips.py          # writes dist/*.zip
    python3 tools/build_skill_zips.py --check  # verify only, build nothing

Exit codes: 0 success, 1 a skill is malformed.
"""

import argparse
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
DIST_DIR = ROOT / "dist"


def frontmatter_name(skill_md):
    """Pull the `name:` field out of the YAML frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "file does not begin with a '---' frontmatter block"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter block is never closed with '---'"
    block = text[3:end]
    match = re.search(r"^name:\s*(.+?)\s*$", block, re.MULTILINE)
    if not match:
        return None, "frontmatter has no 'name:' field"
    return match.group(1), None


def collect(skill_dir):
    """Every file in the skill, sorted for reproducible archives."""
    return sorted(
        p for p in skill_dir.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="validate without writing ZIPs")
    args = ap.parse_args()

    if not SKILLS_DIR.is_dir():
        print(f"error: no skills directory at {SKILLS_DIR}", file=sys.stderr)
        return 1

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print(f"error: {SKILLS_DIR} contains no skill folders", file=sys.stderr)
        return 1

    problems = []
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{skill_dir.name}: no SKILL.md")
            continue

        name, err = frontmatter_name(skill_md)
        if err:
            problems.append(f"{skill_dir.name}/SKILL.md: {err}")
            continue

        # The uploader expects the folder name to match the declared skill name.
        if name != skill_dir.name:
            problems.append(
                f"{skill_dir.name}: folder name does not match frontmatter "
                f"name '{name}' -- rename one to match the other"
            )
            continue

        files = collect(skill_dir)
        if args.check:
            print(f"  ok  {name} ({len(files)} file{'s' if len(files) != 1 else ''})")
            continue

        DIST_DIR.mkdir(exist_ok=True)
        out = DIST_DIR / f"{name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                # Archive path is <skill-name>/<relative path> -- folder at root.
                z.write(f, pathlib.Path(name) / f.relative_to(skill_dir))
        size = out.stat().st_size
        print(f"  {out.relative_to(ROOT)}  ({len(files)} file(s), {size:,} bytes)")

    if problems:
        print("\nProblems found:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    if not args.check:
        print(f"\nAttach the files in {DIST_DIR.relative_to(ROOT)}/ to a GitHub Release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
