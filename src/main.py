from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

try:
	import truststore
except ImportError:  # pragma: no cover - optional dependency at import time
	truststore = None

from src.clients import arxiv_client, ieee_client, openalex_client
from src.export.excel_exporter import export_results
from src.processing.deduplicate import deduplicate_researchers
from src.processing.geography_filter import (
	build_geo_filter,
	filter_author_relations_by_geo,
	filter_papers_by_author_relations,
)
from src.processing.normalize import (
	extract_arxiv_author_relations,
	extract_ieee_author_relations,
	extract_openalex_author_relations,
	normalize_arxiv_papers,
	normalize_ieee_papers,
	normalize_openalex_papers,
)
from src.processing.scoring import score_researcher_candidate
from src.utils.logging_utils import setup_logging


def _load_yaml(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as handle:
		return yaml.safe_load(handle) or {}


def _save_json(path: Path, payload: list[dict]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]
	load_dotenv(project_root / ".env")

	if truststore is not None:
		truststore.inject_into_ssl()

	logger = setup_logging(project_root / "data" / "researcher_discovery_output" / "logs")
	keywords_config = _load_yaml(project_root / "config" / "keywords.yaml")
	settings = _load_yaml(project_root / "config" / "settings.yaml")

	queries = keywords_config.get("queries", [])
	source_settings = settings.get("sources", {})

	openalex_api_key = os.getenv("OPENALEX_API_KEY") or None
	ieee_api_key = os.getenv("IEEE_API_KEY") or None
	contact_email = os.getenv("CONTACT_EMAIL") or None

	all_papers: list[dict] = []
	all_author_relations: list[dict] = []
	data_source_logs: list[dict] = []

	for query_config in queries:
		openalex_settings = source_settings.get("openalex", {})
		if openalex_settings.get("enabled"):
			raw_records, source_log = openalex_client.search_papers(
				query_config,
				openalex_settings,
				logger,
				api_key=openalex_api_key,
				contact_email=contact_email,
			)
			data_source_logs.append(source_log)
			all_papers.extend(normalize_openalex_papers(raw_records, query_config))
			all_author_relations.extend(extract_openalex_author_relations(raw_records, query_config))

		arxiv_settings = source_settings.get("arxiv", {})
		if arxiv_settings.get("enabled"):
			raw_records, source_log = arxiv_client.search_papers(query_config, arxiv_settings, logger)
			data_source_logs.append(source_log)
			all_papers.extend(normalize_arxiv_papers(raw_records, query_config))
			all_author_relations.extend(extract_arxiv_author_relations(raw_records, query_config))

		ieee_settings = source_settings.get("ieee", {})
		if ieee_settings.get("enabled"):
			raw_records, source_log = ieee_client.search_papers(query_config, ieee_settings, logger, api_key=ieee_api_key)
			data_source_logs.append(source_log)
			all_papers.extend(normalize_ieee_papers(raw_records, query_config))
			all_author_relations.extend(extract_ieee_author_relations(raw_records, query_config))

	geo_filter = build_geo_filter(settings.get("geographic_filter", {}))
	filtered_author_relations = filter_author_relations_by_geo(all_author_relations, geo_filter)
	filtered_papers = filter_papers_by_author_relations(all_papers, filtered_author_relations)

	researcher_candidates = deduplicate_researchers(filtered_author_relations)
	scoring_settings = settings.get("scoring", {})
	for candidate in researcher_candidates:
		score_researcher_candidate(candidate, scoring_settings)

	researcher_candidates.sort(
		key=lambda candidate: (-candidate["relevance_score"], -candidate["related_paper_count"], candidate["researcher_name"])
	)

	output_path = project_root / settings.get("output", {}).get(
		"excel_file", "data/researcher_discovery_output/researcher_discovery_mvp.xlsx"
	)
	export_results(
		output_path=output_path,
		query_plan=queries,
		paper_results=filtered_papers,
		author_relations=filtered_author_relations,
		researcher_candidates=researcher_candidates,
		data_source_logs=data_source_logs,
	)

	_save_json(project_root / "data" / "interim" / "paper_results.json", filtered_papers)
	_save_json(project_root / "data" / "interim" / "author_relations.json", filtered_author_relations)
	_save_json(project_root / "data" / "interim" / "researcher_candidates.json", researcher_candidates)
	_save_json(project_root / "data" / "interim" / "source_logs.json", data_source_logs)

	print(f"Queries: {len(queries)}")
	print(f"Paper records: {len(filtered_papers)}")
	print(f"Author-paper relations: {len(filtered_author_relations)}")
	print(f"Researcher candidates: {len(researcher_candidates)}")
	print(f"Output file: {output_path}")


if __name__ == "__main__":
	main()
