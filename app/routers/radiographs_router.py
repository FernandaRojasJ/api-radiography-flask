import logging

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from pydantic import ValidationError

from app.core.security import SecurityError, resolve_authenticated_user_identifier
from app.services.cloudinary_service import CloudinaryUploadError
from app.services.xray_service import (
	DuplicateClinicalHistoryCodeError,
	InvalidFileError,
	XRayCreationError,
	XRayNotFoundError,
	XRayService,
)


radiographs_logger = logging.getLogger(__name__)
radiographs_bp = Blueprint("radiographs", __name__)
radiographs_service = XRayService()


def _require_authenticated_user():
	try:
		return resolve_authenticated_user_identifier(request)
	except SecurityError as exc:
		radiographs_logger.warning("Authentication failed for radiographs endpoint: %s", exc)
		return None


def serialize_radiograph_record(radiograph_record, resolved_image_url: str = None):
	return {
		"id": radiograph_record.id,
		"patient_full_name": radiograph_record.patient_full_name,
		"patient_identifier": radiograph_record.patient_identifier,
		"clinical_history_code": radiograph_record.clinical_history_code,
		"clinical_description": radiograph_record.clinical_description,
		"study_date": radiograph_record.study_date.isoformat() if radiograph_record.study_date else None,
		"image_reference": radiograph_record.image_url,
		"image_url": resolved_image_url,
	}


@radiographs_bp.route("/radiographs", methods=["POST"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "Create a radiograph record",
		"description": "Creates a radiograph with patient data and a Cloudinary-backed image upload.",
		"consumes": ["multipart/form-data"],
		"parameters": [
			{"name": "patient_full_name", "in": "formData", "required": True, "type": "string"},
			{"name": "patient_identifier", "in": "formData", "required": True, "type": "string"},
			{"name": "clinical_history_code", "in": "formData", "required": True, "type": "string"},
			{"name": "clinical_description", "in": "formData", "required": True, "type": "string"},
			{"name": "study_date", "in": "formData", "required": False, "type": "string", "format": "date-time"},
			{"name": "image_file", "in": "formData", "required": True, "type": "file"},
		],
		"responses": {
			"201": {"description": "Radiograph created successfully."},
			"400": {"description": "Invalid payload or invalid image."},
			"401": {"description": "Authentication required."},
			"409": {"description": "Duplicate clinical history code."},
			"502": {"description": "Cloudinary upload error."},
		},
	}
)
def create_radiograph():
	if _require_authenticated_user() is None:
		return jsonify({"message": "Authentication required."}), 401

	radiograph_data = {
		"patient_full_name": request.form.get("patient_full_name"),
		"patient_identifier": request.form.get("patient_identifier"),
		"clinical_history_code": request.form.get("clinical_history_code"),
		"clinical_description": request.form.get("clinical_description"),
		"study_date": request.form.get("study_date"),
	}
	if "image_file" in request.files:
		radiograph_image_file = request.files["image_file"]
	else:
		radiograph_image_file = request.files.get("image")

	try:
		radiograph = radiographs_service.create_xray(
			form_data=radiograph_data,
			image_file=radiograph_image_file,
		)
	except ValidationError as exc:
		return jsonify({"message": "Invalid payload.", "errors": exc.errors()}), 400
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except DuplicateClinicalHistoryCodeError as exc:
		return jsonify({"message": str(exc)}), 409
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502
	except XRayCreationError as exc:
		return jsonify({"message": str(exc)}), 500
	except Exception:
		radiographs_logger.exception("Unexpected error while creating radiograph")
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Created.", "data": serialize_radiograph_record(radiograph)}), 201


@radiographs_bp.route("/radiographs", methods=["GET"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "List radiographs",
		"description": "Returns a paginated list of radiographs.",
		"parameters": [
			{"name": "skip", "in": "query", "required": False, "type": "integer", "default": 0},
			{"name": "limit", "in": "query", "required": False, "type": "integer", "default": 10},
		],
		"responses": {
			"200": {"description": "Radiographs list returned successfully."},
			"500": {"description": "Internal server error."},
		},
	}
)
def list_radiographs():
	skip = request.args.get("skip", default=0, type=int)
	limit = request.args.get("limit", default=10, type=int)

	try:
		radiographs = radiographs_service.list_radiographs(skip=skip, limit=limit)
	except Exception:
		radiographs_logger.exception("Unexpected error while listing radiographs")
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Radiographs retrieved.", "data": [serialize_radiograph_record(record) for record in (radiographs or [])]}), 200


@radiographs_bp.route("/radiographs/<int:radiograph_id>", methods=["GET"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "Get a radiograph by id",
		"description": "Returns one radiograph and resolves its dynamic image URL.",
		"parameters": [
			{"name": "radiograph_id", "in": "path", "required": True, "type": "integer"},
		],
		"responses": {
			"200": {"description": "Radiograph retrieved successfully."},
			"401": {"description": "Authentication required."},
			"404": {"description": "Radiograph not found."},
			"502": {"description": "Cloudinary error."},
		},
	}
)
def get_radiograph_by_id(radiograph_id: int):
	user_identifier = _require_authenticated_user()
	if user_identifier is None:
		return jsonify({"message": "Authentication required."}), 401

	expires_in = request.args.get("expires_in_seconds", default=None, type=int)
	try:
		radiograph = radiographs_service.get_xray_by_id(radiograph_id)
		dynamic_image_url = radiographs_service.resolve_dynamic_image_url(
			record=radiograph,
			user_identifier=user_identifier,
			expires_in_seconds=expires_in,
		)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502
	except Exception:
		radiographs_logger.exception("Unexpected error while retrieving radiograph id=%s", radiograph_id)
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Radiograph retrieved.", "data": serialize_radiograph_record(radiograph, resolved_image_url=dynamic_image_url)}), 200


