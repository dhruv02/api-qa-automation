# Python API QA Automation Framework

A stand-alone **pytest + Requests + JSON Schema** framework that exercises a real, disposable local HTTP API. Designed to demonstrate automated API testing and CI/CD skills to QA Automation and SDET recruiters.

## Testing capabilities

- **HTTP integration tests:** execute real requests over localhost, not direct function calls.
- **Contract validation:** assert JSON schema, field types, allowed values and required properties.
- **Positive + negative tests:** create/read/delete tickets, filtering, pagination and `401`/`404`/`422` error handling.
- **Parameterized tests:** test multiple priorities and malformed payloads with small, reusable fixtures.
- **Independent runs:** start a short-lived FastAPI demo server and reset state before each test.
- **Automated reporting:** export JUnit XML reports in GitHub Actions on Python 3.11 and 3.12.

## Stack

Python 3.11+, pytest, Requests, JSON Schema, FastAPI, Uvicorn, GitHub Actions.

## Setup in VS Code

1. Install Python 3.11+ and VS Code with the Python extension.
2. Open this folder and open the integrated terminal.
3. Create a local environment and install dependencies:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```
4. Execute the suite:
   ```bash
   python -m pytest -v
   ```

The pytest session starts its own server on a free localhost port, so **no separate server setup** is required.

## Run individual categories

```bash
python -m pytest -m smoke -v
python -m pytest -m auth -v
python -m pytest -m contract -v
python -m pytest -m negative -v
python -m pytest --junitxml=reports/results.xml
```

The tests are built around `GET /health`, `GET/POST /tickets`, and `GET/DELETE /tickets/{id}` with a demo-only API key and `/_test/reset` endpoint.

## Test project structure

```text
demo_service/app.py        Small disposable ticket API running locally
tests/conftest.py          Session-scoped server, request/session fixtures, reset
tests/test_smoke_and_auth.py   Health and unauthorized request tests
tests/test_ticket_contract.py Contract, CRUD lifecycle and error-path tests
.github/workflows/tests.yml  CI matrix with JUnit report artifacts
```

## Safety and test isolation

- **Never set `API_BASE_URL` to a live production API.** The test suite creates and deletes data and requires a disposable server with a working `/_test/reset` endpoint.
- The built-in `local-demo-key` is intentionally fake and is **not an example of secure production authentication**. The demo server binds to `127.0.0.1` and resets data only when `DEMO_TEST_MODE=1`.
- When targeting a different disposable test environment, set `API_BASE_URL` and `DEMO_API_KEY` to matching values; that API must implement the same contract.

## Resume bullet point (use after publishing)

> Designed a Python pytest API automation framework using Requests and JSON Schema validation, covering authentication, CRUD flows, negative test cases, data isolation and GitHub Actions CI with JUnit reporting.
