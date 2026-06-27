# Redrob AI Candidate Ranking — Frontend

This Next.js 15 + TypeScript frontend connects directly to the Python backend exposing `/datasets`, `/datasets/upload`, `/rank`, `/results`, `/download`, and `/health` endpoints.

Prerequisites

- Node.js 20+
- pnpm or npm
- Backend running and reachable at `http://localhost:8000` (or set `NEXT_PUBLIC_BACKEND_TARGET`)

Install

```bash
cd frontend
npm install
# or pnpm install
```

Run locally

```bash
# development
NEXT_PUBLIC_BACKEND_TARGET=http://localhost:8000 npm run dev

# build
npm run build
npm start
```

What it does

- Dashboard: upload the candidate dataset once, select a saved dataset, upload JD, run ranking
- Progress panel: polls `/health` for progress messages
- Results: fetches `/results` and `/download` from FastAPI and displays Top 100 with search/sort/pagination
- Candidate modal: inspect individual explanations

Notes

- Candidate datasets are uploaded to `POST /datasets/upload` and stored by the backend under `data/uploads/`.
- Ranking uses `multipart/form-data` POST to `/rank` with fields `jd` and `dataset`; the large candidate file is not uploaded during ranking.
- Download endpoint `/download` should return `submission_top100.csv` as text/csv.

Tailwind and shadcn/ui

- The project is styled with Tailwind; you can integrate `shadcn` components by following their installation instructions and mapping components into `src/components`.
