from app.models.base import db
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class XRayRecord(db.Model):
    """
    Represents an X-ray record in the database.
    """
    __tablename__ = "xray_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    patient_full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    clinical_history_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    clinical_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    study_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)