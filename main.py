# main.py
import uvicorn
from fastapi import FastAPI
from models import IdeaInput, ValidationReport
from services.pipeline_service import run_validation_pipeline

# Initialize the FastAPI app
app = FastAPI(
    title="TrendSpark Validation Engine",
    description="API for validating startup ideas using AI and real-time data.",
    version="1.0.0"
)

# --- API Endpoints ---

@app.get("/api/v1/health", tags=["Status"])
async def get_health():
    """Health check endpoint to ensure the server is running."""
    return {"status": "ok"}


@app.post("/api/v1/validate", response_model=ValidationReport, tags=["Validation"])
async def validate_idea(idea: IdeaInput):
    """
    Main endpoint to validate a startup idea.
    Receives an IdeaInput object and returns a full ValidationReport.
    """
    # This single call runs the entire "engine"
    report = run_validation_pipeline(idea)
    return report

# --- Run the Server ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)