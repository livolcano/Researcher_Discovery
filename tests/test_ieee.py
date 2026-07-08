import logging

from src.clients import ieee_client
from src.processing.normalize import extract_ieee_author_relations, normalize_ieee_papers


class _MockResponse:
	def __init__(self, payload: dict) -> None:
		self._payload = payload

	def raise_for_status(self) -> None:
		return None

	def json(self) -> dict:
		return self._payload


def test_ieee_search_and_normalize_with_mocked_response(monkeypatch) -> None:
	payload = {
		"articles": [
			{
				"article_number": "10578654",
				"doi": "10.1109/ACCESS.2024.123456",
				"title": "Energy-Efficient 6G Networks",
				"abstract": "A practical study on sustainable wireless systems.",
				"publication_year": "2024",
				"publication_date": "15 March 2024",
				"publication_title": "IEEE Access",
				"content_type": "Journals",
				"citing_paper_count": "7",
				"html_url": "https://ieeexplore.ieee.org/document/10578654/",
				"index_terms": {
					"ieee_terms": {"terms": ["Energy efficiency", "6G mobile communication"]},
					"author_terms": {"terms": ["Green networking"]},
				},
				"authors": {
					"authors": [
						{
							"full_name": "Alice Smith",
							"id": 12345,
							"orcid": "https://orcid.org/0000-0002-1825-0097",
							"country": "US",
							"affiliation": "University of Example",
						},
						{
							"full_name": "Bob Lee",
						}
					],
				},
			}
		]
	}

	def _mock_get(*args, **kwargs):
		return _MockResponse(payload)

	monkeypatch.setattr(ieee_client.requests, "get", _mock_get)

	query_config = {"id": "Q-IEEE", "text": '"6G" AND "energy efficiency"', "topic_cluster": "Green 6G"}
	settings = {"enabled": True, "max_results_per_query": 10, "from_publication_year": 2022}

	raw_records, source_log = ieee_client.search_papers(query_config, settings, logging.getLogger("test"), api_key="secret")
	papers = normalize_ieee_papers(raw_records, query_config)
	relations = extract_ieee_author_relations(raw_records, query_config)

	assert source_log["source_system"] == "ieee"
	assert source_log["status"] == "success"
	assert source_log["returned_record_count"] == 1

	assert len(papers) == 1
	paper = papers[0]
	assert paper["source_record_id"] == "10578654"
	assert paper["venue_or_source"] == "IEEE Access"
	assert paper["citation_count"] == 7
	assert paper["topic_terms"] == ["Energy efficiency", "6G mobile communication", "Green networking"]
	assert paper["evidence_url"] == "https://ieeexplore.ieee.org/document/10578654/"

	assert len(relations) == 2
	assert relations[0]["author_name"] == "Alice Smith"
	assert relations[0]["source_author_id"] == "12345"
	assert relations[0]["orcid"] == "0000-0002-1825-0097"
	assert relations[0]["affiliation_raw"] == "University of Example"
	assert relations[0]["institution_name"] == "University of Example"
	assert relations[0]["country_or_region"] == "United States"
	assert relations[1]["affiliation_raw"] is None