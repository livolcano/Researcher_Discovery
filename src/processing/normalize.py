from __future__ import annotations

from datetime import datetime

import pycountry


def _clean_text(value: object) -> str | None:
	if isinstance(value, str):
		cleaned = " ".join(value.strip().split())
		return cleaned or None
	return None


def _normalize_doi(value: str | None) -> str | None:
	if not value:
		return None

	cleaned = value.strip()
	if cleaned.startswith("https://doi.org/"):
		return cleaned.replace("https://doi.org/", "", 1)
	return cleaned or None


def _normalize_orcid(value: str | None) -> str | None:
	if not value:
		return None

	cleaned = value.strip()
	if cleaned.startswith("https://orcid.org/"):
		return cleaned.replace("https://orcid.org/", "", 1)
	return cleaned or None


def _reconstruct_openalex_abstract(abstract_inverted_index: dict | None) -> str | None:
	if not abstract_inverted_index:
		return None

	max_position = max((max(positions) for positions in abstract_inverted_index.values() if positions), default=-1)
	if max_position < 0:
		return None

	words = [""] * (max_position + 1)
	for token, positions in abstract_inverted_index.items():
		for position in positions:
			if 0 <= position < len(words):
				words[position] = token

	abstract = " ".join(word for word in words if word)
	return abstract or None


def _openalex_topic_terms(record: dict) -> list[str]:
	terms: list[str] = []

	primary_topic = record.get("primary_topic") or {}
	if primary_topic.get("display_name"):
		terms.append(primary_topic["display_name"])

	for topic in record.get("topics", []):
		if topic.get("display_name"):
			terms.append(topic["display_name"])

	seen = set()
	unique_terms = []
	for term in terms:
		if term not in seen:
			seen.add(term)
			unique_terms.append(term)
	return unique_terms


def _openalex_venue(record: dict) -> str | None:
	primary_location = record.get("primary_location") or {}
	source = primary_location.get("source") or {}
	return source.get("display_name") or None


def _author_position(index: int, total: int) -> str:
	if total <= 1:
		return "single"
	if index == 0:
		return "first"
	if index == total - 1:
		return "last"
	return "middle"


def _coerce_int(value: object) -> int | None:
	if isinstance(value, bool):
		return None
	if isinstance(value, int):
		return value
	if isinstance(value, str):
		cleaned = value.strip()
		if cleaned.isdigit():
			return int(cleaned)
	return None


def _first_non_empty(record: dict, keys: tuple[str, ...]) -> str | None:
	for key in keys:
		value = record.get(key)
		if isinstance(value, str):
			cleaned = value.strip()
			if cleaned:
				return cleaned
		elif value is not None:
			return str(value)
	return None


def _string_or_none(value: object) -> str | None:
	if isinstance(value, str):
		cleaned = value.strip()
		return cleaned or None
	return None


def _normalize_country_to_english(value: object) -> str | None:
	cleaned = _string_or_none(value)
	if not cleaned:
		return None

	for token in (cleaned, cleaned.upper()):
		try:
			return pycountry.countries.lookup(token).name
		except LookupError:
			continue

	return cleaned


def _primary_institution_from_affiliation(affiliation_values: list[str]) -> str | None:
	for value in affiliation_values:
		cleaned = _clean_text(value)
		if cleaned:
			return cleaned
	return None


def _ieee_record_id(record: dict) -> str | None:
	return _first_non_empty(record, ("article_number", "articleNumber", "document_id", "doi", "html_url"))


def _ieee_topic_terms(record: dict) -> list[str]:
	terms: list[str] = []
	index_terms = record.get("index_terms")
	if isinstance(index_terms, dict):
		for term_group in index_terms.values():
			if isinstance(term_group, dict):
				group_terms = term_group.get("terms")
				if isinstance(group_terms, list):
					for term in group_terms:
						cleaned = _string_or_none(term)
						if cleaned:
							terms.append(cleaned)

	seen = set()
	unique_terms = []
	for term in terms:
		if term not in seen:
			seen.add(term)
			unique_terms.append(term)
	return unique_terms


