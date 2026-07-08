from PyInstaller.utils.hooks import collect_all


streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")
pycountry_datas, pycountry_binaries, pycountry_hiddenimports = collect_all("pycountry")


datas = [
	("ui_app.py", "."),
	("config", "config"),
	("Keywords", "Keywords"),
	("data", "data"),
	("README.md", "."),
	(".env.example", "."),
] + streamlit_datas + pycountry_datas

binaries = streamlit_binaries + pycountry_binaries
hiddenimports = streamlit_hiddenimports + pycountry_hiddenimports


a = Analysis(
	["desktop_launcher.py"],
	pathex=[],
	binaries=binaries,
	datas=datas,
	hiddenimports=hiddenimports,
	hookspath=[],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[],
	noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
	pyz,
	a.scripts,
	[],
	exclude_binaries=True,
	name="ResearcherDiscovery",
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=False,
)

coll = COLLECT(
	exe,
	a.binaries,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name="ResearcherDiscovery",
)

app = BUNDLE(
	coll,
	name="ResearcherDiscovery.app",
	icon=None,
	bundle_identifier=None,
)