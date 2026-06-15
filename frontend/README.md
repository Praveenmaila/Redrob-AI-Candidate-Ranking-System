# Redrob AI Candidate Ranking — Frontend

This Next.js 15 + TypeScript frontend connects to the existing Python backend exposing `/rank`, `/download`, and `/health` endpoints.

Prerequisites

- Node.js 20+
- pnpm or npm
- Backend running and reachable at `http://localhost:8000` (or set `NEXT_PUBLIC_API_URL`)

Install

```bash
cd frontend
npm install
# or pnpm install
```

Run locally

```bash
# development
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

# build
npm run build
npm start
```

What it does

- Dashboard: upload JD and candidate dataset, run ranking
- Progress panel: polls `/health` for progress messages
- Results: fetches `/download` (CSV) and displays Top 100 with search/sort/pagination
- Candidate modal: inspect individual explanations

Notes

- The frontend expects the backend to accept `multipart/form-data` POST to `/rank` with fields `jd` and `candidates`.
- Download endpoint `/download` should return `submission_top100.csv` as text/csv.

Tailwind and shadcn/ui

- The project is styled with Tailwind; you can integrate `shadcn` components by following their installation instructions and mapping components into `src/components`.