def _ieee_authors(record: dict) -> list[dict]:
	authors = record.get("authors")
	if isinstance(authors, list):
		return [author for author in authors if isinstance(author, dict)]
	if isinstance(authors, dict):
		nested_authors = authors.get("authors")
		if isinstance(nested_authors, list):
			return [author for author in nested_authors if isinstance(author, dict)]
	return []


def normalize_openalex_papers(raw_records: list[dict], query_config: dict) -> list[dict]:
	papers = []
	for record in raw_records:
		doi = _normalize_doi(record.get("doi"))
		evidence_url = record.get("id") or (f"https://doi.org/{doi}" if doi else None)
		papers.append(
			{
				"source_system": "openalex",
				"source_query_id": query_config.get("id"),
				"source_query_text": query_config.get("text"),
				"topic_cluster": query_config.get("topic_cluster"),
				"source_record_id": record.get("id"),
				"doi": doi,
				"title": record.get("display_name") or "",
				"abstract_or_summary": _reconstruct_openalex_abstract(record.get("abstract_inverted_index")),
				"publication_year": record.get("publication_year"),
				"publication_date": record.get("publication_date"),
				"venue_or_source": _openalex_venue(record),
				"publication_type": record.get("type"),
				"citation_count": record.get("cited_by_count"),
				"topic_terms": _openalex_topic_terms(record),
				"evidence_url": evidence_url,
				"raw_record": record,
			}
		)
	return papers


def normalize_arxiv_papers(raw_records: list[dict], query_config: dict) -> list[dict]:
	papers = []
	for record in raw_records:
		published = record.get("published")
		publication_year = None
		if published:
			try:
				publication_year = datetime.fromisoformat(published.replace("Z", "+00:00")).year
			except ValueError:
				publication_year = None

		papers.append(
			{
				"source_system": "arxiv",
				"source_query_id": query_config.get("id"),
				"source_query_text": query_config.get("text"),
				"topic_cluster": query_config.get("topic_cluster"),
				"source_record_id": record.get("id"),
				"doi": _normalize_doi(record.get("doi")),
				"title": (record.get("title") or "").strip(),
				"abstract_or_summary": (record.get("summary") or None),
				"publication_year": publication_year,
				"publication_date": published,
				"venue_or_source": "arXiv",
				"publication_type": "preprint",
				"citation_count": None,
				"topic_terms": [tag.get("term") for tag in record.get("tags", []) if tag.get("term")],
				"evidence_url": record.get("id"),
				"raw_record": record,
			}
		)
	return papers


def normalize_ieee_papers(raw_records: list[dict], query_config: dict) -> list[dict]:
	papers = []
	for record in raw_records:
		doi = _normalize_doi(record.get("doi"))
		evidence_url = record.get("html_url") or (f"https://doi.org/{doi}" if doi else None)
		papers.append(
			{
				"source_system": "ieee",
				"source_query_id": query_config.get("id"),
				"source_query_text": query_config.get("text"),
				"topic_cluster": query_config.get("topic_cluster"),
				"source_record_id": _ieee_record_id(record),
				"doi": doi,
				"title": _string_or_none(record.get("title")) or "",
				"abstract_or_summary": _string_or_none(record.get("abstract")),
				"publication_year": _coerce_int(record.get("publication_year")),
				"publication_date": _string_or_none(record.get("publication_date")),
				"venue_or_source": _string_or_none(record.get("publication_title")),
				"publication_type": _string_or_none(record.get("content_type")),
				"citation_count": _coerce_int(record.get("citing_paper_count")),
				"topic_terms": _ieee_topic_terms(record),
				"evidence_url": evidence_url,
				"raw_record": record,
			}
		)
	return papers


