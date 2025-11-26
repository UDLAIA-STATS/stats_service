# GitHub Copilot / AI Agent Instructions for statsservice

Purpose: Provide concise, actionable guidance so AI coding agents become productive quickly in this repo.

**Big Picture**
- **Backend:** Django project `stats_service` with a single app implemented in `stats/` that produces and stores player heatmaps.
- **Asynchronous work:** Celery is used for background processing (`celery.py`), tasks live under `stats/tasks/`.
- **Data flow (example):** incoming `tracks_json` → `stats.entities.utils.json_convert.PlayerJsonTransformer` → `stats.infraestructure.PlayerHeatmapDrawer` (via `HeatmapService`) → saves `Heatmap` model (`stats.entities.models.heatmap.Heatmap`).

**Key files & entry points**
- `celery.py` — defines the Celery `app`. Worker CLI: `celery -A stats_service worker -l info` (ensure broker URL set in env).
- `stats_service/settings.py` — environment-driven configuration via `python-decouple` (`.env` style variables). Required env vars include: `SECRET_KEY`, `DEBUG`, `POSTGRES_*` (DB), and likely `CELERY_BROKER_URL` (not present in settings file — check runtime env).
- `stats/tasks/generate_player_heatmaps_task.py` — Celery task that receives `tracks_json`, transforms it with `PlayerJsonTransformer`, and calls `HeatmapService`.
- `stats/infraestructure/heatmap_drawer.py` — plotting implementation using `mplsoccer`, `matplotlib`, `pandas`; returns PNG bytes.
- `stats/entities/utils/json_convert.py` — reconstructs domain `Track` objects from JSON; callers expect structure: frame_num → track_id → dict compatible with `TrackPlayerDetail`.
- `stats/entities/models/heatmap.py` — Django model storing binary heatmap images.

**Project-specific patterns & conventions**
- Domain layering: code is organized by domain/layer under `stats/` — `entities/`, `infraestructure/`, `tasks/` and `models/` reflect responsibilities.
- Diagram/Drawer abstraction: `Diagram` (abstract) → concrete drawers e.g., `PlayerHeatmapDrawer` that return `dict[int, bytes]` of PNGs.
- JSON payload shape: tasks accept `tracks_json` shaped as `frame_num -> track_id -> { ... }` and use `PlayerJsonTransformer.player_frames_from_json` to get typed `TrackDetail` objects.

**Notable inconsistencies / gotchas to verify before edits**
- `settings.py` lists `INSTALLED_APPS` entry `'stats_app'`, while the code lives in `stats/` (package name `stats`). Confirm whether settings should reference `stats` or the package must be renamed.
- `stats/tasks/generate_player_heatmaps_task.py` imports `shared_task` from `stats_service.celery` (`from stats_service.celery import shared_task`) — typical pattern is `from celery import shared_task`. Check `celery.py` to ensure `shared_task` is exported or update task imports accordingly.
- Celery broker/redis config is not in `settings.py`. Agents must not assume broker type; look for env vars or deployment docs.

**Developer workflows**
- Local development (typical):
  - Create `.env` with required variables used by `python-decouple`.
  - Install deps: `pip install -r requirements.txt`.
  - Migrate DB: `python manage.py migrate`.
  - Run server: `python manage.py runserver`.
  - Run celery worker (PowerShell example):
    ```pwsh
    celery -A stats_service worker --loglevel=info
    ```
  - Run tests: `python manage.py test`.

**Dependencies & runtime notes**
- Plotting and image generation rely on `matplotlib`, `mplsoccer`, `pandas`, `numpy`, and produce PNG bytes stored in a `BinaryField`.
- DB: PostgreSQL (`psycopg2` in `requirements.txt`). Ensure `POSTGRES_*` env vars are set.
- The code expects `python-decouple` for configuration management.

**How AI agents should approach changes**
- Start by opening the files named in **Key files & entry points** to validate intent before making changes.
- When modifying Celery tasks or worker config, ensure broker config is present in env or settings and that imports of `shared_task` are consistent with `celery.py` exports.
- For plotting changes, keep outputs as PNG bytes (function signatures return `dict[int, bytes]`) and preserve the DB save behavior (`Heatmap.objects.create(...)`).
- If you detect the `stats_app` vs `stats` mismatch, flag it as a repo owner question rather than auto-renaming apps.

If anything here is unclear or you'd like more detail (examples of JSON payloads, tests to add, or CI commands), tell me which section to expand.
