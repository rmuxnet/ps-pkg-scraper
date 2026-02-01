from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.scraper import PSScraper

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

@app.get("/", response_class=PlainTextResponse)
def home():
    return "PS PKG Scraper API is Online. Use /search or /details."

@app.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"

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
    links, metadata = scraper.get_game_links(url, "N/A")
    if not links and metadata.get("size") == "N/A":
        raise HTTPException(status_code=404, detail="No content found or scraping failed")
    return {"metadata": metadata, "links": links}