from src.processing.normalize import (
	extract_arxiv_author_relations,
	extract_openalex_author_relations,
	normalize_arxiv_papers,
	normalize_openalex_papers,
)


def test_normalize_openalex_paper_fields() -> None:
	raw_records = [
		{
			"id": "https://openalex.org/W123",
			"doi": "https://doi.org/10.1000/example",
			"display_name": "Energy-Efficient 6G Networks",
			"abstract_inverted_index": {
				"Energy": [0],
				"efficient": [1],
				"wireless": [2],
				"systems": [3],
			},
			"publication_year": 2024,
			"publication_date": "2024-03-15",
			"type": "article",
			"cited_by_count": 12,
			"primary_location": {"source": {"display_name": "IEEE Access"}},
			"primary_topic": {"display_name": "Energy efficiency"},
			"topics": [{"display_name": "Green 6G"}],
		}
	]
	query_config = {"id": "Q01", "text": '"6G" AND "energy efficiency"', "topic_cluster": "Green 6G"}

	papers = normalize_openalex_papers(raw_records, query_config)

	assert len(papers) == 1
	paper = papers[0]
	assert paper["source_system"] == "openalex"
	assert paper["source_query_id"] == "Q01"
	assert paper["source_record_id"] == "https://openalex.org/W123"
	assert paper["doi"] == "10.1000/example"
	assert paper["title"] == "Energy-Efficient 6G Networks"
	assert paper["abstract_or_summary"] == "Energy efficient wireless systems"
	assert paper["publication_year"] == 2024
	assert paper["venue_or_source"] == "IEEE Access"
	assert paper["topic_terms"] == ["Energy efficiency", "Green 6G"]
	assert paper["evidence_url"] == "https://openalex.org/W123"


def test_normalize_arxiv_paper_fields() -> None:
	raw_records = [
		{
			"id": "http://arxiv.org/abs/2501.12345",
			"title": " Green 6G Resource Optimization ",
			"summary": "A preprint about sustainable wireless systems.",
			"published": "2025-01-12T00:00:00Z",
			"doi": "10.48550/arXiv.2501.12345",
			"tags": [{"term": "cs.NI"}, {"term": "eess.SP"}],
		}
	]
	query_config = {"id": "Q02", "text": '"green 6G"', "topic_cluster": "Green 6G"}

	papers = normalize_arxiv_papers(raw_records, query_config)

	assert len(papers) == 1
	paper = papers[0]
	assert paper["source_system"] == "arxiv"
	assert paper["source_record_id"] == "http://arxiv.org/abs/2501.12345"
	assert paper["title"] == "Green 6G Resource Optimization"
	assert paper["abstract_or_summary"] == "A preprint about sustainable wireless systems."
	assert paper["publication_year"] == 2025
	assert paper["publication_type"] == "preprint"
	assert paper["topic_terms"] == ["cs.NI", "eess.SP"]
	assert paper["evidence_url"] == "http://arxiv.org/abs/2501.12345"


def test_author_relation_country_normalized_to_english() -> None:
	openalex_records = [
		{
			"id": "https://openalex.org/W123",
			"display_name": "Energy-Efficient 6G Networks",
			"publication_year": 2024,
			"doi": "https://doi.org/10.1000/example",
			"authorships": [
				{
					"author": {"display_name": "Alice", "id": "https://openalex.org/A1", "orcid": None},
					"institutions": [{"display_name": "Example University", "id": "https://openalex.org/I1", "country_code": "CN"}],
					"raw_affiliation_strings": [],
				}
			],
		}
	]

	arxiv_records = [
		{
			"id": "http://arxiv.org/abs/2501.12345",
			"title": "Test",
			"published": "2025-01-12T00:00:00Z",
			"authors": [{"name": "Bob", "country": "JP", "affiliation": "Example Lab"}],
		}
	]

	query_config = {"id": "Q01", "text": "test", "topic_cluster": "test"}

	openalex_relations = extract_openalex_author_relations(openalex_records, query_config)
	arxiv_relations = extract_arxiv_author_relations(arxiv_records, query_config)

	assert openalex_relations[0]["country_or_region"] == "China"
	assert arxiv_relations[0]["country_or_region"] == "Japan"
