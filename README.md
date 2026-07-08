# Researcher Discovery MVP

Researcher Discovery MVP is a lightweight research scouting tool that searches public academic metadata sources and produces a shortlist of researcher candidates related to a chosen topic.

The project is designed for fast early-stage discovery rather than full sales automation. It helps teams identify researchers, review supporting publications, and export results into Excel for manual follow-up.

## What This Project Does

This project:

- searches academic metadata from OpenAlex, arXiv, and optionally IEEE Xplore
- accepts topic keywords or search queries
- collects paper, author, affiliation, and publication metadata
- normalizes records from multiple sources into a common structure
- deduplicates researchers across sources
- applies simple rule-based scoring for prioritization
- exports results to Excel for review

This project does not:

- send outreach emails
- scrape private contact details
- write back to CRM systems
- replace manual review and business judgment

## Typical Output

The main output is an Excel workbook containing:

- a review sheet with ranked researcher candidates
- paper-level results
- author-paper relationship data
- source logs for traceability

The generated shortlist should be treated as an evidence-backed research candidate list, not as a validated prospect list.

## Main Components

- [src/main.py](src/main.py): pipeline entry point
- [ui_app.py](ui_app.py): Streamlit user interface
- [config/keywords.yaml](config/keywords.yaml): keyword or query configuration
- [config/settings.yaml](config/settings.yaml): source settings, filters, and output configuration
- [src/clients](src/clients): source-specific API clients
- [src/processing](src/processing): normalization, deduplication, filtering, and scoring logic
- [src/export/excel_exporter.py](src/export/excel_exporter.py): Excel export

## API Keys

The project currently supports three data sources. Not all of them require an API key.

### arXiv

- Uses the official arXiv API
- Does not require an API key
- The project already includes request throttling for arXiv

### OpenAlex

- Uses the official OpenAlex API
- Can work without a key, but rate limits and stability are better with one
- A free API key is recommended

Recommended steps:

1. Create an account on the OpenAlex website.
2. Sign in and open the API settings page.
3. Generate or copy your API key.
4. Save it in your local `.env` file as `OPENALEX_API_KEY`.
5. Also set `CONTACT_EMAIL` to follow OpenAlex polite-pool guidance.

If you do not want to apply for a key immediately, you can leave `OPENALEX_API_KEY` empty and the project will usually still run.

### IEEE Xplore

- Uses the IEEE Xplore Metadata API
- Requires an API key
- If no key is provided, the project can skip IEEE and continue with other sources

Recommended steps:

1. Open the IEEE Developer Portal.
2. Register a developer account.
3. Locate the IEEE Xplore Metadata API.
4. Apply for or subscribe to the available access plan.
5. Save the key in your local `.env` file as `IEEE_API_KEY`.
6. Validate that your first request is not blocked by permission or quota errors.

If you do not have an IEEE key yet, you can disable IEEE in [config/settings.yaml](config/settings.yaml) and run the project with OpenAlex and arXiv only.

## Running the Desktop App

This project can be distributed as a desktop app so non-software-engineering users do not need to run commands manually.

### For End Users

If you already received a packaged build from someone else:

- On Windows, launch the provided `.exe` application.
- On macOS, open the provided `.app` bundle.

The desktop app opens the UI directly and allows users to:

- enter keywords
- optionally filter by continent and country
- choose a local output folder
- set the Excel file name
- run the search and download or save the results

If macOS blocks the app on first launch, use right-click and select `Open`, or allow it in System Settings.

### For Internal Packaging

Desktop packaging files are included in this repository:

- [desktop_launcher.py](desktop_launcher.py): desktop entry point
- [ResearcherDiscovery.spec](ResearcherDiscovery.spec): PyInstaller spec for macOS packaging
- [build_mac_app.sh](build_mac_app.sh): macOS build script
- [build_windows_exe.ps1](build_windows_exe.ps1): Windows build script
- [requirements-desktop.txt](requirements-desktop.txt): packaging-only dependencies

Build outputs:

- macOS: `dist/ResearcherDiscovery.app`
- Windows: `dist/ResearcherDiscovery/` with the executable build contents

Windows builds must be created on Windows. macOS app bundles must be created on macOS.

## Local Configuration

Local secrets should be stored in a `.env` file created from [.env.example](.env.example).

Minimal example:

```text
OPENALEX_API_KEY=
IEEE_API_KEY=
CONTACT_EMAIL=your.name@your-company.com
```

Do not commit real API keys to Git.

## Notes

- Metadata quality depends on the source system.
- Researcher deduplication is heuristic, not a full academic identity resolution system.
- Missing institution or country fields are often caused by incomplete upstream metadata rather than application failure.
- Results should always be manually reviewed before outreach or commercial decisions.
