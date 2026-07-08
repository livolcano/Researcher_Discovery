from __future__ import annotations

import logging
from typing import Optional

import requests

from src.utils.logging_utils import build_source_log_entry, sanitize_sensitive_text


IEEE_XPLORE_QUERY_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


def _extract_articles(payload: dict) -> list[dict]:
	articles = payload.get("articles")
	if isinstance(articles, list):
		return [article for article in articles if isinstance(article, dict)]
	return []


def search_papers(
	query_config: dict,
	settings: dict,
	logger: logging.Logger,
	api_key: Optional[str] = None,
) -> tuple[list[dict], dict]:
	if not settings.get("enabled", False):
		return [], build_source_log_entry(
			source_system="ieee",
			query_config=query_config,
			status="skipped_disabled",
		)

	if not api_key:
		logger.warning("IEEE enabled but IEEE_API_KEY is missing. Skipping query %s.", query_config.get("id"))
		return [], build_source_log_entry(
			source_system="ieee",
			query_config=query_config,
			status="skipped_missing_api_key",
			error_message="IEEE_API_KEY not set",
		)

	params = {
		"apikey": api_key,
		"format": "json",
		"querytext": query_config.get("text", ""),
		"max_records": settings.get("max_results_per_query", 50),
		"start_record": 1,
	}

	from_year = settings.get("from_publication_year")
	if from_year:
		params["start_year"] = from_year

	try:
		response = requests.get(IEEE_XPLORE_QUERY_URL, params=params, timeout=30)
		response.raise_for_status()
		articles = _extract_articles(response.json())
		return articles, build_source_log_entry(
			source_system="ieee",
			query_config=query_config,
			status="success",
			returned_record_count=len(articles),
		)
	except (requests.RequestException, ValueError) as exc:
		sanitized_error = sanitize_sensitive_text(exc)
		logger.error("IEEE query failed for %s: %s", query_config.get("id"), sanitized_error)
		return [], build_source_log_entry(
			source_system="ieee",
			query_config=query_config,
			status="error",
			error_message=sanitized_error,
		)
