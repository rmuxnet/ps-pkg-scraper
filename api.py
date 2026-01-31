from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from src.scraper import PSScraper

app = FastAPI(title="PS PKG Scraper API")
scraper = PSScraper()

@app.get("/", response_class=PlainTextResponse)
def home():
    return "PS PKG Scraper API is Online. Use /search or /details."

@app.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"

@app.get("/search")
def search_games(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    results = scraper.search_games(q)
    return {"count": len(results), "results": results}

@app.get("/details")
def get_game_details(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Query parameter 'url' is required")
    links, metadata = scraper.get_game_links(url, "N/A")
    if not links and metadata.get("size") == "N/A":
        raise HTTPException(status_code=404, detail="No content found or scraping failed")
    return {"metadata": metadata, "links": links}