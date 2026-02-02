from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.scraper import PSScraper
from src.database import GameCache
from src.metrics import metrics

app = FastAPI(title="PS PKG Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

scraper = PSScraper()
cache = GameCache()
cache.load()

@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    metrics.request_count += 1
    response = await call_next(request)
    return response

@app.get("/", response_class=PlainTextResponse)
def home():
    return "PS PKG Scraper API is Online. Use /search, /details, or /metrics."

@app.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"

@app.get("/metrics")
def get_metrics():
    """Returns internal metrics: requests, cache stats, and proxy failures."""
    return metrics.to_dict()

@app.get("/search")
@limiter.limit("10/minute")
def search_games(request: Request, q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    results = scraper.search_games(q)
    return {"count": len(results), "results": results}

@app.get("/details")
@limiter.limit("10/minute")
def get_game_details(request: Request, url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Query parameter 'url' is required")
    
    cached_data = cache.get(url)
    if cached_data:
        return {
            "metadata": cached_data.get("metadata", {}), 
            "links": cached_data.get("links", []),
            "source": "cache"
        }

    links, metadata = scraper.get_game_links(url, "N/A")
    if not links and metadata.get("size") == "N/A":
        raise HTTPException(status_code=404, detail="No content found or scraping failed")
    
    game_data = {
        "url": url,
        "title": "API Cached Entry", 
        "downloads": "N/A"
    }
    cache.save(game_data, links, metadata)

    return {"metadata": metadata, "links": links, "source": "live"}