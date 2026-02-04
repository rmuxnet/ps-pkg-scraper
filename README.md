# PS PKG Scraper

Small tool to search and retrieve PS4/PS5 game download links. Offers an interactive CLI and an HTTP API with an optional WebUI.

Supported features
- CLI interactive TUI (app.py)
- FastAPI HTTP API (src.api) with optional WebUI (templates + static)
- Local JSON cache or Redis-backed cache
- Optional proxy list support (one proxy per line)

Quick install
- Python 3.10 recommended.
- Install deps:
```bash
pip install -r requirements.txt
```

Run (API / Web)
- Development:
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
- Production (example):
```bash
uvicorn src.api:app --host 0.0.0.0 --port $PORT
```
- When `webui` is enabled in config/settings.json, the root path (/) serves the WebUI from `templates/index.html` and static assets from `static/`.

Run (CLI)
```bash
python app.py
# or search directly
python app.py -s "Game Name"
```

API endpoints
- GET / — root (WebUI when enabled; otherwise plain text info)
- GET /health — simple health check, returns "OK"
- GET /search?q=QUERY — search games (rate-limited)
- GET /details?url=GAME_URL — fetch download links and metadata (rate-limited)

Notes
- The API is rate-limited (slowapi).
- Static web assets: `static/` and templates: `templates/`.
- Templates used by WebUI: `static/res/*.html` (card_result, card_details, link_item).

Configuration
- Primary config: `config/settings.json` (optional). Default settings are in `src/config.py`.
- Environment variables:
  - SCRAPER_BASE_URL — override base scraping URL
  - REDIS_URL — Redis connection string; if set, cache will use Redis
  - PORT — port for uvicorn if used by a platform
- Default scraper settings:
  - base_url: https://www.superpsx.com/
  - timeout: configurable via settings.json
  - proxy_file: default `config/proxy.txt` (the scraper will also check `proxy.txt`)

Caching
- Default cache file: `games_cache.json` (path can be overridden in config/settings.json)
- Cache TTL default: 31536000 seconds (~1 year)
- If REDIS_URL is provided, Redis will be used instead of the local JSON file.

Proxies
- Provide proxies one per line in the configured proxy file (default `config/proxy.txt` or `proxy.txt`).
- Proxies are selected randomly; failing proxies are removed from the list during runtime.

Docker
- Dockerfile present: builds image and runs `uvicorn src.api:app`.
- Exposes port 8000.

Deployment (example)
- Render/Platform: render.yaml included; start command uses `uvicorn src.api:app --host 0.0.0.0 --port $PORT`.

Project layout (important files)
- src/api.py — FastAPI application and WebUI mount
- src/scraper.py — main scraping logic
- src/func/ — helper parsing, search, proxy and link extraction functions
- src/database.py — simple JSON / Redis cache logic
- app.py — interactive CLI
- templates/index.html — WebUI front page
- static/ — WebUI assets (JS, CSS, templates)
- config/settings.json — example configuration

Usage tips
- For local dev, use `--reload` with uvicorn.
- To force fresh scraping, delete the cache file or evict Redis keys.
- Respect target site terms of service.

License
- MIT
