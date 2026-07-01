# Jack
For Wethos 

## Running the agent

The `.skill` files in this repo are Agent Skills bundles. To turn them into a
working Claude agent:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...   # or `ant auth login`

python scripts/upload_skills.py          # registers/updates the skills with Claude, writes skills.json
python scripts/agent.py "your task here" # runs Claude with all registered skills attached
```

Re-run `upload_skills.py` whenever a `.skill` file changes — it uploads a new
version instead of duplicating the skill. Files the agent generates are saved
to `outputs/`.
