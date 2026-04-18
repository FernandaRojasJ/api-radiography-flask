from app.models.xray_record import XRayRecord
from app.models.base import db

class XRayRepository:
    def __init__(self):
        self.session = db.session

    def save(self, record: XRayRecord):
        """Physically store or update a record."""
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_query(self):
        """Returns the base query for the CRUD operations to filter or paginate."""
        return self.session.query(XRayRecord)

    def get_by_id(self, record_id: int):
        return self.session.query(XRayRecord).filter(XRayRecord.id == record_id).first()

    def get_by_clinical_history_code(self, clinical_history_code: str):
        return (
            self.session.query(XRayRecord)
            .filter(XRayRecord.clinical_history_code == clinical_history_code)
            .first()
        )

    def get_all(self):
        return self.session.query(XRayRecord).all()

    def delete(self, record: XRayRecord):
        """Physically delete a record."""
        self.session.delete(record)
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def get_all_paginated(
        self,
        skip: int = 0,
        limit: int = 10,
        patient_name: str = None,
        clinical_history_code: str = None,
        study_date: str = None,
        sort_by: str = "study_date",
        sort_order: str = "desc",
    ):

        query = self.session.query(XRayRecord)

        if patient_name:
            query = query.filter(XRayRecord.patient_full_name.ilike(f"%{patient_name}%"))

        if clinical_history_code:
            query = query.filter(XRayRecord.clinical_history_code == clinical_history_code)

        if study_date:
            query = query.filter(db.func.date(XRayRecord.study_date) == study_date)

        sortable_fields = {
            "study_date": XRayRecord.study_date,
            "patient_full_name": XRayRecord.patient_full_name,
            "clinical_history_code": XRayRecord.clinical_history_code,
        }
        sort_column = sortable_fields.get(sort_by, XRayRecord.study_date)

        if (sort_order or "desc").lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query.offset(skip).limit(limit).all()