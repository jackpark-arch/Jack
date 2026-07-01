#!/usr/bin/env python3
"""Run a task against Claude using this repo's uploaded Skills.

Usage:
    python scripts/agent.py "Build next week's content calendar for Acme Co"

Requires skills.json (created by upload_skills.py) and an Anthropic
credential in the environment (ANTHROPIC_API_KEY, or an `ant auth login`
profile).
"""
import json
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_MANIFEST = REPO_ROOT / "skills.json"
OUTPUT_DIR = REPO_ROOT / "outputs"
MODEL = "claude-opus-4-8"


def load_skills() -> list[dict]:
    if not SKILLS_MANIFEST.exists():
        sys.exit(f"{SKILLS_MANIFEST.name} not found — run `python scripts/upload_skills.py` first.")
    manifest = json.loads(SKILLS_MANIFEST.read_text())
    return [{"type": "custom", "skill_id": entry["skill_id"], "version": "latest"} for entry in manifest.values()]


def save_generated_files(client: anthropic.Anthropic, content: list) -> None:
    for block in content:
        if block.type != "bash_code_execution_tool_result":
            continue
        result = block.content
        if result.type != "bash_code_execution_result" or not result.content:
            continue
        for file_ref in result.content:
            if file_ref.type != "bash_code_execution_output":
                continue
            metadata = client.beta.files.retrieve_metadata(file_ref.file_id)
            safe_name = Path(metadata.filename).name
            if not safe_name or safe_name in (".", ".."):
                continue
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            downloaded = client.beta.files.download(file_ref.file_id)
            downloaded.write_to_file(OUTPUT_DIR / safe_name)
            print(f"Saved {OUTPUT_DIR / safe_name}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('Usage: python scripts/agent.py "<task description>"')
    task = " ".join(sys.argv[1:])

    client = anthropic.Anthropic()
    skills = load_skills()

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={"skills": skills},
        tools=[{"type": "code_execution_20260521", "name": "code_execution"}],
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": task}],
    )

    for block in response.content:
        if block.type == "text":
            print(block.text)

    save_generated_files(client, response.content)


if __name__ == "__main__":
    main()
