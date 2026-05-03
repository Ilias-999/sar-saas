from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.parser import parse_sar_text
from app.stats import calculate_stats
from app.database import init_db, get_db
from app.models import Operation


app = FastAPI(title="SAR Analyzer Backend", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP only. Later, restrict to your frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def log_operation(
    db: Session,
    operation_type: str,
    filename: str,
    message: str,
    status: str
):
    """Log an operation to the database"""
    try:
        operation = Operation(
            operation_type=operation_type,
            filename=filename,
            message=message,
            status=status,
        )
        db.add(operation)
        db.commit()
        db.refresh(operation)
        print(f"[LOG] {operation_type}: {filename} - {status}")
        return operation
    except Exception as e:
        print(f"[ERROR] Failed to log operation: {str(e)}")
        db.rollback()
        return None

@app.get("/")
def health_check():
    return {
        "message": "SAR Analyzer Backend is running",
        "status": "ok",
    }


@app.get("/api/health/db")
def db_health_check(db: Session = Depends(get_db)):
    """Check database connectivity and table status"""
    try:
        # Try to query the operations table
        count = db.query(Operation).count()
        return {
            "status": "ok",
            "database": "connected",
            "operations_table": "exists",
            "total_logs": count,
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }


@app.get("/api/operations")
def get_operations(db: Session = Depends(get_db)):
    """
    Get all logged operations, ordered by date descending (newest first)
    """
    try:
        operations = db.query(Operation).order_by(Operation.date.desc()).all()
        return {
            "status": "success",
            "count": len(operations),
            "operations": [op.to_dict() for op in operations]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "operations": []
        }

@app.post("/api/analyze")
async def analyze_sar_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a SAR text file, parse it, calculate stats, and return JSON.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        raw_content = await file.read()
        text_content = raw_content.decode("utf-8", errors="ignore")
        log_operation(
            db,
            operation_type="FILE_UPLOAD",
            filename=file.filename,
            message=f"File uploaded successfully ({len(raw_content)} bytes)",
            status="success"
        )
    except Exception as exc:
        error_msg = f"Could not read uploaded file: {str(exc)}"
        log_operation(
            db,
            operation_type="FILE_UPLOAD",
            filename=file.filename,
            message=error_msg,
            status="failed"
        )
        raise HTTPException(status_code=400, detail=error_msg)

    if not text_content.strip():
        error_msg = "Uploaded file is empty"
        log_operation(
            db,
            operation_type="FILE_VALIDATION",
            filename=file.filename,
            message=error_msg,
            status="failed"
        )
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        log_operation(
            db,
            operation_type="PARSING",
            filename=file.filename,
            message="Started parsing SAR file",
            status="in_progress"
        )
        metrics = parse_sar_text(text_content)
        log_operation(
            db,
            operation_type="PARSING",
            filename=file.filename,
            message=f"Parsing completed - {len(metrics)} metrics parsed",
            status="success"
        )

        log_operation(
            db,
            operation_type="STATS_CALCULATION",
            filename=file.filename,
            message="Started calculating statistics",
            status="in_progress"
        )
        stats = calculate_stats(metrics)
        log_operation(
            db,
            operation_type="STATS_CALCULATION",
            filename=file.filename,
            message=f"Statistics calculated - {len(stats)} stats generated",
            status="success"
        )

        log_operation(
            db,
            operation_type="ANALYSIS",
            filename=file.filename,
            message=f"Analysis completed successfully",
            status="success"
        )

    except Exception as exc:
        error_msg = f"Could not analyze SAR file: {str(exc)}"
        log_operation(
            db,
            operation_type="ANALYSIS",
            filename=file.filename,
            message=error_msg,
            status="failed"
        )
        raise HTTPException(status_code=500, detail=error_msg)

    return {
        "filename": file.filename,
        "metrics_count": len(metrics),
        "stats_count": len(stats),
        "stats": stats,
    }
