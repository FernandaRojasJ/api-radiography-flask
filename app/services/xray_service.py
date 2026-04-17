from datetime import datetime
from typing import Optional
import re
from uuid import uuid4

from pydantic import ValidationError
from werkzeug.datastructures import FileStorage

from app.core.config import Config
from app.models.xray_record import XRayRecord
from app.repositories.xray_repository import XRayRepository
from app.schemas.xray_schema import XRayCreateSchema, XRayUpdateSchema
from app.services.cloudinary_service import CloudinaryService, CloudinaryUploadError
class XRayNotFoundError(Exception):
	pass

class InvalidFileError(Exception):
	pass
class DuplicateClinicalHistoryCodeError(Exception):
	pass
class XRayCreationError(Exception):
	pass
class XRayService:
	ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
	ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}

	def __init__(self):
		self.repository = XRayRepository()
		self.cloudinary_service = CloudinaryService(
			cloud_name=Config.CLOUDINARY_CLOUD_NAME,
			api_key=Config.CLOUDINARY_API_KEY,
			api_secret=Config.CLOUDINARY_API_SECRET,
			folder=Config.CLOUDINARY_FOLDER,
			upload_type=Config.CLOUDINARY_UPLOAD_TYPE,
		)
		self.max_file_size_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
		self.default_signed_ttl = Config.CLOUDINARY_SIGNED_URL_TTL_SECONDS
		self.min_signed_ttl = Config.CLOUDINARY_MIN_SIGNED_URL_TTL_SECONDS
		self.max_signed_ttl = Config.CLOUDINARY_MAX_SIGNED_URL_TTL_SECONDS

	def create_xray(self, form_data: dict, image_file: FileStorage):
		try:
			payload = XRayCreateSchema.model_validate(form_data)
			self._assert_unique_clinical_code(payload.clinical_history_code)
			self._validate_file(image_file)

			public_id = self._build_public_id(payload.clinical_history_code)
			stored_public_id = self.cloudinary_service.upload_authenticated_image(
				image_file.stream,
				public_id=public_id,
			)

			record = XRayRecord(
				patient_full_name=payload.patient_full_name,
				clinical_history_code=payload.clinical_history_code,
				clinical_description=payload.clinical_description,
				study_date=payload.study_date or datetime.utcnow(),
				image_url=stored_public_id,
			)

			saved_record = self.repository.save(record)
			if saved_record is None:
				raise XRayCreationError("Repository returned None while saving X-ray record.")

			return saved_record
		except (ValidationError, InvalidFileError, DuplicateClinicalHistoryCodeError):
			raise
		except CloudinaryUploadError:
			raise
		except Exception as exc:
			self.repository.rollback()
			raise XRayCreationError(f"Failed to create X-ray record. Detail: {exc}") from exc

	def list_xrays(self, skip: int = 0, limit: int = 10, patient_name: str = None):
		return self.repository.get_all_paginated(skip=skip, limit=limit, patient_name=patient_name)

	def get_xray_by_id(self, record_id: int):
		record = self.repository.get_by_id(record_id)
		if record is None:
			raise XRayNotFoundError("X-ray record not found.")
		return record

	def update_xray(
		self,
		record_id: int,
		form_data: dict,
		image_file: Optional[FileStorage] = None,
	):
		record = self.get_xray_by_id(record_id)
		payload = XRayUpdateSchema.model_validate(form_data)
		update_data = payload.model_dump(exclude_unset=True)

		new_code = update_data.get("clinical_history_code")
		if new_code and new_code != record.clinical_history_code:
			self._assert_unique_clinical_code(new_code)

		for field_name, value in update_data.items():
			setattr(record, field_name, value)

		if image_file and image_file.filename:
			self._validate_file(image_file)
			effective_code = record.clinical_history_code
			public_id = self._build_public_id(effective_code)
			stored_public_id = self.cloudinary_service.upload_authenticated_image(
				image_file.stream,
				public_id=public_id,
			)
			record.image_url = stored_public_id

		return self.repository.save(record)

	def delete_xray(self, record_id: int):
		record = self.get_xray_by_id(record_id)
		self.repository.delete(record)

	def generate_signed_image_url(
		self,
		record_id: int,
		expires_in_seconds: Optional[int] = None,
	):
		record = self.get_xray_by_id(record_id)
		if not record.image_url:
			raise InvalidFileError("This record has no associated image.")

		ttl = expires_in_seconds if expires_in_seconds is not None else self.default_signed_ttl
		ttl = self._sanitize_ttl(ttl)

		signed = self.cloudinary_service.generate_signed_image_url(
			public_id=record.image_url,
			expires_in_seconds=ttl,
		)
		return {
			"xray_id": record.id,
			**signed,
		}

	def prepare_image_access(self, record_id: int, expires_in_seconds: Optional[int] = None):
		record = self.get_xray_by_id(record_id)
		if not record.image_url:
			raise InvalidFileError("This record has no associated image.")

		ttl = expires_in_seconds if expires_in_seconds is not None else self.default_signed_ttl
		ttl = self._sanitize_ttl(ttl)

		return {
			"xray_id": record.id,
			"public_id": record.image_url,
			"expires_in_seconds": ttl,
		}

	def get_image_content(self, record_id: int, expires_in_seconds: int):
		image_access = self.prepare_image_access(record_id, expires_in_seconds)
		return self.cloudinary_service.download_authenticated_image(
			public_id=image_access["public_id"],
			expires_in_seconds=image_access["expires_in_seconds"],
		)

	def _assert_unique_clinical_code(self, clinical_history_code: str):
		existing = self.repository.get_by_clinical_history_code(clinical_history_code)
		if existing:
			raise DuplicateClinicalHistoryCodeError(
				"A record with this clinical_history_code already exists."
			)

	def _build_public_id(self, clinical_history_code: str):
		clean_code = re.sub(r"[^a-zA-Z0-9_-]", "_", clinical_history_code.strip())
		date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
		random_suffix = uuid4().hex[:12]
		return f"medical/{date_prefix}/{clean_code}_{random_suffix}"

	def _sanitize_ttl(self, ttl: int):
		if ttl < self.min_signed_ttl:
			return self.min_signed_ttl
		if ttl > self.max_signed_ttl:
			return self.max_signed_ttl
		return ttl

	def _validate_file(self, image_file: FileStorage):
		if image_file is None:
			raise InvalidFileError("Image file is required.")
		if not image_file.filename:
			raise InvalidFileError("Image filename is required.")

		lower_name = image_file.filename.lower()
		extension = lower_name.rsplit(".", 1)[-1] if "." in lower_name else ""
		if extension not in self.ALLOWED_EXTENSIONS:
			raise InvalidFileError("Invalid file extension. Allowed: jpg, jpeg, png.")
		if image_file.mimetype not in self.ALLOWED_MIME_TYPES:
			raise InvalidFileError("Invalid MIME type. Allowed: image/jpeg, image/png.")

		image_file.stream.seek(0, 2)
		file_size = image_file.stream.tell()
		image_file.stream.seek(0)
		if file_size > self.max_file_size_bytes:
			raise InvalidFileError(
				f"File exceeds max allowed size of {Config.MAX_FILE_SIZE_MB} MB."
			)
