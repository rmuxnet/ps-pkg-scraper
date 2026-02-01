import re
import urllib.parse
from curl_cffi import requests # Changed from cloudscraper
from bs4 import BeautifulSoup

try:
    from src.config import cfg
except Exception:
    cfg = None

DEFAULT_BASE_URL = "https://www.superpsx.com/"
DEFAULT_IGNORE_DOMAINS = [
    "superpsx", "facebook", "twitter", "discord",
    "instagram", "pinterest", "youtube", "telegram",
    "wp.com", "google.com"
]
DEFAULT_TIMEOUT = 30 # Increased timeout for cloud stability

class PSScraper:
    def __init__(self):
        # We now use a curl_cffi Session instead of cloudscraper
        self.scraper = requests.Session()
        
        scraper_cfg = getattr(cfg, "scraper", {}) if cfg else {}
        self.base_url = scraper_cfg.get("base_url", DEFAULT_BASE_URL)
        self.ignore_domains = scraper_cfg.get("ignore_domains", DEFAULT_IGNORE_DOMAINS)
        self.timeout = scraper_cfg.get("timeout", DEFAULT_TIMEOUT)

    def search_games(self, query):
        params = {"s": query}
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        try:
            # impersonate="chrome" is the magic key to bypass Cloudflare
            response = self.scraper.get(url, timeout=self.timeout, impersonate="chrome")
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            results = []
            items = soup.select("article.item")

            for item in items:
                title_node = item.select_one(".penci-entry-title a")
                if not title_node: continue

                img_node = item.select_one(".thumbnail")
                image = img_node.get("data-bgset") if img_node else None

                results.append({
                    "title": title_node.get_text(strip=True),
                    "url": title_node["href"],
                    "image": image,
                    "downloads": "N/A",
                    "size": "N/A",
                })

            return results
        except Exception as e:
            # Print the error so you can see it in Render logs if it fails again
            print(f"[ERROR] Search failed: {e}")
            return []

    def _extract_links(self, soup):
        links = []
        try:
            potential_links = soup.find_all("a", href=True)
            for link in potential_links:
                href = link["href"]
                if not any(domain in href.lower() for domain in self.ignore_domains):
                    if href.startswith("http") and len(href) > 15:
                        links.append(href)
        except Exception:
            pass
        return list(set(links))

    def _extract_grouped_links(self, soup):
        grouped_links = []
        tables = soup.find_all("table")
        found_structured_links = False
        seen_urls = set()

        for table in tables:
            block_name = "General / Misc"
            
            rows = table.find_all("tr")
            if not rows: continue

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    header_text = cols[0].get_text(strip=True).lower()
                    if "version" in header_text:
                        val = cols[1].get_text(strip=True, separator=" ")
                        clean_ver = re.sub(r'(?i)thanks?.*', '', val).strip()
                        clean_ver = re.sub(r'[\u200b-\u200d\uFEFF]', '', clean_ver)
                        if len(clean_ver) > 3:
                            block_name = clean_ver
                        break
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 1:
                    row_label = "Link"
                    content_col = None
                    
                    if len(cols) >= 2:
                        row_label = cols[0].get_text(strip=True).replace("⇛", "").strip()
                        content_col = cols[1]
                    else:
                        content_col = cols[0]
                    
                    if not content_col: continue

                    links = content_col.find_all("a", href=True)
                    for link in links:
                        href = link["href"]
                        if not any(domain in href.lower() for domain in self.ignore_domains):
                            if href.startswith("http") and len(href) > 15:
                                if href not in seen_urls:
                                    grouped_links.append({
                                        "group": block_name,
                                        "label": row_label if row_label else "Download",
                                        "url": href
                                    })
                                    seen_urls.add(href)
                                    found_structured_links = True
        
        if not found_structured_links:
            raw = self._extract_links(soup)
            return [{"group": "All Links", "label": "Link", "url": u} for u in raw]
        
        return grouped_links

    def _parse_metadata(self, soup, metadata):
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    key_raw = cols[0].get_text(strip=True, separator=" ").lower()
                    key = re.sub(r'[^\w\s]', '', key_raw).strip()
                    val = cols[1].get_text(strip=True, separator=" ")
                    
                    if "size" in key or "tamanho" in key:
                        metadata["size"] = val
                    elif "password" in key or "senha" in key:
                        metadata["password"] = val
                    elif "version" in key or "versão" in key:
                        if val.lower() != "n/a":
                            clean_ver = re.sub(r'(?i)thanks?.*', '', val).strip()
                            clean_ver = re.sub(r'[\u200b-\u200d\uFEFF]', '', clean_ver)
                            
                            curr_ver = metadata.get("version", "N/A")
                            if curr_ver == "N/A":
                                metadata["version"] = clean_ver
                            elif clean_ver not in curr_ver:
                                metadata["version"] = f"{curr_ver} | {clean_ver}"
                        
                        ids = re.findall(r'((?:CUSA|PPSA)\d{5})', val, re.IGNORECASE)
                        for mid in ids:
                            mid = mid.upper()
                            curr_cusa = metadata.get("cusa", "N/A")
                            if curr_cusa == "N/A":
                                metadata["cusa"] = mid
                            elif mid not in curr_cusa:
                                metadata["cusa"] = f"{curr_cusa}, {mid}"
                        
                        found_region = None
                        if "USA" in val: found_region = "USA"
                        elif "EUR" in val: found_region = "EUR"
                        elif "JPN" in val: found_region = "JPN"
                        elif "ASIA" in val: found_region = "ASIA"
                        
                        if found_region:
                            curr_reg = metadata.get("region", "N/A")
                            if curr_reg == "N/A":
                                metadata["region"] = found_region
                            elif found_region not in curr_reg:
                                metadata["region"] = f"{curr_reg}, {found_region}"

                    elif "voice" in key:
                        if metadata["voice"] == "N/A":
                            metadata["voice"] = val
                    elif "subtitles" in key or "screen languages" in key:
                        if metadata["subtitles"] == "N/A":
                            metadata["subtitles"] = val
                    elif "firmware" in key or "working" in key or "note" in key:
                        if "working" in val.lower() or re.search(r'\d+\.xx', val) or re.search(r'\d+\.\d+', val):
                            metadata["firmware"] = val
        return metadata

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

        try:
            # Added impersonate="chrome" here as well
            resp = self.scraper.get(game_url, timeout=self.timeout, impersonate="chrome")
            soup = BeautifulSoup(resp.content, "html.parser")
            
            self._parse_metadata(soup, metadata)

            dl_node = soup.find("a", href=re.compile(r"dll-")) or \
                      soup.select_one("a:has(img[alt*='Download'])")

            if dl_node:
                try:
                    dl_url = dl_node["href"]
                    # Added impersonate="chrome" here as well
                    dl_resp = self.scraper.get(dl_url, timeout=self.timeout, impersonate="chrome")
                    dl_soup = BeautifulSoup(dl_resp.content, "html.parser")
                    
                    self._parse_metadata(dl_soup, metadata)
                    final_links = self._extract_grouped_links(dl_soup)
                    
                    if final_links:
                        return final_links, metadata
                except Exception as e:
                    print(f"[WARNING] DL Page extract failed: {e}")
                    pass

            final_links = self._extract_grouped_links(soup)
            return final_links, metadata
        except Exception as e:
            print(f"[ERROR] Game link extract failed: {e}")
            return [], metadata