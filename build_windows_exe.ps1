$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

python -m venv .venv-win-build
.\.venv-win-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-desktop.txt
pyinstaller --clean --noconsole --name ResearcherDiscovery --collect-all streamlit --collect-all pycountry --add-data "ui_app.py;." --add-data "config;config" --add-data "Keywords;Keywords" --add-data "data;data" --add-data "README.md;." --add-data ".env.example;." desktop_launcher.py

Write-Host "Built executable folder: dist\ResearcherDiscovery"