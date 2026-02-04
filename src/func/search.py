import urllib.parse
from bs4 import BeautifulSoup

from src.func.get_proxy import get_proxy

def search_games(scraper, base_url, timeout, proxies, query):
    params = {"s": query}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    proxy = get_proxy(proxies)

    if proxy:
        print(f"[DEBUG] Using Proxy: {proxy.get('https')}")

    try:
        response = scraper.get(
            url,
            timeout=timeout,
            impersonate="chrome",
            proxies=proxy
        )
        response.raise_for_status()
    except Exception as e:
        if proxy:
            failed_proxy_url = proxy.get('https')
            print(f"[WARNING] Proxy {failed_proxy_url} failed.")
            if failed_proxy_url in proxies:
                proxies.remove(failed_proxy_url)
                print(f"[INFO] Removed bad proxy. {len(proxies)} remaining.")
            print(f"[WARNING] Retrying with direct connection...")
            try:
                response = scraper.get(
                    url,
                    timeout=timeout,
                    impersonate="chrome",
                    proxies=None
                )
                response.raise_for_status()
            except Exception as final_e:
                print(f"[ERROR] Search failed (Direct): {final_e}")
                return []
        else:
            print(f"[ERROR] Search failed: {e}")
            return []

    soup = BeautifulSoup(response.content, "html.parser")
    results = []
    items = soup.select("article.item")

    for item in items:
        title_node = item.select_one(".penci-entry-title a")
        if not title_node:
            continue

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
