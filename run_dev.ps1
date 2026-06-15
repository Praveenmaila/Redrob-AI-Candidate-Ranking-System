# Run dev backend (uvicorn) and frontend (npm) — Windows PowerShell helper
# Starts the backend in a background process then runs the frontend dev server in the foreground.

param(
    [string]$Python = ".venv\Scripts\python.exe",
    [int]$BackendPort = 8000
)

Write-Host "Starting backend API using $Python"
Start-Process -NoNewWindow -FilePath $Python -ArgumentList "-m", "uvicorn", "backend_api:app", "--reload", "--host", "0.0.0.0", "--port", "$BackendPort"

Write-Host "Starting frontend dev server"
Push-Location frontend
if (Test-Path package-lock.json) {
    Write-Host "Detected package-lock.json"
}
npm run dev
Pop-Location