@radiographs_bp.route("/radiographs/<int:radiograph_id>", methods=["PUT"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "Update a radiograph",
		"description": "Updates patient fields and optionally replaces the image via multipart/form-data.",
		"consumes": ["multipart/form-data"],
		"parameters": [
			{"name": "radiograph_id", "in": "path", "required": True, "type": "integer"},
			{"name": "patient_full_name", "in": "formData", "required": False, "type": "string"},
			{"name": "patient_identifier", "in": "formData", "required": False, "type": "string"},
			{"name": "clinical_history_code", "in": "formData", "required": False, "type": "string"},
			{"name": "clinical_description", "in": "formData", "required": False, "type": "string"},
			{"name": "study_date", "in": "formData", "required": False, "type": "string", "format": "date-time"},
			{"name": "image_file", "in": "formData", "required": False, "type": "file"},
		],
		"responses": {
			"200": {"description": "Radiograph updated successfully."},
			"400": {"description": "Invalid payload or invalid image."},
			"401": {"description": "Authentication required."},
			"404": {"description": "Radiograph not found."},
			"409": {"description": "Duplicate clinical history code."},
			"502": {"description": "Cloudinary upload error."},
		},
	}
)
def update_radiograph(radiograph_id: int):
	if radiograph_id <= 0:
		return jsonify({"message": "radiograph_id must be greater than 0."}), 400

	if _require_authenticated_user() is None:
		return jsonify({"message": "Authentication required."}), 401

	radiograph_data = {
		"patient_full_name": request.form.get("patient_full_name"),
		"patient_identifier": request.form.get("patient_identifier"),
		"clinical_history_code": request.form.get("clinical_history_code"),
		"clinical_description": request.form.get("clinical_description"),
		"study_date": request.form.get("study_date"),
	}
	radiograph_data = {key: value for key, value in radiograph_data.items() if value not in (None, "")}
	if "image_file" in request.files:
		radiograph_image_file = request.files["image_file"]
	else:
		radiograph_image_file = request.files.get("image")
	if radiograph_image_file and not radiograph_image_file.filename:
		radiograph_image_file = None

	try:
		radiograph = radiographs_service.update_xray(
			record_id=radiograph_id,
			form_data=radiograph_data,
			image_file=radiograph_image_file,
		)
	except ValidationError as exc:
		return jsonify({"message": "Invalid payload.", "errors": exc.errors()}), 400
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except DuplicateClinicalHistoryCodeError as exc:
		return jsonify({"message": str(exc)}), 409
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502
	except Exception:
		radiographs_logger.exception("Unexpected error while updating radiograph id=%s", radiograph_id)
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Updated.", "data": serialize_radiograph_record(radiograph)}), 200


@radiographs_bp.route("/radiographs/<int:radiograph_id>", methods=["DELETE"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "Delete a radiograph",
		"description": "Deletes a radiograph record permanently.",
		"parameters": [
			{"name": "radiograph_id", "in": "path", "required": True, "type": "integer"},
		],
		"responses": {
			"204": {"description": "Radiograph deleted successfully."},
			"401": {"description": "Authentication required."},
			"404": {"description": "Radiograph not found."},
		},
	}
)
def delete_radiograph(radiograph_id: int):
	if _require_authenticated_user() is None:
		return jsonify({"message": "Authentication required."}), 401

	try:
		radiographs_service.delete_xray(radiograph_id)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except Exception:
		radiographs_logger.exception("Unexpected error while deleting radiograph id=%s", radiograph_id)
		return jsonify({"message": "Internal server error."}), 500

	return "", 204


@radiographs_bp.route("/radiographs/<int:radiograph_id>/image", methods=["GET"])
@swag_from(
	{
		"tags": ["Radiographs"],
		"summary": "Stream a secure radiograph image",
		"description": "Returns a temporary secure image URL for the radiograph.",
		"parameters": [
			{"name": "radiograph_id", "in": "path", "required": True, "type": "integer"},
			{"name": "expires_in_seconds", "in": "query", "required": False, "type": "integer", "default": 600},
		],
		"responses": {
			"200": {"description": "Secure image URL generated successfully."},
			"401": {"description": "Authentication required."},
			"404": {"description": "Radiograph not found."},
			"400": {"description": "Radiograph has no associated image."},
			"502": {"description": "Cloudinary error."},
		},
	}
)
def get_radiograph_image(radiograph_id: int):
	user_identifier = _require_authenticated_user()
	if user_identifier is None:
		return jsonify({"message": "Authentication required."}), 401

	expires_in = request.args.get("expires_in_seconds", default=None, type=int)
	try:
		radiograph = radiographs_service.get_xray_by_id(radiograph_id)
		image_url = radiographs_service.resolve_dynamic_image_url(
			record=radiograph,
			user_identifier=user_identifier,
			expires_in_seconds=expires_in,
		)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502
	except Exception:
		radiographs_logger.exception("Unexpected error while building radiograph image URL id=%s", radiograph_id)
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Radiograph image URL retrieved.", "data": {"image_url": image_url}}), 200
