#!/usr/bin/env python3
"""Register this repo's .skill bundles with Claude via the Skills API.

Each *.skill file is a zip archive containing <skill-name>/SKILL.md at a
single top-level directory — the format the Skills API expects.

Run this once, and again whenever a .skill file changes (it uploads a new
version rather than a duplicate skill). agent.py reads the resulting
skills.json to know which skill_ids to attach to a run.
"""
import json
import sys
import zipfile
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_MANIFEST = REPO_ROOT / "skills.json"


def load_skill_files(skill_path: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(skill_path) as zf:
        return [(name, zf.read(name)) for name in zf.namelist() if not name.endswith("/")]


def main() -> None:
    client = anthropic.Anthropic()
    manifest = json.loads(SKILLS_MANIFEST.read_text()) if SKILLS_MANIFEST.exists() else {}

    skill_paths = sorted(REPO_ROOT.glob("*.skill"))
    if not skill_paths:
        sys.exit("No .skill files found in the repo root.")

    for skill_path in skill_paths:
        name = skill_path.stem
        files = load_skill_files(skill_path)
        print(f"Uploading {skill_path.name} ({len(files)} file(s))...")

        existing = manifest.get(name)
        if existing:
            version = client.beta.skills.versions.create(existing["skill_id"], files=files)
            manifest[name] = {"skill_id": existing["skill_id"], "version": version.version}
            print(f"  -> new version for skill_id={existing['skill_id']}: {version.version}")
        else:
            skill = client.beta.skills.create(display_title=name, files=files)
            manifest[name] = {"skill_id": skill.id, "version": skill.latest_version}
            print(f"  -> created skill_id={skill.id} version={skill.latest_version}")

    SKILLS_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nWrote {SKILLS_MANIFEST.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
