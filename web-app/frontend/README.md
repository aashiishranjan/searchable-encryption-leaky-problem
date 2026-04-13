# Frontend – Searchable Encryption Leaky Problem

A React single-page application that provides a professional dashboard for
the SSE leakage-analysis demo.

## Quick start

```bash
cd web-app/frontend
npm install
npm start          # → http://localhost:3000
```

> **Note:** The Flask backend must be running on `http://localhost:5000`
> before starting the frontend (the CRA `proxy` in `package.json` forwards
> all `/api` requests to port 5000 automatically).

## Features

| Tab | Description |
|-----|-------------|
| 📁 Documents | Load 10 built-in cybersecurity documents or upload your own |
| 🔍 Search | Keyword search with BEFORE / AFTER mode toggle |
| ⚖️ Compare | Side-by-side before/after comparison for the same keyword |
| 📊 Charts | Recharts visualisation of all four leakage types |
| 🕓 History | Full query history with statistics |

## BEFORE / AFTER modes

| Mode | What the server sees |
|------|---------------------|
| 🔴 BEFORE | Exact result count (volume leakage visible) |
| 🟢 AFTER | Padded to 5 results (volume leakage hidden) |

## Dependencies

- **React 18** – UI framework
- **Axios** – HTTP client
- **Recharts** – chart library

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_BASE` | (CRA proxy) | Override backend URL |
