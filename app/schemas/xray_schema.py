from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class XRayCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_full_name: str = Field(..., min_length=3, max_length=100)
    patient_identifier: str = Field(..., min_length=1, max_length=50)
    clinical_history_code: str = Field(..., min_length=1, max_length=50)
    clinical_description: str = Field(..., min_length=3, max_length=2000)
    study_date: Optional[datetime] = None


class XRayUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_full_name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    patient_identifier: Optional[str] = Field(default=None, min_length=1, max_length=50)
    clinical_history_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    clinical_description: Optional[str] = Field(default=None, max_length=2000)
    study_date: Optional[datetime] = None


class XRayResponseSchema(BaseModel):
    id: int
    patient_full_name: str
    patient_identifier: str
    clinical_history_code: str
    clinical_description: str
    study_date: Optional[datetime] = None
    image_reference: Optional[str] = None
    image_url: Optional[str] = None


class PaginationSchema(BaseModel):
    page: int
    size: int
    skip: int
    limit: int
    sort_by: str
    sort_order: str


class RadiographListSchema(BaseModel):
    message: str
    pagination: PaginationSchema
    filters: dict[str, Optional[str]]
    data: List[XRayResponseSchema]
