from __future__ import annotations

from typing import Optional

import pycountry


MIDDLE_EAST_ALPHA2_CODES = {
	"AE",
	"BH",
	"CY",
	"EG",
	"IL",
	"IQ",
	"IR",
	"JO",
	"KW",
	"LB",
	"OM",
	"PS",
	"QA",
	"SA",
	"SY",
	"TR",
	"YE",
}

ALLOWED_CONTINENTS = {"APAC", "EMEA", "AMER"}


def _clean_string(value: object) -> Optional[str]:
	if isinstance(value, str):
		cleaned = value.strip()
		return cleaned or None
	return None


def normalize_country_to_english(value: object) -> Optional[str]:
	cleaned = _clean_string(value)
	if not cleaned:
		return None

	for token in (cleaned, cleaned.upper()):
		try:
			return pycountry.countries.lookup(token).name
		except LookupError:
			continue

	return cleaned


def _continent_code_from_alpha2(alpha2: Optional[str]) -> Optional[str]:
	if not alpha2:
		return None

	if alpha2 in {
		"DZ", "AO", "BJ", "BW", "BF", "BI", "CM", "CV", "CF", "TD", "KM", "CD", "CG", "CI", "DJ", "EG", "GQ", "ER", "SZ", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "LY", "MG", "MW", "ML", "MR", "MU", "YT", "MA", "MZ", "NA", "NE", "NG", "RE", "RW", "SH", "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "SD", "TZ", "TG", "TN", "UG", "EH", "ZM", "ZW",
	}:
		return "AF"
	if alpha2 in {
		"AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE", "FO", "FI", "FR", "DE", "GI", "GR", "VA", "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT", "MD", "MC", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "RU", "SM", "RS", "SK", "SI", "ES", "SJ", "SE", "CH", "UA", "GB",
	}:
		return "EU"
	if alpha2 in {
		"AG", "AI", "AW", "BS", "BB", "BZ", "BM", "BQ", "VG", "CA", "KY", "CR", "CU", "CW", "DM", "DO", "SV", "GL", "GD", "GP", "GT", "HT", "HN", "JM", "MQ", "MX", "MS", "NI", "PA", "PR", "BL", "KN", "LC", "MF", "PM", "VC", "SX", "TT", "TC", "US", "VI",
	}:
		return "NA"
	if alpha2 in {
		"AR", "BO", "BR", "CL", "CO", "EC", "FK", "GF", "GY", "PY", "PE", "SR", "UY", "VE",
	}:
		return "SA"
	if alpha2 in {
		"AF", "AM", "AZ", "BD", "BT", "BN", "KH", "CN", "GE", "HK", "IN", "ID", "JP", "KZ", "KG", "LA", "MO", "MY", "MV", "MN", "MM", "NP", "KP", "PK", "PH", "SG", "KR", "LK", "TW", "TJ", "TH", "TL", "TM", "UZ", "VN", "AE", "BH", "IL", "IQ", "IR", "JO", "KW", "LB", "OM", "PS", "QA", "SA", "SY", "TR", "YE",
	}:
		return "AS"
	if alpha2 in {
		"AS", "AU", "CK", "FJ", "PF", "GU", "KI", "MH", "FM", "NR", "NC", "NZ", "NU", "NF", "MP", "PW", "PG", "PN", "WS", "SB", "TK", "TO", "TV", "UM", "VU", "WF",
	}:
		return "OC"
	return None


def continent_from_country(country_or_region: object) -> Optional[str]:
	if not isinstance(country_or_region, str):
		return None

	cleaned = country_or_region.strip()
	if not cleaned:
		return None

	try:
		country = pycountry.countries.lookup(cleaned)
	except LookupError:
		return None

	alpha2 = getattr(country, "alpha_2", None)
	if alpha2 in MIDDLE_EAST_ALPHA2_CODES:
		return "EMEA"

	continent_code = _continent_code_from_alpha2(alpha2)
	continent_by_code = {
		"AF": "EMEA",
		"EU": "EMEA",
		"NA": "AMER",
		"SA": "AMER",
		"AS": "APAC",
		"OC": "APAC",
	}
	return continent_by_code.get(continent_code)


def build_geo_filter(settings: dict) -> dict:
	country = normalize_country_to_english(settings.get("country_or_region"))
	continent = _clean_string(settings.get("continent"))
	continent = continent.upper() if continent else None

	if continent and continent not in ALLOWED_CONTINENTS:
		raise ValueError(
			"Invalid geography filter continent. Use APAC, EMEA, or AMER."
		)

	return {
		"country_or_region": country,
		"continent": continent,
	}


def has_geo_filter(geo_filter: dict) -> bool:
	return bool(geo_filter.get("country_or_region") or geo_filter.get("continent"))


def relation_matches_geo_filter(author_relation: dict, geo_filter: dict) -> bool:
	if not has_geo_filter(geo_filter):
		return True

	country_value = normalize_country_to_english(author_relation.get("country_or_region"))
	if not country_value:
		return False

	country_filter = geo_filter.get("country_or_region")
	if country_filter and country_value.casefold() != country_filter.casefold():
		return False

	continent_filter = geo_filter.get("continent")
	if continent_filter and continent_from_country(country_value) != continent_filter:
		return False

	return True


def filter_author_relations_by_geo(author_relations: list[dict], geo_filter: dict) -> list[dict]:
	if not has_geo_filter(geo_filter):
		return author_relations

	return [
		relation
		for relation in author_relations
		if relation_matches_geo_filter(relation, geo_filter)
	]


def filter_papers_by_author_relations(paper_results: list[dict], author_relations: list[dict]) -> list[dict]:
	allowed_record_keys = {
		(str(relation.get("source_system")), str(relation.get("source_record_id")))
		for relation in author_relations
		if relation.get("source_record_id") is not None
	}

	return [
		record
		for record in paper_results
		if (str(record.get("source_system")), str(record.get("source_record_id"))) in allowed_record_keys
	]