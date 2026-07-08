from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_SENSITIVE_PATTERNS = (
	(re.compile(r"([?&](?:api[_-]?key|apikey|access[_-]?token|token|client[_-]?secret)=)([^&\s]+)", re.IGNORECASE), r"\1[REDACTED]"),
	(re.compile(r"\b((?:OPENALEX|IEEE|API|ACCESS|CLIENT|AUTH|BEARER|GITHUB)[A-Z0-9_]*?(?:KEY|TOKEN|SECRET))=([^\s]+)", re.IGNORECASE), r"\1=[REDACTED]"),
)


def setup_logging(log_dir: Path) -> logging.Logger:
	log_dir.mkdir(parents=True, exist_ok=True)

	logger = logging.getLogger("researcher_discovery_mvp")
	if logger.handlers:
		return logger

	logger.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

	file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
	file_handler.setFormatter(formatter)

	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(stream_handler)
	logger.propagate = False
	return logger


def sanitize_sensitive_text(value: object) -> str:
	text = str(value)
	for pattern, replacement in _SENSITIVE_PATTERNS:
		text = pattern.sub(replacement, text)
	return text


def build_source_log_entry(
	*,
	source_system: str,
	query_config: dict,
	status: str,
	returned_record_count: int = 0,
	error_message: Optional[str] = None,
) -> dict:
	return {
		"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
		"source_system": source_system,
		"source_query_id": query_config.get("id"),
		"source_query_text": query_config.get("text"),
		"topic_cluster": query_config.get("topic_cluster"),
		"status": status,
		"returned_record_count": returned_record_count,
		"error_message": sanitize_sensitive_text(error_message) if error_message else None,
	}
