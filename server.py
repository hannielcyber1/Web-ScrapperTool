"""
FastAPI Web Server for Scrapling Web Scraping Studio
With Adaptive PDF/Excel Content Classification and Downloads.
"""

import os
from typing import Optional
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from core.scraper import ScraplingEngine
from exporters.smart_exporter import export_adaptive, get_file_slug

app = FastAPI(
    title="Scrapling Web Scraping Tool",
    description="Adaptive web scraper with automatic PDF and Excel generation",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "web", "templates", "index.html")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class ScrapeRequest(BaseModel):
    url: str
    mode: Optional[str] = "fast"
    custom_css: Optional[str] = None
    custom_xpath: Optional[str] = None
    impersonate: Optional[str] = "chrome"
    timeout: Optional[int] = 30
    solve_cloudflare: Optional[bool] = True
    export_format: Optional[str] = "auto"  # 'auto' | 'excel' | 'pdf' | 'both'


@app.get("/", response_class=HTMLResponse)
async def get_index():
    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=404, detail="Template file not found")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)


@app.post("/api/scrape")
async def api_scrape(req: ScrapeRequest):
    if not req.url or not req.url.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "URL cannot be empty"}
        )

    result = ScraplingEngine.scrape(
        url=req.url,
        mode=req.mode or "fast",
        custom_css=req.custom_css,
        custom_xpath=req.custom_xpath,
        timeout=req.timeout or 30,
        impersonate=req.impersonate or "chrome",
        solve_cloudflare=req.solve_cloudflare if req.solve_cloudflare is not None else True
    )

    if result.get("success"):
        # Auto-classify and generate the appropriate PDF or Excel file
        export_info = export_adaptive(
            result,
            output_dir=OUTPUT_DIR,
            preferred_format=req.export_format or "auto"
        )
        result["adaptive_export"] = export_info

    return JSONResponse(content=result)


@app.get("/api/download")
async def api_download(file: str = Query(..., description="File name in output directory")):
    safe_filename = os.path.basename(file)
    file_path = os.path.join(OUTPUT_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File {safe_filename} not found")

    media_type = "application/octet-stream"
    if safe_filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif safe_filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif safe_filename.endswith(".json"):
        media_type = "application/json"
    elif safe_filename.endswith(".md"):
        media_type = "text/markdown"
    elif safe_filename.endswith(".csv"):
        media_type = "text/csv"

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type
    )


class ExportRequest(BaseModel):
    scrape_data: dict
    format: str  # 'excel' | 'pdf' | 'both'


@app.post("/api/export")
async def api_export(req: ExportRequest):
    if not req.scrape_data:
        raise HTTPException(status_code=400, detail="Scrape data is required")

    export_info = export_adaptive(
        req.scrape_data,
        output_dir=OUTPUT_DIR,
        preferred_format=req.format
    )
    return JSONResponse(content=export_info)


def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    print(f"\n⚡ Starting Scrapling Web Studio on http://{host}:{port}")
    print(f"👉 Open http://{host}:{port} in your browser to start scraping!\n")
    uvicorn.run("server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Scrapling Web UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    args = parser.parse_args()

    start_server(host=args.host, port=args.port)
