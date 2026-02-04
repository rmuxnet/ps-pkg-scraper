import urllib.parse
from bs4 import BeautifulSoup
from src.func.get_proxy import get_proxy
from src.logger import log

def search_games(scraper, base_url, timeout, proxies, query):
    params = {"s": query}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    proxy = get_proxy(proxies)

    if proxy:
        log.debug(f"Search Proxy: {proxy.get('https')}")

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
            log.warning(f"Proxy {failed_proxy_url} failed during search.")
            
            if failed_proxy_url in proxies:
                proxies.remove(failed_proxy_url)
                log.info(f"Removed bad proxy. {len(proxies)} remaining.")
            
            log.warning("Retrying search with direct connection...")
            try:
                response = scraper.get(
                    url,
                    timeout=timeout,
                    impersonate="chrome",
                    proxies=None
                )
                response.raise_for_status()
            except Exception as final_e:
                log.error(f"Search failed (Direct): {final_e}")
                return []
        else:
            log.error(f"Search failed: {e}")
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
    
    log.info(f"Search for '{query}' returned {len(results)} results.")
    return results