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
		"description": "Returns a paginated list with optional filters and sorting.",
		"parameters": [
			{"name": "page", "in": "query", "required": False, "type": "integer", "default": 1},
			{"name": "size", "in": "query", "required": False, "type": "integer", "default": 10},
			{
				"name": "sort",
				"in": "query",
				"required": False,
				"type": "string",
				"default": "study_date:desc",
				"description": "Format field:order. Example: patient_full_name:asc",
			},
			{
				"name": "patient_name",
				"in": "query",
				"required": False,
				"type": "string",
				"description": "Partial match over patient_full_name",
			},
			{
				"name": "clinical_history_code",
				"in": "query",
				"required": False,
				"type": "string",
				"description": "Exact match by clinical history code",
			},
			{
				"name": "study_date",
				"in": "query",
				"required": False,
				"type": "string",
				"description": "Date filter in format YYYY-MM-DD",
			},
			{"name": "skip", "in": "query", "required": False, "type": "integer", "default": 0},
			{"name": "limit", "in": "query", "required": False, "type": "integer", "default": 10},
			{"name": "sort_by", "in": "query", "required": False, "type": "string"},
			{"name": "sort_order", "in": "query", "required": False, "type": "string"},
		],
		"responses": {
			"200": {"description": "Radiographs list returned successfully."},
			"500": {"description": "Internal server error."},
		},
	}
)
def list_radiographs():
	allowed_sort_fields = {"study_date", "patient_full_name", "clinical_history_code"}
	allowed_sort_orders = {"asc", "desc"}

	sort_expression = (request.args.get("sort", default="study_date:desc", type=str) or "").strip()
	sort_by = "study_date"
	sort_order = "desc"
	if sort_expression:
		if ":" in sort_expression:
			raw_field, raw_order = sort_expression.split(":", 1)
		else:
			raw_field, raw_order = sort_expression, "desc"
		candidate_field = raw_field.strip()
		candidate_order = raw_order.strip().lower()
		if candidate_field in allowed_sort_fields:
			sort_by = candidate_field
		if candidate_order in allowed_sort_orders:
			sort_order = candidate_order

	explicit_sort_by = request.args.get("sort_by", default=None, type=str)
	explicit_sort_order = request.args.get("sort_order", default=None, type=str)
	if explicit_sort_by in allowed_sort_fields:
		sort_by = explicit_sort_by
	if explicit_sort_order and explicit_sort_order.lower() in allowed_sort_orders:
		sort_order = explicit_sort_order.lower()

	raw_skip = request.args.get("skip", default=None, type=int)
	raw_limit = request.args.get("limit", default=None, type=int)

	if raw_skip is not None or raw_limit is not None:
		skip = max(raw_skip or 0, 0)
		size = raw_limit or 10
		if size < 1:
			size = 1
		if size > 100:
			size = 100
		limit = size
		page = (skip // size) + 1
	else:
		page = request.args.get("page", default=1, type=int)
		size = request.args.get("size", default=10, type=int)
		if page < 1:
			page = 1
		if size < 1:
			size = 1
		if size > 100:
			size = 100
		skip = (page - 1) * size
		limit = size

	patient_name = request.args.get("patient_name", default=None, type=str)
	clinical_history_code = request.args.get("clinical_history_code", default=None, type=str)
	study_date = request.args.get("study_date", default=None, type=str)

	try:
		radiographs = radiographs_service.list_radiographs(
			skip=skip,
			limit=limit,
			patient_name=patient_name,
			clinical_history_code=clinical_history_code,
			study_date=study_date,
			sort_by=sort_by,
			sort_order=sort_order,
		)
	except Exception:
		radiographs_logger.exception("Unexpected error while listing radiographs")
		return jsonify({"message": "Internal server error."}), 500

	filters = {
		"patient_name": patient_name,
		"clinical_history_code": clinical_history_code,
		"study_date": study_date,
	}
	return jsonify(
		{
			"message": "Radiographs retrieved.",
			"pagination": {
				"page": page,
				"size": size,
				"skip": skip,
				"limit": limit,
				"sort_by": sort_by,
				"sort_order": sort_order,
			},
			"filters": filters,
			"data": [serialize_radiograph_record(record) for record in (radiographs or [])],
		}
	), 200


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
