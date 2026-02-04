import re
import urllib.parse
import os
from curl_cffi import requests
from bs4 import BeautifulSoup

from src.logger import log

from src.func.extract_link import extract_links, extract_grouped_links
from src.func.get_proxy import get_proxy
from src.func.parse import parse_metadata
from src.func.search import search_games as func_search_games

try:
    from src.config import cfg
except Exception:
    cfg = None
    log.warning("Config not loaded, using defaults.")

DEFAULT_BASE_URL = "https://www.superpsx.com/"
DEFAULT_IGNORE_DOMAINS = [
    "superpsx", "facebook", "twitter", "discord",
    "instagram", "pinterest", "youtube", "telegram",
    "wp.com", "google.com"
]
DEFAULT_TIMEOUT = 30

class PSScraper:
    def __init__(self):
        self.scraper = requests.Session()
        scraper_cfg = getattr(cfg, "scraper", {}) if cfg else {}
        self.base_url = scraper_cfg.get("base_url", DEFAULT_BASE_URL)
        self.ignore_domains = scraper_cfg.get("ignore_domains", DEFAULT_IGNORE_DOMAINS)
        self.timeout = scraper_cfg.get("timeout", DEFAULT_TIMEOUT)

        self.proxies = []
        proxy_file = scraper_cfg.get("proxy_file", "proxy.txt")
        
        if proxy_file and os.path.exists(proxy_file):
            try:
                with open(proxy_file, "r", encoding="utf-8") as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                log.info(f"Loaded {len(self.proxies)} proxies from {proxy_file}")
            except Exception as e:
                log.error(f"Failed to load proxies from {proxy_file}: {e}")
        elif os.path.exists("proxy.txt"):
            try:
                with open("proxy.txt", "r", encoding="utf-8") as f:
                    self.proxies = [line.strip() for line in f if line.strip()]
                log.info(f"Loaded {len(self.proxies)} proxies from proxy.txt")
            except Exception as e:
                log.error(f"Failed to load proxies from proxy.txt: {e}")
        else:
            log.warning(f"No proxy file found (checked '{proxy_file}' and 'proxy.txt'). Using local IP.")

    def search_games(self, query):
        return func_search_games(self.scraper, self.base_url, self.timeout, self.proxies, query)

    def _extract_links(self, soup):
        return extract_links(soup, self.ignore_domains)

    def _extract_grouped_links(self, soup):
        return extract_grouped_links(soup, self.ignore_domains)

    def get_game_links(self, game_url, current_size="N/A"):
        metadata = {
            "size": current_size,
            "version": "N/A",
            "region": "N/A",
            "password": "N/A",
            "firmware": "N/A",
            "voice": "N/A",
            "subtitles": "N/A",
            "cusa": "N/A"
        }

        proxy = get_proxy(self.proxies)
        if proxy:
            log.debug(f"Using Proxy: {proxy.get('https')}")

        try:
            resp = self.scraper.get(game_url, timeout=self.timeout, impersonate="chrome", proxies=proxy)
            resp.raise_for_status()
        except Exception as e:
            if proxy:
                failed_proxy_url = proxy.get('https')
                if failed_proxy_url in self.proxies:
                    self.proxies.remove(failed_proxy_url)
                    log.warning(f"Proxy died ({failed_proxy_url}). Removed. {len(self.proxies)} left.")
                
                log.warning("Retrying direct connection...")
                try:
                    resp = self.scraper.get(game_url, timeout=self.timeout, impersonate="chrome", proxies=None)
                    resp.raise_for_status()
                except Exception as final_e:
                    log.error(f"Link extract failed (Direct): {final_e}")
                    return [], metadata
            else:
                log.error(f"Link extract failed: {e}")
                return [], metadata

        soup = BeautifulSoup(resp.content, "html.parser")
        parse_metadata(soup, metadata)

        dl_node = soup.find("a", href=re.compile(r"dll-")) or \
                  soup.select_one("a:has(img[alt*='Download'])")

        if dl_node:
            try:
                dl_url = dl_node["href"]
                dl_proxy = get_proxy(self.proxies)
                if dl_proxy:
                    log.debug(f"Using Proxy for DL Page: {dl_proxy.get('https')}")

                try:
                    dl_resp = self.scraper.get(
                        dl_url,
                        timeout=self.timeout,
                        impersonate="chrome",
                        proxies=dl_proxy
                    )
                    dl_resp.raise_for_status()
                except Exception:
                    if dl_proxy:
                        failed_dl_proxy = dl_proxy.get('https')
                        if failed_dl_proxy in self.proxies:
                            self.proxies.remove(failed_dl_proxy)
                            log.warning(f"DL Proxy died. Removed. {len(self.proxies)} left.")
                        
                        log.warning("DL proxy failed. Retrying direct...")
                        dl_resp = self.scraper.get(dl_url, timeout=self.timeout, impersonate="chrome", proxies=None)
                        dl_resp.raise_for_status()
                    else:
                        raise

                dl_soup = BeautifulSoup(dl_resp.content, "html.parser")
                parse_metadata(dl_soup, metadata)
                final_links = self._extract_grouped_links(dl_soup)

                if final_links:
                    return final_links, metadata
            except Exception as e:
                log.warning(f"DL Page extract failed: {e}")
                pass

        final_links = self._extract_grouped_links(soup)
        return final_links, metadata