# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Import your models and services
from models import IdeaInput, ValidationReport
from services.pipeline_service import run_validation_pipeline

# Initialize FastAPI app
app = FastAPI(
    title="TrendSpark Validation Engine",
    description="API for validating startup ideas using AI and real-time data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ─── Enable CORS (fixes OPTIONS 405 errors from browser preflight) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:*",       # allow any port on localhost
        "http://localhost:*",
        "*"                         # ← wildcard for development (restrict later)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# Mount the static folder → /static/index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend at root path (/)
@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = Path("static") / "index.html"
    
    if not index_path.is_file():
        return HTMLResponse(
            content="""
            <h1 style="color: #ff4444; text-align: center; margin-top: 120px; font-family: system-ui;">
                404 - Frontend File Not Found<br>
                <small style="color: #aaa; font-size: 1rem;">
                    Expected location: <code>Backend/static/index.html</code><br>
                    Please make sure the file exists in the 'static' folder.
                </small>
            </h1>
            """,
            status_code=404
        )
    
    return FileResponse(
        path=index_path,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Health check
@app.get("/api/v1/health", tags=["Status"])
async def get_health():
    """Health check endpoint to ensure the server is running."""
    return {"status": "ok"}


# Main validation endpoint
@app.post("/api/v1/validate", response_model=ValidationReport)
async def validate_idea(idea: IdeaInput):
    """
    Receives an IdeaInput object and returns a full ValidationReport.
    """
    report = run_validation_pipeline(idea)
    return report


# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,                # auto-reload on file changes (great for dev)
        reload_dirs=["."],          # watch current directory (Backend)
        # workers=1,                # uncomment only when you need multiple workers
    )