from __future__ import annotations

import logging
from typing import Optional

import requests

from src.utils.logging_utils import build_source_log_entry, sanitize_sensitive_text


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
OPENALEX_MAX_PER_PAGE = 200


def _to_positive_int(value: object, fallback: int) -> int:
	if isinstance(value, bool):
		return fallback
	if isinstance(value, int):
		return value if value > 0 else fallback
	if isinstance(value, str):
		cleaned = value.strip()
		if cleaned.isdigit():
			parsed = int(cleaned)
			return parsed if parsed > 0 else fallback
	return fallback


def search_papers(
	query_config: dict,
	settings: dict,
	logger: logging.Logger,
	api_key: Optional[str] = None,
	contact_email: Optional[str] = None,
) -> tuple[list[dict], dict]:
	target_results = _to_positive_int(settings.get("max_results_per_query", 50), 50)
	page_size = _to_positive_int(settings.get("page_size", min(target_results, OPENALEX_MAX_PER_PAGE)), min(target_results, OPENALEX_MAX_PER_PAGE))
	page_size = min(page_size, OPENALEX_MAX_PER_PAGE)
	max_pages = _to_positive_int(settings.get("max_pages", 20), 20)

	params = {
		"search": query_config.get("text", ""),
		"per-page": page_size,
	}

	from_year = settings.get("from_publication_year")
	if from_year:
		params["filter"] = f"from_publication_date:{from_year}-01-01"

	if api_key:
		params["api_key"] = api_key
	if contact_email:
		params["mailto"] = contact_email

	try:
		records: list[dict] = []
		for page in range(1, max_pages + 1):
			params["page"] = page
			response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=30)
			response.raise_for_status()
			payload = response.json()
			page_records = payload.get("results", [])
			if not isinstance(page_records, list):
				break

			records.extend(record for record in page_records if isinstance(record, dict))
			if len(records) >= target_results:
				records = records[:target_results]
				break
			if len(page_records) < page_size:
				break

		return records, build_source_log_entry(
			source_system="openalex",
			query_config=query_config,
			status="success",
			returned_record_count=len(records),
		)
	except requests.RequestException as exc:
		sanitized_error = sanitize_sensitive_text(exc)
		logger.error("OpenAlex query failed for %s: %s", query_config.get("id"), sanitized_error)
		return [], build_source_log_entry(
			source_system="openalex",
			query_config=query_config,
			status="error",
			error_message=sanitized_error,
		)
