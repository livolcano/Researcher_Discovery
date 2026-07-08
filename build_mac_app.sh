#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 -m venv .venv-mac-build
source .venv-mac-build/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-desktop.txt
pyinstaller --clean ResearcherDiscovery.spec

echo "Built app bundle: dist/ResearcherDiscovery.app"