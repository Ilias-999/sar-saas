from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    operation_type = Column(String(50), nullable=False)  # e.g., "FILE_UPLOAD", "ANALYSIS", "PARSING"
    filename = Column(String(255), nullable=False)
    message = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)  # e.g., "success", "failed", "in_progress"

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "operation_type": self.operation_type,
            "filename": self.filename,
            "message": self.message,
            "status": self.status,
        }
