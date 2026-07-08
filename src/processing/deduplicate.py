from __future__ import annotations

from collections import Counter
from typing import Optional


def _clean_text(value: Optional[str]) -> Optional[str]:
	if value is None:
		return None
	cleaned = " ".join(value.strip().split())
	return cleaned or None


def create_researcher_key(author_relation: dict) -> tuple[str, Optional[str]]:
	orcid = _clean_text(author_relation.get("orcid"))
	if orcid:
		return f"orcid:{orcid.lower()}", None

	source_author_id = _clean_text(author_relation.get("source_author_id"))
	if source_author_id:
		return f"source_author_id:{source_author_id.lower()}", None

	author_name = (_clean_text(author_relation.get("author_name")) or "unknown").lower()
	institution_name = _clean_text(author_relation.get("institution_name"))
	if institution_name:
		return f"name_institution:{author_name}|{institution_name.lower()}", None

	return f"name_only:{author_name}", "Lower-confidence match using author name only."


def _join_unique(values: set[str]) -> str:
	return "; ".join(sorted(value for value in values if value))


def _build_notes(group: dict, has_primary_institution: bool, has_country: bool) -> str:
	notes = set(group["notes"])

	if group["name_only_match_count"]:
		notes.add("Lower-confidence match using author name only.")

	if not has_primary_institution:
		if group["has_affiliation_context"]:
			notes.add("Primary institution unavailable as structured metadata; review affiliation_raw in Author_Paper_Relation.")
		else:
			notes.add("Primary institution not provided by source metadata.")
	elif group["inferred_institution_count"] and not group["structured_institution_count"]:
		notes.add("Primary institution is based on raw affiliation text and may require normalization.")

	if not has_country:
		notes.add("Country/region not provided by source metadata.")

	return " ".join(sorted(notes))


def deduplicate_researchers(author_relations: list[dict]) -> list[dict]:
	grouped: dict[str, dict] = {}

	for relation in author_relations:
		key, note = create_researcher_key(relation)
		group = grouped.setdefault(
			key,
			{
				"researcher_key": key,
				"names": [],
				"institutions": [],
				"countries": [],
				"orcid": None,
				"source_author_ids": set(),
				"paper_ids": set(),
				"paper_titles": [],
				"publication_years": [],
				"topic_clusters": set(),
				"evidence_urls": set(),
				"notes": set(),
				"name_only_match_count": 0,
				"has_affiliation_context": False,
				"structured_institution_count": 0,
				"inferred_institution_count": 0,
			},
		)

		affiliation_raw = _clean_text(relation.get("affiliation_raw"))
		institution_id = _clean_text(relation.get("institution_id"))
		if affiliation_raw:
			group["has_affiliation_context"] = True

		author_name = _clean_text(relation.get("author_name"))
		if author_name:
			group["names"].append(author_name)

		institution_name = _clean_text(relation.get("institution_name"))
		if institution_name:
			group["institutions"].append(institution_name)
			if institution_id:
				group["structured_institution_count"] += 1
			elif affiliation_raw:
				group["inferred_institution_count"] += 1

		country = _clean_text(relation.get("country_or_region"))
		if country:
			group["countries"].append(country)

		if relation.get("orcid") and not group["orcid"]:
			group["orcid"] = relation.get("orcid")

		if relation.get("source_author_id"):
			group["source_author_ids"].add(relation["source_author_id"])

		if relation.get("source_record_id"):
			group["paper_ids"].add(relation["source_record_id"])

		paper_title = _clean_text(relation.get("paper_title"))
		if paper_title:
			group["paper_titles"].append((relation.get("publication_year") or 0, paper_title))

		if relation.get("publication_year") is not None:
			group["publication_years"].append(relation["publication_year"])

		if relation.get("topic_cluster"):
			group["topic_clusters"].add(relation["topic_cluster"])

		if relation.get("evidence_url"):
			group["evidence_urls"].add(relation["evidence_url"])

		if note:
			group["notes"].add(note)
			if note == "Lower-confidence match using author name only.":
				group["name_only_match_count"] += 1

	candidates = []
	for group in grouped.values():
		name_counter = Counter(group["names"])
		institution_counter = Counter(group["institutions"])
		country_counter = Counter(group["countries"])
		top_papers = []
		seen_titles = set()
		for _, title in sorted(group["paper_titles"], key=lambda item: (-item[0], item[1])):
			if title not in seen_titles:
				seen_titles.add(title)
				top_papers.append(title)
			if len(top_papers) == 5:
				break

		candidates.append(
			{
				"researcher_key": group["researcher_key"],
				"researcher_name": name_counter.most_common(1)[0][0] if name_counter else "Unknown",
				"primary_institution": institution_counter.most_common(1)[0][0] if institution_counter else None,
				"country_or_region": country_counter.most_common(1)[0][0] if country_counter else None,
				"orcid": group["orcid"],
				"source_author_ids": _join_unique(group["source_author_ids"]),
				"related_paper_count": len(group["paper_ids"]),
				"latest_publication_year": max(group["publication_years"]) if group["publication_years"] else None,
				"top_evidence_papers": "; ".join(top_papers),
				"topic_clusters": _join_unique(group["topic_clusters"]),
				"evidence_urls": _join_unique(group["evidence_urls"]),
				"relevance_score": 0,
				"relevance_level": "Low",
				"review_status": "Pending",
				"notes": _build_notes(group, bool(institution_counter), bool(country_counter)),
			}
		)

	return sorted(candidates, key=lambda candidate: (-candidate["related_paper_count"], candidate["researcher_name"]))
