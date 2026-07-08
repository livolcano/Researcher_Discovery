from __future__ import annotations

import logging
import time
from datetime import datetime

import feedparser
import requests

from src.utils.logging_utils import build_source_log_entry


ARXIV_QUERY_URL = "https://export.arxiv.org/api/query"
_LAST_REQUEST_TIME = 0.0


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


def _entry_to_dict(entry: dict) -> dict:
	authors = []
	for author in entry.get("authors", []):
		authors.append(
			{
				"name": author.get("name"),
				"affiliation": author.get("affiliation"),
			}
		)

	tags = []
	for tag in entry.get("tags", []):
		tags.append(
			{
				"term": tag.get("term"),
				"scheme": tag.get("scheme"),
				"label": tag.get("label"),
			}
		)

	links = []
	for link in entry.get("links", []):
		links.append(
			{
				"href": link.get("href"),
				"rel": link.get("rel"),
				"type": link.get("type"),
				"title": link.get("title"),
			}
		)

	return {
		"id": entry.get("id"),
		"title": entry.get("title"),
		"summary": entry.get("summary"),
		"published": entry.get("published"),
		"updated": entry.get("updated"),
		"authors": authors,
		"tags": tags,
		"links": links,
		"doi": entry.get("arxiv_doi") or entry.get("doi"),
	}


def _passes_year_filter(record: dict, from_publication_year: int | None) -> bool:
	if not from_publication_year:
		return True

	published = record.get("published")
	if not published:
		return True

	try:
		return datetime.fromisoformat(published.replace("Z", "+00:00")).year >= from_publication_year
	except ValueError:
		return True


def _respect_rate_limit(settings: dict) -> None:
	global _LAST_REQUEST_TIME

	interval_seconds = float(settings.get("request_interval_seconds", 3.0) or 0)
	if interval_seconds <= 0:
		return

	now = time.monotonic()
	elapsed = now - _LAST_REQUEST_TIME
	if elapsed < interval_seconds:
		time.sleep(interval_seconds - elapsed)


def search_papers(query_config: dict, settings: dict, logger: logging.Logger) -> tuple[list[dict], dict]:
	target_results = _to_positive_int(settings.get("max_results_per_query", 50), 50)
	page_size = _to_positive_int(settings.get("page_size", min(target_results, 100)), min(target_results, 100))
	max_pages = _to_positive_int(settings.get("max_pages", 20), 20)

	base_params = {
		"search_query": f"all:{query_config.get('text', '')}",
		"max_results": page_size,
		"sortBy": "submittedDate",
		"sortOrder": "descending",
	}

	try:
		retry_on_429 = int(settings.get("retry_on_429", 1) or 0)
		retry_backoff_seconds = float(settings.get("retry_backoff_seconds", 6.0) or 0)
		from_year = settings.get("from_publication_year")
		records: list[dict] = []

		for page in range(max_pages):
			params = dict(base_params)
			params["start"] = page * page_size

			response = None
			for attempt in range(retry_on_429 + 1):
				_respect_rate_limit(settings)
				response = requests.get(ARXIV_QUERY_URL, params=params, timeout=30)

				global _LAST_REQUEST_TIME
				_LAST_REQUEST_TIME = time.monotonic()

				if response.status_code != 429 or attempt == retry_on_429:
					break

				logger.warning(
					"arXiv rate-limited query %s. Retrying in %.1f seconds.",
					query_config.get("id"),
					retry_backoff_seconds,
				)
				time.sleep(retry_backoff_seconds)

			assert response is not None
			response.raise_for_status()
			feed = feedparser.parse(response.text)
			page_records = [_entry_to_dict(entry) for entry in feed.entries]
			if not page_records:
				break

			if from_year:
				page_records = [record for record in page_records if _passes_year_filter(record, from_year)]

			records.extend(page_records)
			if len(records) >= target_results:
				records = records[:target_results]
				break
			if len(feed.entries) < page_size:
				break
			if from_year and not page_records:
				break

		return records, build_source_log_entry(
			source_system="arxiv",
			query_config=query_config,
			status="success",
			returned_record_count=len(records),
		)
	except requests.RequestException as exc:
		logger.error("arXiv query failed for %s: %s", query_config.get("id"), exc)
		return [], build_source_log_entry(
			source_system="arxiv",
			query_config=query_config,
			status="error",
			error_message=str(exc),
		)
