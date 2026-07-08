import pytest

from src.processing.geography_filter import (
	build_geo_filter,
	filter_author_relations_by_geo,
	filter_papers_by_author_relations,
)


def test_empty_geo_filter_keeps_all_relations() -> None:
	author_relations = [
		{"source_system": "openalex", "source_record_id": "1", "country_or_region": "Japan"},
		{"source_system": "openalex", "source_record_id": "2", "country_or_region": None},
	]

	geo_filter = build_geo_filter({"country_or_region": "", "continent": ""})
	filtered = filter_author_relations_by_geo(author_relations, geo_filter)

	assert len(filtered) == 2


def test_country_filter_only_keeps_matching_country() -> None:
	author_relations = [
		{"source_system": "openalex", "source_record_id": "1", "country_or_region": "JP"},
		{"source_system": "openalex", "source_record_id": "2", "country_or_region": "China"},
	]

	geo_filter = build_geo_filter({"country_or_region": "Japan", "continent": ""})
	filtered = filter_author_relations_by_geo(author_relations, geo_filter)

	assert len(filtered) == 1
	assert filtered[0]["source_record_id"] == "1"


def test_continent_filter_only_keeps_matching_continent() -> None:
	author_relations = [
		{"source_system": "openalex", "source_record_id": "1", "country_or_region": "Germany"},
		{"source_system": "openalex", "source_record_id": "2", "country_or_region": "Japan"},
		{"source_system": "openalex", "source_record_id": "3", "country_or_region": "Canada"},
	]

	geo_filter = build_geo_filter({"country_or_region": "", "continent": "APAC"})
	filtered = filter_author_relations_by_geo(author_relations, geo_filter)

	assert len(filtered) == 1
	assert filtered[0]["source_record_id"] == "2"


def test_invalid_continent_raises_error() -> None:
	with pytest.raises(ValueError):
		build_geo_filter({"country_or_region": "", "continent": "ASIA"})


def test_filter_papers_keeps_only_records_linked_to_filtered_relations() -> None:
	papers = [
		{"source_system": "openalex", "source_record_id": "1", "title": "A"},
		{"source_system": "openalex", "source_record_id": "2", "title": "B"},
		{"source_system": "ieee", "source_record_id": "1", "title": "C"},
	]
	author_relations = [
		{"source_system": "openalex", "source_record_id": "1", "country_or_region": "Japan"},
		{"source_system": "ieee", "source_record_id": "1", "country_or_region": "Japan"},
	]

	filtered = filter_papers_by_author_relations(papers, author_relations)

	assert len(filtered) == 2
	assert {record["title"] for record in filtered} == {"A", "C"}