import json
import os
import time
import redis

try:
    from src.config import cfg  # type: ignore
except Exception:
    cfg = None

DEFAULT_CACHE_FILE = "games_cache.json"
DEFAULT_CACHE_TTL = 31536000

if cfg and getattr(cfg, "database", None) is not None:
    try:
        CACHE_FILE = cfg.database.get("cache_file", DEFAULT_CACHE_FILE)
        CACHE_TTL = cfg.database.get("cache_ttl", DEFAULT_CACHE_TTL)
    except Exception:
        CACHE_FILE = DEFAULT_CACHE_FILE
        CACHE_TTL = DEFAULT_CACHE_TTL
else:
    CACHE_FILE = DEFAULT_CACHE_FILE
    CACHE_TTL = DEFAULT_CACHE_TTL

class GameCache:
    def __init__(self):
        self._cache = {}
        self.redis_client = None

        self.redis_url = os.getenv("REDIS_URL")

        if self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                print("[INFO] Connected to Redis Cloud Database")
            except Exception as e:
                print(f"[ERROR] Could not connect to Redis: {e}")
                self.redis_client = None

    def load(self):
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
                except (OSError, json.JSONDecodeError):
                    self._cache = {}
            else:
                self._cache = {}

    def get(self, url):
        if self.redis_client:
            try:
                data_str = self.redis_client.get(url)
                if not data_str:
                    return None
                data = json.loads(data_str)
                if "metadata" not in data or not data.get("links"):
                    return None
                return data
            except Exception:
                return None

        data = self._cache.get(url)
        if not data:
            return None

        if "metadata" not in data:
            return None

        if not data.get("links"):
            return None

        timestamp = data.get("timestamp", 0)
        if (time.time() - timestamp) > CACHE_TTL:
            return None

        return data

    def save(self, game_data, links, metadata):
        cache_entry = {
            "url": game_data["url"],
            "title": game_data["title"],
            "size": metadata.get("size", "N/A"),
            "downloads": game_data.get("downloads", "N/A"),
            "links": links,
            "metadata": metadata,
            "timestamp": time.time(),
        }

        if self.redis_client:
            try:
                self.redis_client.setex(
                    game_data["url"],
                    CACHE_TTL,
                    json.dumps(cache_entry)
                )
            except Exception as e:
                print(f"[ERROR] Failed to save to Redis: {e}")
            return

        self._cache[game_data["url"]] = cache_entry
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=4)
        except OSError:
            pass