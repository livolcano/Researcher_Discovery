from __future__ import annotations


TOPIC_SIGNAL_TERMS = (
	"energy efficiency",
	"power efficiency",
	"sustainability",
	"green 6g",
)


def score_researcher_candidate(candidate: dict, settings: dict) -> dict:
	score = 0
	topic_clusters = (candidate.get("topic_clusters") or "").lower()
	latest_publication_year = candidate.get("latest_publication_year")
	recent_year_threshold = settings.get("recent_year_threshold")

	if any(term in topic_clusters for term in TOPIC_SIGNAL_TERMS):
		score += 3

	if recent_year_threshold and latest_publication_year and latest_publication_year >= recent_year_threshold:
		score += 2

	if (candidate.get("related_paper_count") or 0) >= 2:
		score += 2

	if candidate.get("evidence_urls"):
		score += 1

	if candidate.get("primary_institution"):
		score += 1

	if candidate.get("orcid") or candidate.get("source_author_ids"):
		score += 1

	candidate["relevance_score"] = score

	high_threshold = settings.get("high_relevance_min_score", 8)
	medium_threshold = settings.get("medium_relevance_min_score", 5)
	if score >= high_threshold:
		candidate["relevance_level"] = "High"
	elif score >= medium_threshold:
		candidate["relevance_level"] = "Medium"
	else:
		candidate["relevance_level"] = "Low"

	return candidate
