---
name: researcher-discovery
description: "Use when running the Researcher Discovery workflow to generate candidate researcher shortlist and relevance scoring from topic keywords, geography filters, and source settings (OpenAlex/arXiv/IEEE). Triggers: researcher discovery, candidate list, shortlist, relevance score, scoring result, OpenAlex, arXiv."
argument-hint: "<keywords and optional geography filters>"
---

# Researcher Discovery Workflow

Run this skill when you need two outputs from this project:

1. Candidate researcher shortlist
2. Relevance scoring results

## When to Use

- Build a ranked researcher candidate list for one or more topics
- Re-run discovery with different keyword sets
- Apply optional geography filters (`country_or_region`, `continent`)
- Produce a machine-readable summary for downstream review

## Inputs to Collect First

- Keywords (required, one or more)
- Country (optional)
- Continent (optional; one of `APAC`, `EMEA`, `AMER`)
- Top N candidates to display (optional; default `20`)
- Excel output path override (optional)

## Procedure

1. Confirm required environment is ready (`.env`, dependencies, source toggles in `config/settings.yaml`).
2. Collect inputs interactively in chat, one question at a time:
   - Ask keywords first (required)
   - Then ask optional geography filters (`country_or_region`, `continent`)
   - Ask top N (default `20`) and optional output overrides
3. Run the workflow script with interactive mode or explicit arguments:
   - [run_research_pipeline.py](./scripts/run_research_pipeline.py)
4. Return:
   - concise run summary
   - top candidate rows with score and level (markdown table)
   - generated Excel path
5. If the user asks to tune ranking behavior, update `config/settings.yaml` scoring thresholds and rerun.

## Command Examples

```bash
python .github/skills/researcher-discovery/scripts/run_research_pipeline.py \
  --interactive
```

```bash
python .github/skills/researcher-discovery/scripts/run_research_pipeline.py \
  --keywords "Open RAN" "6G ISAC" \
  --country Japan \
  --continent APAC \
  --top-n 15 \
  --format both
```

```bash
python .github/skills/researcher-discovery/scripts/run_research_pipeline.py \
  --keywords "sustainable wireless" \
  --format table \
  --json-output data/interim/researcher_discovery_summary.json
```
