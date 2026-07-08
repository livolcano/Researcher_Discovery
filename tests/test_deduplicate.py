from src.processing.deduplicate import deduplicate_researchers


def test_orcid_based_deduplication() -> None:
	relations = [
		{
			"author_name": "Alice Chen",
			"orcid": "0000-0001-2345-6789",
			"source_author_id": None,
			"institution_name": "Tsinghua University",
			"country_or_region": "CN",
			"source_record_id": "paper-1",
			"paper_title": "Paper One",
			"publication_year": 2024,
			"topic_cluster": "Green 6G",
			"evidence_url": "https://example.org/paper-1",
		},
		{
			"author_name": "Alice Chen",
			"orcid": "0000-0001-2345-6789",
			"source_author_id": "https://openalex.org/A123",
			"institution_name": "Tsinghua University",
			"country_or_region": "CN",
			"source_record_id": "paper-2",
			"paper_title": "Paper Two",
			"publication_year": 2025,
			"topic_cluster": "6G Sustainability",
			"evidence_url": "https://example.org/paper-2",
		},
	]

	candidates = deduplicate_researchers(relations)

	assert len(candidates) == 1
	assert candidates[0]["orcid"] == "0000-0001-2345-6789"
	assert candidates[0]["related_paper_count"] == 2


def test_source_author_id_based_deduplication() -> None:
	relations = [
		{
			"author_name": "Bob Li",
			"orcid": None,
			"source_author_id": "https://openalex.org/A999",
			"institution_name": "Shanghai Jiao Tong University",
			"country_or_region": "CN",
			"source_record_id": "paper-1",
			"paper_title": "Paper One",
			"publication_year": 2024,
			"topic_cluster": "Power Efficiency",
			"evidence_url": "https://example.org/paper-1",
		},
		{
			"author_name": "B. Li",
			"orcid": None,
			"source_author_id": "https://openalex.org/A999",
			"institution_name": "Shanghai Jiao Tong University",
			"country_or_region": "CN",
			"source_record_id": "paper-2",
			"paper_title": "Paper Two",
			"publication_year": 2023,
			"topic_cluster": "Power Efficiency",
			"evidence_url": "https://example.org/paper-2",
		},
	]

	candidates = deduplicate_researchers(relations)

	assert len(candidates) == 1
	assert candidates[0]["source_author_ids"] == "https://openalex.org/A999"
	assert candidates[0]["related_paper_count"] == 2


def test_name_institution_fallback() -> None:
	relations = [
		{
			"author_name": "Carol Wang",
			"orcid": None,
			"source_author_id": None,
			"institution_name": "Southeast University",
			"country_or_region": "CN",
			"source_record_id": "paper-1",
			"paper_title": "Paper One",
			"publication_year": 2024,
			"topic_cluster": "Wireless Power Monitoring",
			"evidence_url": "https://example.org/paper-1",
		},
		{
			"author_name": "Carol Wang",
			"orcid": None,
			"source_author_id": None,
			"institution_name": "Southeast University",
			"country_or_region": "CN",
			"source_record_id": "paper-2",
			"paper_title": "Paper Two",
			"publication_year": 2025,
			"topic_cluster": "Wireless Power Monitoring",
			"evidence_url": "https://example.org/paper-2",
		},
	]

	candidates = deduplicate_researchers(relations)

	assert len(candidates) == 1
	assert candidates[0]["researcher_name"] == "Carol Wang"
	assert candidates[0]["primary_institution"] == "Southeast University"


def test_notes_explain_missing_country_and_affiliation_based_institution() -> None:
	relations = [
		{
			"author_name": "Dana Xu",
			"orcid": None,
			"source_author_id": None,
			"institution_name": "Department of Electronics, Example University",
			"institution_id": None,
			"affiliation_raw": "Department of Electronics, Example University",
			"country_or_region": None,
			"source_record_id": "paper-1",
			"paper_title": "Paper One",
			"publication_year": 2024,
			"topic_cluster": "Wireless Power Monitoring",
			"evidence_url": "https://example.org/paper-1",
		},
	]

	candidates = deduplicate_researchers(relations)

	assert len(candidates) == 1
	assert candidates[0]["primary_institution"] == "Department of Electronics, Example University"
	assert "Country/region not provided by source metadata." in candidates[0]["notes"]
	assert "Primary institution is based on raw affiliation text and may require normalization." in candidates[0]["notes"]
	assert candidates[0]["related_paper_count"] == 1
