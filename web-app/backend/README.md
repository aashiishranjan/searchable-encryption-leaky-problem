# Backend – Searchable Encryption Leaky Problem

A Flask REST API that integrates with the existing `src/` cryptographic
modules to expose the SSE leakage-analysis demo as an HTTP service.

## Quick start

```bash
cd web-app/backend
pip install -r requirements.txt
python app.py          # → http://127.0.0.1:5000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/documents` | List documents in the current session |
| `POST` | `/api/upload` | Upload custom documents (JSON body) |
| `POST` | `/api/upload/samples` | Load the built-in 10-document corpus |
| `POST` | `/api/search` | Search by keyword (mode: before \| after) |
| `POST` | `/api/compare` | Compare before/after for the same keyword |
| `GET` | `/api/analysis` | Full leakage analysis for the session |
| `GET` | `/api/history` | Query history with statistics |
| `POST` | `/api/reset` | Wipe session and start fresh |

## Upload custom documents

```http
POST /api/upload
Content-Type: application/json

{
  "documents": [
    {"id": "my_doc_1", "content": "Your document text here."},
    {"id": "my_doc_2", "content": "Another document."}
  ]
}
```

## Search

```http
POST /api/search
Content-Type: application/json

{"keyword": "encryption", "mode": "before"}
```

`mode` can be `"before"` (full leakage) or `"after"` (with result-padding
mitigation).  The response includes a complete 6-step breakdown.

## Session management

Session state (encryption key, index, query log) is stored server-side and
identified by a UUID in a signed cookie (`sid`).  Call `POST /api/reset` to
start a fresh session.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (dev key) | Flask secret key for signing cookies |
| `CORS_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5000` | Bind port |
| `DEBUG` | `True` | Flask debug mode |
