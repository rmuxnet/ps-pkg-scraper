import random
from typing import Optional, Dict, List

def get_proxy(proxies: List[str]) -> Optional[Dict[str, str]]:
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}