def extract_openalex_author_relations(raw_records: list[dict], query_config: dict) -> list[dict]:
	relations = []
	for record in raw_records:
		authorships = record.get("authorships", [])
		doi = _normalize_doi(record.get("doi"))
		evidence_url = record.get("id") or (f"https://doi.org/{doi}" if doi else None)
		total_authors = len(authorships)

		for index, authorship in enumerate(authorships):
			author = authorship.get("author") or {}
			institutions = authorship.get("institutions") or []
			primary_institution = institutions[0] if institutions else {}
			raw_affiliations = [_clean_text(value) for value in authorship.get("raw_affiliation_strings", [])]
			raw_affiliations = [value for value in raw_affiliations if value]
			affiliation_raw = "; ".join(raw_affiliations) or None
			relations.append(
				{
					"source_system": "openalex",
					"source_query_id": query_config.get("id"),
					"source_query_text": query_config.get("text"),
					"topic_cluster": query_config.get("topic_cluster"),
					"source_record_id": record.get("id"),
					"doi": doi,
					"paper_title": record.get("display_name") or "",
					"publication_year": record.get("publication_year"),
					"author_name": author.get("display_name") or "",
					"source_author_id": author.get("id"),
					"orcid": _normalize_orcid(author.get("orcid")),
					"affiliation_raw": affiliation_raw,
					"institution_name": _clean_text(primary_institution.get("display_name")) or _primary_institution_from_affiliation(raw_affiliations),
					"institution_id": primary_institution.get("id"),
						"country_or_region": _normalize_country_to_english(primary_institution.get("country_code")),
					"author_position": _author_position(index, total_authors),
					"evidence_url": evidence_url,
				}
			)
	return relations


def extract_arxiv_author_relations(raw_records: list[dict], query_config: dict) -> list[dict]:
	relations = []
	for record in raw_records:
		authors = record.get("authors", [])
		total_authors = len(authors)
		published = record.get("published")
		publication_year = None
		if published:
			try:
				publication_year = datetime.fromisoformat(published.replace("Z", "+00:00")).year
			except ValueError:
				publication_year = None

		for index, author in enumerate(authors):
			affiliation_raw = _clean_text(author.get("affiliation"))
			relations.append(
				{
					"source_system": "arxiv",
					"source_query_id": query_config.get("id"),
					"source_query_text": query_config.get("text"),
					"topic_cluster": query_config.get("topic_cluster"),
					"source_record_id": record.get("id"),
					"doi": _normalize_doi(record.get("doi")),
					"paper_title": (record.get("title") or "").strip(),
					"publication_year": publication_year,
					"author_name": author.get("name") or "",
					"source_author_id": None,
					"orcid": None,
					"affiliation_raw": affiliation_raw,
					"institution_name": affiliation_raw,
					"institution_id": None,
					"country_or_region": _normalize_country_to_english(author.get("country")),
					"author_position": _author_position(index, total_authors),
					"evidence_url": record.get("id"),
				}
			)
	return relations


def extract_ieee_author_relations(raw_records: list[dict], query_config: dict) -> list[dict]:
	relations = []
	for record in raw_records:
		authors = _ieee_authors(record)
		total_authors = len(authors)
		doi = _normalize_doi(record.get("doi"))
		evidence_url = record.get("html_url") or (f"https://doi.org/{doi}" if doi else None)
		publication_year = _coerce_int(record.get("publication_year"))

		for index, author in enumerate(authors):
			affiliation_raw = _clean_text(author.get("affiliation"))
			relations.append(
				{
					"source_system": "ieee",
					"source_query_id": query_config.get("id"),
					"source_query_text": query_config.get("text"),
					"topic_cluster": query_config.get("topic_cluster"),
					"source_record_id": _ieee_record_id(record),
					"doi": doi,
					"paper_title": _string_or_none(record.get("title")) or "",
					"publication_year": publication_year,
					"author_name": _first_non_empty(author, ("full_name", "preferred_name", "name")) or "",
					"source_author_id": _first_non_empty(author, ("id", "author_id", "authorUrl")),
					"orcid": _normalize_orcid(_string_or_none(author.get("orcid"))),
					"affiliation_raw": affiliation_raw,
					"institution_name": affiliation_raw,
					"institution_id": None,
					"country_or_region": _normalize_country_to_english(_first_non_empty(author, ("country", "country_code", "country_name"))),
					"author_position": _author_position(index, total_authors),
					"evidence_url": evidence_url,
				}
			)
	return relations
