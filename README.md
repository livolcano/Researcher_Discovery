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

## Runtime Requirement

- Python 3.14 (recommended: 3.14.6)

Recommended local setup commands:

```bash
python3.14 --version
python3.14 -m venv .venv-mac
source .venv-mac/bin/activate
pip install -r requirements.txt
```

If `python3` points to an older system Python on macOS, use `python3.14` explicitly.

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

## Guided Setup with GitHub Copilot

If you are not a software engineer but you do have GitHub Copilot in VS Code, you can use Copilot as a step-by-step assistant to get this project running locally.

Recommended workflow:

1. Open VS Code.
2. Open the GitHub Copilot chat panel.
3. Open an empty folder or the folder where you want to clone this repository.
4. Copy the prompt below into Copilot chat.
5. Let Copilot guide you one step at a time instead of trying to do everything manually.

Suggested prompt for Copilot:

```text
I am not a software engineer. Please help me run this project locally from start to finish.

Work step by step and wait for me at each major checkpoint.

My goals are:
1. Check whether my local machine is ready.
2. Check Python version and any missing tools.
3. Clone this GitHub repository into my local machine.
4. Open the cloned project in VS Code.
5. Create and activate a virtual environment.
6. Install dependencies from requirements.txt.
7. Create a local .env file from .env.example.
8. Explain which API keys are required, which are optional, and where to paste them.
9. Help me decide whether to disable IEEE if I do not have an IEEE API key yet.
10. Run the project locally.
11. Help me start the Streamlit UI version.
12. Verify that the output Excel file is generated correctly.
13. If anything fails, diagnose the problem and give me the smallest possible fix.

Important rules:
- Do not rewrite the project.
- Do not refactor code unless absolutely necessary.
- Prefer minimal fixes.
- Tell me exactly which terminal command to run when needed.
- Explain each step in simple language.
- Assume I am unfamiliar with Python environments.
```

What Copilot should help you confirm during setup:

- Git is installed and can clone the repository.
- A compatible Python version is available.
- The virtual environment is created successfully.
- All dependencies are installed.
- `.env` exists and contains the required variables.
- OpenAlex works with or without a key.
- IEEE is disabled if no IEEE API key is available.
- The Streamlit UI launches successfully on your local machine.

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
