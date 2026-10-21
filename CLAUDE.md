# SSWPA website

FastAPI app (`app/main.py`) with Jinja templates in `templates/`. Deployed to a GCP VM behind Caddy (see DEPLOYMENT.md).

## Running locally

The user runs the app themselves; do not start it unprompted. There are two ways, with different trade-offs:

| | `./run-local.sh` (Docker) | `python run_local.py` (host Python) |
|---|---|---|
| How | Builds image `sswpa-local` from the Dockerfile, copies `app/`, `static/`, `templates/` into it, starts container `sswpa-local` | Sets `ENVIRONMENT=local` and runs uvicorn directly on the machine |
| URL | http://localhost:8000 (HTTP only) | https://localhost:8000 when `localhost+2.pem` / `localhost+2-key.pem` exist in the repo root (they do), otherwise http |
| Code changes | No hot reload: re-run the script to rebuild | Hot reload on `app/`, `templates/`, `static/`: just refresh |
| Environment | Clean container (Python 3.11), independent of the local venv | Needs the local `venv` with `requirements.txt` installed (the venv here is Python 3.13 and was missing `markdown` as of Oct 2026) |
| Payments | Square needs HTTPS, so payment flow can't be tested | HTTPS, so payments can be tested |
| Stop | `./stop-local.sh` | Ctrl+C |

- Both read `.env` (Square sandbox keys, `GMAIL_APP_PASSWORD`, `ENVIRONMENT`). `run-local.sh` also passes `ADMIN_PASSWORD`, which is not in `.env`, so `/admin/wm` login is empty in that mode.
- Local database: `./local-data/sswpa.db` (Docker mode).
- Status: `./run-local.sh` was run successfully in Oct 2026. `python run_local.py` has not been verified recently.
- LOCAL_DEVELOPMENT.md and DEPLOYMENT.md (`docker-compose up` / `python main.py`) are older and partly inaccurate (e.g. LOCAL_DEVELOPMENT.md says http but `run_local.py` uses https when certs exist).

## Yearly content updates

Each event type has its own skill in `.claude/skills/`. The site has four event types; update only the one being asked about:

- Artist Recital (ticketed): managed in the admin page (`/admin/wm`), no skill needed. `gen-program-md` builds `ticket_tool/program.md` from a program screenshot.
- Honor Recital: `update-honor-recital`
- Audition (`young-artists-audition.html` plus the downloadable application form in `static/documents/`): `update-audition`
- Heinz Hall (`young-artists-heinz-hall.html`): `update-heinz-hall`
