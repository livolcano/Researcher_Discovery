from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.main import build_queries_from_keywords, run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent
CONTINENT_OPTIONS = ["", "APAC", "EMEA", "AMER"]
RESULT_COLUMNS = [
	"researcher_name",
	"primary_institution",
	"country_or_region",
	"related_paper_count",
	"latest_publication_year",
	"relevance_level",
]


def _default_output_directory() -> Path:
	if getattr(sys, "frozen", False):
		return Path.home() / "Documents" / "Researcher Discovery Output"
	return PROJECT_ROOT / "data" / "researcher_discovery_output"


DEFAULT_OUTPUT_DIR = _default_output_directory()


def _parse_keywords(raw_value: str) -> list[str]:
	return [line.strip() for line in raw_value.splitlines() if line.strip()]


def _default_output_filename() -> str:
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	return f"Researcher Discovery {timestamp}.xlsx"


def _resolve_output_path(directory_value: str, filename_value: str) -> Path:
	directory_text = directory_value.strip()
	filename_text = filename_value.strip()

	if not filename_text:
		raise ValueError("Please provide an Excel file name.")
	if not filename_text.lower().endswith(".xlsx"):
		filename_text = f"{filename_text}.xlsx"

	base_directory = Path(directory_text).expanduser() if directory_text else DEFAULT_OUTPUT_DIR
	if not base_directory.is_absolute():
		base_directory = PROJECT_ROOT / base_directory

	return base_directory / filename_text


def _choose_output_directory(initial_directory: str) -> str:
	if getattr(sys, "frozen", False):
		command = [sys.executable, "--pick-folder", initial_directory]
	else:
		command = [sys.executable, str(PROJECT_ROOT / "desktop_launcher.py"), "--pick-folder", initial_directory]

	result = subprocess.run(command, capture_output=True, text=True)
	if result.returncode != 0:
		return initial_directory

	selected_directory = result.stdout.strip()
	return selected_directory or initial_directory


def _results_table(candidates: list[dict]) -> pd.DataFrame:
	frame = pd.DataFrame(candidates)
	if frame.empty:
		return pd.DataFrame(columns=RESULT_COLUMNS)

	available_columns = [column for column in RESULT_COLUMNS if column in frame.columns]
	return frame[available_columns]


st.set_page_config(page_title="Researcher Discovery", page_icon="Search", layout="centered")

if "output_directory" not in st.session_state:
	st.session_state["output_directory"] = str(DEFAULT_OUTPUT_DIR)
if "output_filename" not in st.session_state:
	st.session_state["output_filename"] = _default_output_filename()

st.title("Researcher Discovery")
st.caption("Enter keywords and optional geography filters to generate researcher candidates.")

folder_display_col, folder_action_col = st.columns([4, 1])
folder_display_col.text_input(
	"Excel output folder",
	value=st.session_state["output_directory"],
	disabled=True,
)
if folder_action_col.button("Choose Folder", use_container_width=True):
	st.session_state["output_directory"] = _choose_output_directory(st.session_state["output_directory"])
	st.rerun()

with st.form("search_form"):
	keywords_value = st.text_area(
		"Keywords",
		placeholder='One keyword or search query per line, for example:\n"Open RAN"\n"6G" AND "ISAC"',
		height=180,
	)
	continent_value = st.selectbox("Continent (optional)", CONTINENT_OPTIONS, index=0)
	country_value = st.text_input("Country (optional)", placeholder="For example: Japan")
	output_filename_value = st.text_input(
		"Excel file name",
		value=st.session_state["output_filename"],
		placeholder="For example: researcher_search.xlsx",
	)
	submitted = st.form_submit_button("Start Search", use_container_width=True)

if submitted:
	keywords = _parse_keywords(keywords_value)
	if not keywords:
		st.error("Please enter at least one keyword.")
	else:
		status_box = st.status("Running normally...", expanded=False)
		try:
			st.session_state["output_filename"] = output_filename_value
			queries = build_queries_from_keywords(keywords)
			geo_filter = {
				"country_or_region": country_value.strip() or None,
				"continent": continent_value or None,
			}
			output_path = _resolve_output_path(st.session_state["output_directory"], output_filename_value)

			results = run_pipeline(
				project_root=PROJECT_ROOT,
				queries_override=queries,
				geo_filter_override=geo_filter,
				output_path_override=output_path,
			)
			status_box.update(label="Completed", state="complete")
		except Exception as exc:
			status_box.update(label="Aborted unexpectedly", state="error")
			st.error(f"Search failed: {exc}")
		else:
			query_count = len(results["queries"])
			paper_count = len(results["paper_results"])
			relation_count = len(results["author_relations"])
			candidate_count = len(results["researcher_candidates"])

			col1, col2 = st.columns(2)
			col1.metric("Queries", query_count)
			col1.metric("Papers", paper_count)
			col2.metric("Relations", relation_count)
			col2.metric("Candidates", candidate_count)

			st.dataframe(_results_table(results["researcher_candidates"]), use_container_width=True, hide_index=True)
			st.caption(f"Excel output: {results['output_path']}")

			with results["output_path"].open("rb") as handle:
				st.download_button(
					"Download Excel",
					data=handle.read(),
					file_name=results["output_path"].name,
					mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					use_container_width=True,
				)