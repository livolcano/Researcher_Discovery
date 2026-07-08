from pathlib import Path

import pandas as pd

from src.export.excel_exporter import export_results


def test_export_results_replaces_blank_cells_with_explanations(tmp_path: Path) -> None:
	output_path = tmp_path / "researcher_discovery_mvp.xlsx"

	export_results(
		output_path=output_path,
		query_plan=[{"id": "Q01", "text": '"green 6G"', "topic_cluster": "Green 6G"}],
		paper_results=[
			{
				"source_system": "arxiv",
				"source_query_id": "Q01",
				"source_query_text": '"green 6G"',
				"topic_cluster": "Green 6G",
				"source_record_id": "arxiv:1",
				"doi": None,
				"title": "Example Paper",
				"abstract_or_summary": None,
				"publication_year": 2025,
				"publication_date": "2025-01-12",
				"venue_or_source": "arXiv",
				"publication_type": "preprint",
				"citation_count": None,
				"topic_terms": ["Green 6G"],
				"evidence_url": "http://arxiv.org/abs/2501.12345",
				"raw_record": {"id": "arxiv:1"},
			}
		],
		author_relations=[
			{
				"source_system": "arxiv",
				"source_query_id": "Q01",
				"source_query_text": '"green 6G"',
				"topic_cluster": "Green 6G",
				"source_record_id": "arxiv:1",
				"doi": None,
				"paper_title": "Example Paper",
				"publication_year": 2025,
				"author_name": "Dana Xu",
				"source_author_id": None,
				"orcid": None,
				"affiliation_raw": "Department of Electronics, Example University",
				"institution_name": None,
				"institution_id": None,
				"country_or_region": None,
				"author_position": "first",
				"evidence_url": "http://arxiv.org/abs/2501.12345",
			}
		],
		researcher_candidates=[
			{
				"researcher_key": "name_only:dana xu",
				"researcher_name": "Dana Xu",
				"primary_institution": None,
				"country_or_region": None,
				"orcid": None,
				"source_author_ids": "",
				"related_paper_count": 1,
				"latest_publication_year": 2025,
				"top_evidence_papers": "Example Paper",
				"topic_clusters": "Green 6G",
				"evidence_urls": "http://arxiv.org/abs/2501.12345",
				"relevance_score": 7,
				"relevance_level": "Medium",
				"review_status": "Pending",
				"notes": "",
			}
		],
		data_source_logs=[
			{
				"timestamp_utc": "2026-06-10T00:00:00Z",
				"source_system": "arxiv",
				"source_query_id": "Q01",
				"source_query_text": '"green 6G"',
				"topic_cluster": "Green 6G",
				"status": "success",
				"returned_record_count": 1,
				"error_message": None,
			}
		],
	)

	researchers = pd.read_excel(output_path, sheet_name="Researcher_Candidates")
	author_relations = pd.read_excel(output_path, sheet_name="Author_Paper_Relation")
	logs = pd.read_excel(output_path, sheet_name="Data_Source_Log")

	assert len(researchers) == 1
	assert researchers.loc[0, "country_or_region"] == "Country/region not provided by source metadata."
	assert author_relations.loc[0, "institution_name"] == "Structured institution metadata unavailable; see affiliation_raw."
	assert author_relations.loc[0, "country_or_region"] == "arXiv metadata does not provide structured country/region."
	assert logs.loc[0, "error_message"] == "No error."


def test_review_sheet_adds_continent_from_country(tmp_path: Path) -> None:
	output_path = tmp_path / "researcher_discovery_mvp.xlsx"

	export_results(
		output_path=output_path,
		query_plan=[],
		paper_results=[],
		author_relations=[],
		researcher_candidates=[
			{
				"researcher_key": "name_only:alice smith",
				"researcher_name": "Alice Smith",
				"primary_institution": "Example University",
				"country_or_region": "Japan",
				"orcid": None,
				"source_author_ids": "",
				"related_paper_count": 3,
				"latest_publication_year": 2025,
				"top_evidence_papers": "Example Paper",
				"topic_clusters": "Green 6G",
				"evidence_urls": "https://example.com",
				"relevance_score": 8,
				"relevance_level": "High",
				"review_status": "Pending",
				"notes": "Ready for review",
			}
		],
		data_source_logs=[],
	)

	review = pd.read_excel(output_path, sheet_name="Review")

	assert review.loc[0, "country_or_region"] == "Japan"
	assert review.loc[0, "continent"] == "APAC"


def test_review_sheet_is_first_tab(tmp_path: Path) -> None:
	output_path = tmp_path / "researcher_discovery_mvp.xlsx"

	export_results(
		output_path=output_path,
		query_plan=[],
		paper_results=[],
		author_relations=[],
		researcher_candidates=[],
		data_source_logs=[],
	)

	workbook = pd.ExcelFile(output_path)
	assert workbook.sheet_names[0] == "Review"


def test_researcher_entries_without_country_are_not_excluded_by_default(tmp_path: Path) -> None:
	output_path = tmp_path / "researcher_discovery_mvp.xlsx"

	export_results(
		output_path=output_path,
		query_plan=[],
		paper_results=[],
		author_relations=[],
		researcher_candidates=[
			{
				"researcher_key": "name_only:alice smith",
				"researcher_name": "Alice Smith",
				"primary_institution": "Example University",
				"country_or_region": "Japan",
				"orcid": None,
				"source_author_ids": "",
				"related_paper_count": 3,
				"latest_publication_year": 2025,
				"top_evidence_papers": "Paper A",
				"topic_clusters": "Green 6G",
				"evidence_urls": "https://example.com/a",
				"relevance_score": 8,
				"relevance_level": "High",
				"review_status": "Pending",
				"notes": "Ready",
			},
			{
				"researcher_key": "name_only:bob lee",
				"researcher_name": "Bob Lee",
				"primary_institution": "Unknown Institute",
				"country_or_region": None,
				"orcid": None,
				"source_author_ids": "",
				"related_paper_count": 1,
				"latest_publication_year": 2024,
				"top_evidence_papers": "Paper B",
				"topic_clusters": "Green 6G",
				"evidence_urls": "https://example.com/b",
				"relevance_score": 5,
				"relevance_level": "Low",
				"review_status": "Pending",
				"notes": "",
			},
		],
		data_source_logs=[],
	)

	researchers = pd.read_excel(output_path, sheet_name="Researcher_Candidates")
	review = pd.read_excel(output_path, sheet_name="Review")

	assert len(researchers) == 2
	assert len(review) == 2
	assert researchers.loc[0, "researcher_name"] == "Alice Smith"
	assert review.loc[0, "researcher_name"] == "Alice Smith"