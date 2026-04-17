from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class XRayCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_full_name: str = Field(..., min_length=3, max_length=100)
    clinical_history_code: str = Field(..., min_length=1, max_length=50)
    clinical_description: Optional[str] = Field(default=None, max_length=2000)
    study_date: Optional[datetime] = None


class XRayUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_full_name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    clinical_history_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    clinical_description: Optional[str] = Field(default=None, max_length=2000)
    study_date: Optional[datetime] = None
