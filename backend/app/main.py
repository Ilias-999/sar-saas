from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.parser import parse_sar_text
from app.stats import calculate_stats


app = FastAPI(title="SAR Analyzer Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP only. Later, restrict to your frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {
        "message": "SAR Analyzer Backend is running",
        "status": "ok",
    }

@app.post("/api/analyze")
async def analyze_sar_file(file: UploadFile = File(...)):
    """
    Upload a SAR text file, parse it, calculate stats, and return JSON.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        raw_content = await file.read()
        text_content = raw_content.decode("utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded file: {str(exc)}",
        )

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        metrics = parse_sar_text(text_content)
        stats = calculate_stats(metrics)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze SAR file: {str(exc)}",
        )

    return {
        "filename": file.filename,
        "metrics_count": len(metrics),
        "stats_count": len(stats),
        "stats": stats,
    }
