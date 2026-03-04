# Kerala Courts Case Search API

FastAPI wrapper for querying case information from the Kerala High Court case information system.

The service exposes a clean REST API for:
- searching cases by type/number/year,
- fetching case details and proceedings,
- resolving file-view tokens,
- downloading case/interim PDFs,
- retrieving judgement PDF URLs.

## Features

- Search a case and retrieve `cino` + `case_no`
- Fetch detailed case HTML and `vieworder` parameters
- Fetch proceedings HTML for a case
- Download case PDF by `cino`
- Resolve file view data and extract PDF URL (when available)
- Download interim order PDF by URL
- Retrieve judgement PDF URL from token
- List all known Kerala case type IDs and display names

## Tech Stack

- Python `>=3.14`
- FastAPI
- Pydantic
- Requests

## Project Structure

```text
app/
  api/v1/endpoints/
    cases.py
    case_details.py
    case_proceedings.py
    case_files.py
    case_type.py
  models/
    schemas.py
    case_type_mapping.py
  services/
    kerala_courts_service.py
  main.py
run.py
pyproject.toml
```

## Getting Started

### 1) Prerequisites

- Python `3.14`
- `uv` (recommended)

### 2) Install dependencies

Using `uv`:

```bash
uv sync
```

### 3) Run the API

Option A (recommended):

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Option B (entrypoint script):

```bash
uv run python run.py
```

## Base URLs

- API root: `http://127.0.0.1:8000`
- Versioned API prefix: `/api/v1`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

## API Endpoints

### 1) Get case types

`GET /api/v1/case-types/`

Returns all case type IDs with display names.

Example:

```bash
curl http://127.0.0.1:8000/api/v1/case-types/
```

---

### 2) Search case

`POST /api/v1/cases/search`

Request body:

```json
{
  "case_type_id": "157",
  "case_no": "1234",
  "case_year": "2024"
}
```

Response:

```json
{
  "cino": "KLHC010012342024",
  "case_no": "WP(C)/1234/2024",
  "success": true
}
```

---

### 3) Get case details

`POST /api/v1/case-details/`

Request body:

```json
{
  "cino": "KLHC010012342024",
  "case_no": "WP(C)/1234/2024"
}
```

Response includes:
- `details_html`
- `vieworder_token` (optional)
- `vieworder_lookups` (optional)

---

### 4) Get case proceedings

`POST /api/v1/case-proceedings/`

Request body:

```json
{
  "cino": "KLHC010012342024"
}
```

Response includes `proceedings_html`.

---

### 5) Download case PDF

`POST /api/v1/case-files/pdf`

Request body:

```json
{
  "cino": "KLHC010012342024"
}
```

Returns `application/pdf` as an attachment.

---

### 6) Get case file view

`POST /api/v1/case-files/view`

Request body:

```json
{
  "token": "your_vieworder_token",
  "lookups": "your_vieworder_lookups"
}
```

Response includes:
- `fileview_html`
- `pdf_url` (optional, extracted from HTML object tag)

---

### 7) Download interim PDF

`GET /api/v1/case-files/interim-pdf?pdf_url=<url-encoded-pdf-url>`

Returns `application/pdf` as an attachment.

Example:

```bash
curl -G "http://127.0.0.1:8000/api/v1/case-files/interim-pdf" \
  --data-urlencode "pdf_url=https://hckinfo.keralacourts.in/path/to/file.pdf" \
  --output interim.pdf
```

---

### 8) Get judgement PDF URL

`POST /api/v1/case-files/judgement-pdf`

Request body:

```json
{
  "token": "your_vieworder_token"
}
```

Response:

```json
{
  "pdf_url": "https://hckinfo.keralacourts.in/path/to/judgement.pdf"
}
```

## Typical Workflow

1. Call `GET /api/v1/case-types/` to find a valid `case_type_id`.
2. Call `POST /api/v1/cases/search` to get `cino` and normalized `case_no`.
3. Call `POST /api/v1/case-details/` to get case HTML and vieworder params.
4. (Optional) Call `POST /api/v1/case-proceedings/` for proceedings HTML.
5. For PDFs:
   - use `POST /api/v1/case-files/pdf` for the main case PDF by `cino`,
   - use `POST /api/v1/case-files/view` + `GET /api/v1/case-files/interim-pdf` for interim documents,
   - use `POST /api/v1/case-files/judgement-pdf` for judgement PDF URL.

## Error Handling

- `400 Bad Request`: validation/upstream parsing/request failures
- `500 Internal Server Error`: unexpected internal failures

FastAPI `detail` fields include the underlying error message when available.

## Notes

- This API depends on upstream Kerala Courts endpoints; availability or HTML changes upstream may affect behavior.
- Several responses intentionally return raw HTML (`details_html`, `proceedings_html`, `fileview_html`) so clients can parse domain-specific details.
- `pdf_url` fields can be `null` when no PDF object is found in upstream HTML.
