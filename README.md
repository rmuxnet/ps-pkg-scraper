# PS PKG Scraper

A small tool to search and retrieve PS4/PS5 game download links. Provides both an interactive CLI and a simple HTTP API.

## Install

1.  **Install Python 3.8+**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## CLI Usage

Interactive mode:
```bash
python app.py
```

Direct search:
```bash
python app.py -s "Game Name"
```

Workflow:
- Search for a game.
- Select a result to view metadata and download links.
- Results may be cached locally (JSON) or in Redis (if REDIS_URL set).

## HTTP API

Start server:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Endpoints:
- GET / — health/info text
- GET /health — returns "OK"
- GET /search?q=QUERY — search games (rate-limited)
- GET /details?url=GAME_URL — fetch download links and metadata (rate-limited)

Example:
```bash
curl "http://localhost:8000/search?q=persona"
curl "http://localhost:8000/details?url=https://example.com/game-page"
```

## Configuration

- settings.json — local config (scraper.base_url, timeout, ignore_domains, database.cache_file, database.cache_ttl).
- Environment variables:
  - SCRAPER_BASE_URL — override base URL
  - REDIS_URL — if set, app will attempt to use Redis for caching

Defaults:
- cache file: `games_cache.json`
- cache TTL: 31536000 seconds

## Proxy and Cache

- `proxy.txt` — optional list of proxies (one per line). If present, scraper will pick proxies randomly.
- Cache: local JSON file or Redis (if REDIS_URL provided). To refresh results, delete the cache file or evict keys in Redis.

## Deployment

render.yaml is included for Render.com. The service uses:
- buildCommand: `pip install -r requirements.txt`
- startCommand: `uvicorn api:app --host 0.0.0.0 --port $PORT`

Ensure env vars (e.g., REDIS_URL) are configured in your deployment environment.

## Notes

- Use responsibly and respect site terms of service.
- The scraper uses simple HTML parsing; site changes may require updates.

TODO:
- Add proxy health checks and a background validator (periodically test/mark bad proxies).
- Expose proxy status/metrics via API (e.g., /proxy/health).
- Add more robust health checks (API readiness, Redis connectivity, cache integrity).
- Add metrics (request counts, cache hits/misses, proxy failures) and basic monitoring endpoints.

Contributing
- PRs welcome. Please include tests for new behavior and update README/TODO as features evolve.
