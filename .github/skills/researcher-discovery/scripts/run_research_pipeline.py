from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CONTINENT_CHOICES = ("APAC", "EMEA", "AMER")


def _find_project_root(start_path: Path) -> Path:
	for candidate in [start_path, *start_path.parents]:
		if (candidate / "src" / "main.py").exists():
			return candidate
	raise RuntimeError("Could not locate project root containing src/main.py.")


def _parse_keyword_text(raw: str) -> list[str]:
	fragments = []
	for chunk in raw.replace("\n", ";").split(";"):
		cleaned = chunk.strip()
		if cleaned:
			fragments.append(cleaned)
	return fragments


def _render_markdown_table(top_candidates: list[dict]) -> str:
	if not top_candidates:
		return "No candidates found."

	headers = [
		"Rank",
		"Researcher",
		"Institution",
		"Country/Region",
		"Score",
		"Level",
		"Papers",
		"Latest Year",
	]
	lines = ["| " + " | ".join(headers) + " |", "|---|---|---|---|---:|---|---:|---:|"]
	for index, candidate in enumerate(top_candidates, start=1):
		row = [
			str(index),
			str(candidate.get("researcher_name") or "").replace("|", "\\|"),
			str(candidate.get("primary_institution") or "").replace("|", "\\|"),
			str(candidate.get("country_or_region") or "").replace("|", "\\|"),
			str(candidate.get("relevance_score") or 0),
			str(candidate.get("relevance_level") or ""),
			str(candidate.get("related_paper_count") or 0),
			str(candidate.get("latest_publication_year") or ""),
		]
		lines.append("| " + " | ".join(row) + " |")
	return "\n".join(lines)


def _collect_interactive_inputs(default_top_n: int) -> dict:
	print("Researcher Discovery Interactive Mode")
	print("Enter required and optional filters. Press Enter to skip optional values.")

	keywords = []
	while not keywords:
		keywords_raw = input('Keywords (required, use ";" to separate multiple keywords): ').strip()
		keywords = _parse_keyword_text(keywords_raw)
		if not keywords:
			print("At least one keyword is required.")

	country = input("Country/Region (optional): ").strip() or None

	continent = None
	while continent is None:
		continent_raw = input("Continent (optional: APAC, EMEA, AMER): ").strip().upper()
		if not continent_raw:
			break
		if continent_raw in CONTINENT_CHOICES:
			continent = continent_raw
		else:
			print("Invalid continent. Please choose APAC, EMEA, or AMER.")

	top_n_raw = input(f"Top N candidates (default {default_top_n}): ").strip()
	if top_n_raw:
		top_n = int(top_n_raw)
	else:
		top_n = default_top_n

	output = input("Excel output path override (optional): ").strip() or None
	json_output = input("JSON summary output path (optional): ").strip() or None

	format_choice = None
	while format_choice is None:
		format_raw = input("Display format (json/table/both, default both): ").strip().lower()
		if not format_raw:
			format_choice = "both"
		elif format_raw in ("json", "table", "both"):
			format_choice = format_raw
		else:
			print("Invalid format. Choose json, table, or both.")

	return {
		"keywords": keywords,
		"country": country,
		"continent": continent,
		"top_n": top_n,
		"output": output,
		"json_output": json_output,
		"format": format_choice,
	}


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Run researcher discovery and print shortlist + scoring summary."
	)
	parser.add_argument(
		"--keywords",
		nargs="+",
		help='One or more keywords, e.g. --keywords "Open RAN" "6G ISAC".',
	)
	parser.add_argument("--interactive", action="store_true", help="Collect inputs interactively in terminal prompts.")
	parser.add_argument("--country", help="Optional country_or_region filter.", default=None)
	parser.add_argument(
		"--continent",
		choices=list(CONTINENT_CHOICES),
		help="Optional continent filter.",
		default=None,
	)
	parser.add_argument("--top-n", type=int, default=20, help="How many top candidates to include in summary.")
	parser.add_argument(
		"--output",
		help="Optional Excel output path override. Relative paths are resolved from project root.",
		default=None,
	)
	parser.add_argument(
		"--json-output",
		help="Optional path to save the summary JSON output.",
		default=None,
	)
	parser.add_argument(
		"--format",
		choices=["json", "table", "both"],
		default="both",
		help="Console output format. 'table' prints markdown table for top candidates.",
	)
	return parser


def main() -> None:
	args = _build_parser().parse_args()
	if args.interactive:
		interactive_values = _collect_interactive_inputs(args.top_n)
		keywords = interactive_values["keywords"]
		country = interactive_values["country"]
		continent = interactive_values["continent"]
		top_n = interactive_values["top_n"]
		output = interactive_values["output"]
		json_output = interactive_values["json_output"]
		output_format = interactive_values["format"]
	else:
		if not args.keywords:
			raise ValueError("Either provide --keywords or use --interactive.")
		keywords = args.keywords
		country = args.country
		continent = args.continent
		top_n = args.top_n
		output = args.output
		json_output = args.json_output
		output_format = args.format

	skill_script_path = Path(__file__).resolve()
	project_root = _find_project_root(skill_script_path)
	sys.path.insert(0, str(project_root))

	from src.main import build_queries_from_keywords, run_pipeline

	queries = build_queries_from_keywords(keywords)
	geo_filter_override = {
		"country_or_region": country,
		"continent": continent,
	}
	output_override = None
	if output:
		output_path = Path(output).expanduser()
		output_override = output_path if output_path.is_absolute() else (project_root / output_path)

	results = run_pipeline(
		project_root=project_root,
		queries_override=queries,
		geo_filter_override=geo_filter_override,
		output_path_override=output_override,
	)

	top_n = max(top_n, 1)
	top_candidates = []
	for candidate in results["researcher_candidates"][:top_n]:
		top_candidates.append(
			{
				"researcher_name": candidate.get("researcher_name"),
				"primary_institution": candidate.get("primary_institution"),
				"country_or_region": candidate.get("country_or_region"),
				"relevance_score": candidate.get("relevance_score"),
				"relevance_level": candidate.get("relevance_level"),
				"related_paper_count": candidate.get("related_paper_count"),
				"latest_publication_year": candidate.get("latest_publication_year"),
			}
		)

	summary = {
		"query_count": len(results["queries"]),
		"paper_count": len(results["paper_results"]),
		"author_relation_count": len(results["author_relations"]),
		"candidate_count": len(results["researcher_candidates"]),
		"excel_output_path": str(results["output_path"]),
		"top_candidates": top_candidates,
	}

	if json_output:
		json_output_path = Path(json_output).expanduser()
		if not json_output_path.is_absolute():
			json_output_path = project_root / json_output_path
		json_output_path.parent.mkdir(parents=True, exist_ok=True)
		json_output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

	if output_format in ("table", "both"):
		print(_render_markdown_table(top_candidates))
	if output_format in ("json", "both"):
		print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
