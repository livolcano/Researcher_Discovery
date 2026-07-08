from __future__ import annotations

import os
import sys
from pathlib import Path


def _resource_path(relative_path: str) -> Path:
	base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
	return base_path / relative_path


def _pick_folder(initial_directory: str) -> int:
	from tkinter import Tk, filedialog

	base_directory = Path(initial_directory).expanduser() if initial_directory else Path.home()
	if not base_directory.exists():
		base_directory = Path.home()

	root = Tk()
	root.withdraw()
	try:
		root.attributes("-topmost", True)
	except Exception:
		pass

	selected_directory = filedialog.askdirectory(
		initialdir=str(base_directory),
		title="Select Excel output folder",
	)
	root.destroy()

	if selected_directory:
		print(selected_directory)
	return 0


def _run_streamlit() -> int:
	from streamlit import config as streamlit_config
	from streamlit.web import bootstrap

	script_path = _resource_path("ui_app.py")
	os.chdir(script_path.parent)

	flag_options = {
		"server.headless": False,
		"browser.gatherUsageStats": False,
		"server.fileWatcherType": "none" if getattr(sys, "frozen", False) else "auto",
	}
	streamlit_config._main_script_path = os.path.abspath(script_path)
	bootstrap.load_config_options(flag_options=flag_options)
	bootstrap.run(str(script_path), False, [], flag_options)
	return 0


def main() -> int:
	if len(sys.argv) > 1 and sys.argv[1] == "--pick-folder":
		initial_directory = sys.argv[2] if len(sys.argv) > 2 else ""
		return _pick_folder(initial_directory)

	return _run_streamlit()


if __name__ == "__main__":
	raise SystemExit(main())