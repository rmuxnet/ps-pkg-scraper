import json
import os

DEFAULTS = {
    "scraper": {
        "base_url": "https://www.superpsx.com/",
        "timeout": 15,
        "ignore_domains": []
    },
    "database": {
        "cache_file": "games_cache.json",
        "cache_ttl": 31536000
    }
}

class Config:
    def __init__(self, config_path="settings.json"):
        self.settings = self._load_settings(config_path)

    def _load_settings(self, path):
        final_settings = DEFAULTS.copy()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                    final_settings["scraper"].update(file_settings.get("scraper", {}))
                    final_settings["database"].update(file_settings.get("database", {}))
            except Exception as e:
                print(f"[ERROR] Could not load {path}: {e}")
        env_base_url = os.getenv("SCRAPER_BASE_URL")
        if env_base_url:
            final_settings["scraper"]["base_url"] = env_base_url
        return final_settings

    @property
    def scraper(self):
        return self.settings.get("scraper", DEFAULTS["scraper"])

    @property
    def database(self):
        return self.settings.get("database", DEFAULTS["database"])

cfg = Config()
