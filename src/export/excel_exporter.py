from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.processing.geography_filter import continent_from_country


README_LINES = [
	"This is an evidence-backed researcher candidate list.",
	"It is not a validated sales prospect list.",
	"It should be reviewed by Sales / FAE before outreach.",
	"Blank-looking fields are replaced with short explanations so source limitations stay visible.",
	"Institution names copied from raw affiliation text should be normalized before outreach.",
	"No personal email addresses are collected by this MVP.",
	"No automated email sending is included.",
]

PAPER_COLUMNS = [
	"source_system",
	"source_query_id",
	"source_query_text",
	"topic_cluster",
	"source_record_id",
	"doi",
	"title",
	"abstract_or_summary",
	"publication_year",
	"publication_date",
	"venue_or_source",
	"publication_type",
	"citation_count",
	"topic_terms",
	"evidence_url",
	"raw_record",
]

AUTHOR_RELATION_COLUMNS = [
	"source_system",
	"source_query_id",
	"source_query_text",
	"topic_cluster",
	"source_record_id",
	"doi",
	"paper_title",
	"publication_year",
	"author_name",
	"source_author_id",
	"orcid",
	"affiliation_raw",
	"institution_name",
	"institution_id",
	"country_or_region",
	"author_position",
	"evidence_url",
]

RESEARCHER_COLUMNS = [
	"researcher_key",
	"researcher_name",
	"primary_institution",
	"country_or_region",
	"orcid",
	"source_author_ids",
	"related_paper_count",
	"latest_publication_year",
	"top_evidence_papers",
	"topic_clusters",
	"evidence_urls",
	"relevance_score",
	"relevance_level",
	"review_status",
	"notes",
]

REVIEW_COLUMNS = [
	"researcher_name",
	"primary_institution",
	"country_or_region",
	"continent",
	"latest_publication_year",
	"related_paper_count",
	"top_evidence_papers",
	"relevance_score",
	"relevance_level",
	"review_status",
	"notes",
]

DATA_SOURCE_LOG_COLUMNS = [
	"timestamp_utc",
	"source_system",
	"source_query_id",
	"source_query_text",
	"topic_cluster",
	"status",
	"returned_record_count",
	"error_message",
]

EXCEL_CELL_LIMIT = 32767

def _is_missing(value) -> bool:
	return value in (None, "", [], {})


def _missing_value_message(sheet_name: str, column: str, record: dict) -> str:
	source_system = (record.get("source_system") or "").lower()

	if column == "notes":
		return "No additional notes."
	if column == "error_message":
		return "No error." if (record.get("status") or "").lower() == "success" else "No error details returned."
	if column == "source_author_ids":
		return "No source author ID retained."
	if column == "source_author_id":
		return "No source author ID returned by source metadata."
	if column == "orcid":
		return "No ORCID found in source metadata."
	if column == "doi":
		return "DOI not returned by source."
	if column == "citation_count":
		return "Citation count not available from source."
	if column == "abstract_or_summary":
		return "No abstract or summary returned by source."
	if column == "institution_id":
		return "No structured institution ID returned by source metadata."
	if column in {"institution_name", "primary_institution"}:
		if record.get("affiliation_raw"):
			return "Structured institution metadata unavailable; see affiliation_raw."
		return "Institution not provided by source metadata."
	if column == "country_or_region":
		if source_system == "arxiv":
			return "arXiv metadata does not provide structured country/region."
		if source_system == "ieee":
			return "IEEE metadata did not provide country/region for this author."
		if record.get("affiliation_raw"):
			return "Country/region unavailable in source metadata; review affiliation_raw."
		return "Country/region not provided by source metadata."
	if column == "continent":
		return "Continent unavailable because country/region is missing or unmapped."
	if column == "venue_or_source":
		return "Venue/source not returned by source metadata."
	if column == "top_evidence_papers":
		return "No evidence paper titles retained."
	if column == "paper_title":
		return "Paper title missing from source metadata."
	if column == "publication_year":
		return "Publication year not returned by source."
	if column == "latest_publication_year":
		return "Latest publication year not available from supporting records."
	return "Not available from source metadata."


def _excel_safe_value(value):
	if isinstance(value, (dict, list)):
		value = json.dumps(value, ensure_ascii=False)

	if isinstance(value, str) and len(value) > EXCEL_CELL_LIMIT:
		suffix = "... [truncated]"
		return value[: EXCEL_CELL_LIMIT - len(suffix)] + suffix

	return value


def _frame(records: list[dict], columns: list[str], sheet_name: str) -> pd.DataFrame:
	if not records:
		return pd.DataFrame(columns=columns)
	normalized_records = []
	for record in records:
		normalized_record = {}
		for column in columns:
			if column == "continent":
				value = continent_from_country(record.get("country_or_region"))
			else:
				value = record.get(column)
			if _is_missing(value):
				value = _missing_value_message(sheet_name, column, record)
			normalized_record[column] = _excel_safe_value(value)
		normalized_records.append(normalized_record)
	frame = pd.DataFrame(normalized_records)
	for column in columns:
		if column not in frame.columns:
			frame[column] = None
	frame = frame[columns]
	return frame


def export_results(
	output_path: Path,
	query_plan: list[dict],
	paper_results: list[dict],
	author_relations: list[dict],
	researcher_candidates: list[dict],
	data_source_logs: list[dict],
) -> Path:
	output_path.parent.mkdir(parents=True, exist_ok=True)

	with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
		_frame(researcher_candidates, REVIEW_COLUMNS, "Review").to_excel(writer, sheet_name="Review", index=False)
		pd.DataFrame({"Notes": README_LINES}).to_excel(writer, sheet_name="README", index=False)
		pd.DataFrame(query_plan).to_excel(writer, sheet_name="Query_Plan", index=False)
		_frame(paper_results, PAPER_COLUMNS, "Paper_Results").to_excel(writer, sheet_name="Paper_Results", index=False)
		_frame(author_relations, AUTHOR_RELATION_COLUMNS, "Author_Paper_Relation").to_excel(writer, sheet_name="Author_Paper_Relation", index=False)
		_frame(researcher_candidates, RESEARCHER_COLUMNS, "Researcher_Candidates").to_excel(writer, sheet_name="Researcher_Candidates", index=False)
		_frame(data_source_logs, DATA_SOURCE_LOG_COLUMNS, "Data_Source_Log").to_excel(writer, sheet_name="Data_Source_Log", index=False)

	return output_path
