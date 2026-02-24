# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

IntelliDoc Nexus is a multi-agent RAG-powered document intelligence platform with a Python/FastAPI backend and React/Vite/TypeScript frontend. Documents are uploaded, chunked, embedded, and indexed for AI-powered Q&A with citations.

### Services

| Service | Port | Notes |
|---------|------|-------|
| Backend (FastAPI) | 8000 | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Frontend (Vite) | 3000 | `cd frontend && npx vite --host 0.0.0.0 --port 3000` |
| PostgreSQL 16 | 5432 | Via Docker Compose: `sudo docker compose -f infrastructure/docker-compose.yml up -d db` |
| Redis 7 | 6379 | Via Docker Compose: `sudo docker compose -f infrastructure/docker-compose.yml up -d redis` |

### Running Docker in this environment

Docker runs inside a Firecracker VM. Required workarounds are already applied:
- Storage driver: `fuse-overlayfs` (configured in `/etc/docker/daemon.json`)
- iptables: set to `iptables-legacy`
- Start daemon: `sudo dockerd &>/tmp/dockerd.log &`

### Backend setup caveats

- The backend `.env` file must point to `localhost` (not `db`/`redis`) when running outside Docker Compose. Copy `.env.example` and replace `db:5432` with `localhost:5432` and `redis:6379` with `localhost:6379`.
- Set `PINECONE_API_KEY=` and `ANTHROPIC_API_KEY=` (empty) in `.env` to enable graceful fallback. A non-empty invalid key causes a Pinecone 401 error during document upload. An empty key triggers a `RuntimeError` that the ingestion service catches and skips.
- The dev user is auto-seeded on startup when `APP_ENV=development`: email `dev@intellidoc.local`, password `devpassword123`.
- `~/.local/bin` must be on `PATH` for `uvicorn` and other pip-installed scripts.

### Testing

- Backend tests use SQLite (via `aiosqlite`) and require no running database: `cd backend && python3 -m pytest tests/ -v`
- Frontend has no ESLint config file (`.eslintrc*`) so `npm run lint` fails. Use `npx tsc -b --noEmit` for type checking.
- Frontend build: `cd frontend && npm run build`

### Frontend dev server

The Vite config proxies `/api` requests to `http://localhost:8000`, so the backend must be running for API calls to work. The frontend auto-detects dev user login from the backend's auth flow.
