from bs4 import BeautifulSoup
import re

def extract_links(soup, ignore_domains):
    links = []
    try:
        potential_links = soup.find_all("a", href=True)
        for link in potential_links:
            href = link["href"]
            if not any(domain in href.lower() for domain in ignore_domains):
                if href.startswith("http") and len(href) > 15:
                    links.append(href)
    except Exception:
        pass
    return list(set(links))


def extract_grouped_links(soup, ignore_domains):
    grouped_links = []
    tables = soup.find_all("table")
    found_structured_links = False
    seen_urls = set()

    for table in tables:
        block_name = "General / Misc"
        rows = table.find_all("tr")
        if not rows:
            continue

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

                if not content_col:
                    continue

                links = content_col.find_all("a", href=True)
                for link in links:
                    href = link["href"]
                    if not any(domain in href.lower() for domain in ignore_domains):
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
        raw = extract_links(soup, ignore_domains)
        return [{"group": "All Links", "label": "Link", "url": u} for u in raw]

    return grouped_links
