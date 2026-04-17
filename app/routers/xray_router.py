import time

from flask import Blueprint, jsonify, request
from flask import send_file, url_for
from flasgger import swag_from
from pydantic import ValidationError
from app.core.config import Config
from app.core.security import (
	build_image_access_fingerprint,
	generate_image_access_token,
	verify_image_access_token,
)
from io import BytesIO

from app.services.cloudinary_service import CloudinaryUploadError
from app.services.xray_service import (
	DuplicateClinicalHistoryCodeError,
	InvalidFileError,
	XRayCreationError,
	XRayNotFoundError,
	XRayService,
)
xray_bp = Blueprint("xray", __name__)
xray_service = XRayService()


def serialize_xray_record(xray_record):
	return {
		"id": xray_record.id,
		"patient_full_name": xray_record.patient_full_name,
		"clinical_history_code": xray_record.clinical_history_code,
		"clinical_description": xray_record.clinical_description,
		"study_date": xray_record.study_date.isoformat() if xray_record.study_date else None,
		"has_image": bool(xray_record.image_url),
	}


@xray_bp.route("/xray", methods=["POST"])
@swag_from(
	{
		"tags": ["XRay"],
		"consumes": ["multipart/form-data"],
		"parameters": [
			{"name": "patient_full_name", "in": "formData", "required": True, "type": "string"},
			{"name": "clinical_history_code", "in": "formData", "required": True, "type": "string"},
			{"name": "clinical_description", "in": "formData", "required": False, "type": "string"},
			{
				"name": "study_date",
				"in": "formData",
				"required": False,
				"type": "string",
				"format": "date-time",
			},
			{"name": "image", "in": "formData", "required": True, "type": "file"},
		],
		"responses": {
			"201": {"description": "Record created"},
			"400": {"description": "Validation error"},
			"409": {"description": "Duplicate code"},
			"502": {"description": "Cloudinary error"},
		},
	}
)
def create_xray():
	xray_data = {
		"patient_full_name": request.form.get("patient_full_name"),
		"clinical_history_code": request.form.get("clinical_history_code"),
		"clinical_description": request.form.get("clinical_description"),
		"study_date": request.form.get("study_date"),
	}
	xray_image_file = request.files.get("image")

	try:
		xray = xray_service.create_xray(form_data=xray_data, image_file=xray_image_file)
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
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Created.", "data": serialize_xray_record(xray)}), 201


@xray_bp.route("/xray", methods=["GET"])
@swag_from(
	{
		"tags": ["XRay"],
		"parameters": [
			{"name": "skip", "in": "query", "required": False, "type": "integer", "default": 0},
			{"name": "limit", "in": "query", "required": False, "type": "integer", "default": 10},
			{"name": "patient_name", "in": "query", "required": False, "type": "string"},
		],
		"responses": {"200": {"description": "List records"}},
	}
)
def list_xray_records():
	skip = request.args.get("skip", default=0, type=int)
	limit = request.args.get("limit", default=10, type=int)
	patient_name = request.args.get("patient_name", default=None, type=str)

	xrays = xray_service.list_xrays(skip=skip, limit=limit, patient_name=patient_name)
	return jsonify({"data": [serialize_xray_record(record) for record in xrays]}), 200


@xray_bp.route("/xray/<int:xray_id>", methods=["GET"])
@swag_from(
	{
		"tags": ["XRay"],
		"parameters": [
			{
				"name": "xray_id",
				"in": "path",
				"required": True,
				"type": "integer",
				"description": "X-ray record identifier",
				"example": 1,
			}
		],
		"responses": {"200": {"description": "Get one"}, "404": {"description": "Not found"}},
	}
)
def get_xray_by_id(xray_id: int):
	try:
		xray = xray_service.get_xray_by_id(xray_id)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404

	return jsonify({"data": serialize_xray_record(xray)}), 200


@xray_bp.route("/xray/<int:xray_id>", methods=["PUT"])
@swag_from(
	{
		"tags": ["XRay"],
		"consumes": ["multipart/form-data"],
		"parameters": [
			{
				"name": "xray_id",
				"in": "path",
				"required": True,
				"type": "integer",
				"description": "X-ray record identifier",
				"example": 1,
			},
			{"name": "patient_full_name", "in": "formData", "required": False, "type": "string"},
			{"name": "clinical_history_code", "in": "formData", "required": False, "type": "string"},
			{"name": "clinical_description", "in": "formData", "required": False, "type": "string"},
			{
				"name": "study_date",
				"in": "formData",
				"required": False,
				"type": "string",
				"format": "date-time",
			},
			{"name": "image", "in": "formData", "required": False, "type": "file"},
		],
		"responses": {
			"200": {"description": "Updated"},
			"404": {"description": "Not found"},
			"409": {"description": "Duplicate code"},
		},
	}
)
def update_xray(xray_id: int):
	xray_data = {
		"patient_full_name": request.form.get("patient_full_name"),
		"clinical_history_code": request.form.get("clinical_history_code"),
		"clinical_description": request.form.get("clinical_description"),
		"study_date": request.form.get("study_date"),
	}
	xray_data = {key: value for key, value in xray_data.items() if value is not None}
	xray_image_file = request.files.get("image")

	try:
		xray = xray_service.update_xray(
			record_id=xray_id,
			form_data=xray_data,
			image_file=xray_image_file,
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
		return jsonify({"message": "Internal server error."}), 500

	return jsonify({"message": "Updated.", "data": serialize_xray_record(xray)}), 200


@xray_bp.route("/xray/<int:xray_id>", methods=["DELETE"])
@swag_from(
	{
		"tags": ["XRay"],
		"parameters": [
			{
				"name": "xray_id",
				"in": "path",
				"required": True,
				"type": "integer",
				"description": "X-ray record identifier",
				"example": 1,
			}
		],
		"responses": {"204": {"description": "Deleted"}, "404": {"description": "Not found"}},
	}
)
def delete_xray(xray_id: int):
	try:
		xray_service.delete_xray(xray_id)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	return "", 204


@xray_bp.route("/xray/<int:xray_id>/image", methods=["GET"])
@swag_from(
	{
		"tags": ["XRay"],
		"parameters": [
			{
				"name": "xray_id",
				"in": "path",
				"required": True,
				"type": "integer",
				"description": "X-ray record identifier",
				"example": 1,
			},
			{
				"name": "expires_in_seconds",
				"in": "query",
				"required": False,
				"type": "integer",
				"description": "Signed URL lifetime in seconds",
				"example": 600,
			}
		],
		"responses": {
			"200": {"description": "Returns temporary signed URL"},
			"404": {"description": "Record not found"},
			"400": {"description": "Record has no image"},
		},
	}
)
def get_xray_image_access_url(xray_id: int):
	expires_in = request.args.get("expires_in_seconds", default=None, type=int)
	try:
		image_access = xray_service.prepare_image_access(
			record_id=xray_id,
			expires_in_seconds=expires_in,
		)
		fingerprint = build_image_access_fingerprint(request)
		expires_at = int(time.time()) + image_access["expires_in_seconds"]
		access_token = generate_image_access_token(
			secret_key=Config.SECRET_KEY,
			xray_id=xray_id,
			expires_at=expires_at,
			fingerprint=fingerprint,
		)
		image_url = url_for(
			"xray.stream_xray_image",
			xray_id=xray_id,
			access_token=access_token,
			_external=True,
		)
		return jsonify(
			{
				"message": "Image access token generated.",
				"data": {
					"xray_id": xray_id,
					"access_token": access_token,
					"expires_at": expires_at,
					"expires_in_seconds": image_access["expires_in_seconds"],
					"image_url": image_url,
				},
			}
		), 200
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502
	except Exception:
		return jsonify({"message": "Internal server error."}), 500


@xray_bp.route("/xray/<int:xray_id>/image/content", methods=["GET"])
@swag_from(
	{
		"tags": ["XRay"],
		"parameters": [
			{
				"name": "xray_id",
				"in": "path",
				"required": True,
				"type": "integer",
				"description": "X-ray record identifier",
				"example": 1,
			},
			{
				"name": "access_token",
				"in": "query",
				"required": True,
				"type": "string",
				"description": "Signed token generated for this request",
			},
		],
		"responses": {
			"200": {"description": "Returns the image bytes"},
			"401": {"description": "Invalid or expired token"},
			"404": {"description": "Record not found"},
		},
	}
)
def stream_xray_image(xray_id: int):
	access_token = request.args.get("access_token", default="", type=str)
	fingerprint = build_image_access_fingerprint(request)
	try:
		payload = verify_image_access_token(
			secret_key=Config.SECRET_KEY,
			token=access_token,
			xray_id=xray_id,
			fingerprint=fingerprint,
		)
	except ValueError as exc:
		return jsonify({"message": str(exc)}), 401
	remaining_ttl = max(1, int(payload["expires_at"]) - int(time.time()))

	try:
		image_content = xray_service.get_image_content(
			record_id=xray_id,
			expires_in_seconds=remaining_ttl,
		)
	except XRayNotFoundError as exc:
		return jsonify({"message": str(exc)}), 404
	except InvalidFileError as exc:
		return jsonify({"message": str(exc)}), 400
	except CloudinaryUploadError as exc:
		return jsonify({"message": str(exc)}), 502

	response = send_file(
		BytesIO(image_content["content"]),
		mimetype=image_content["content_type"],
		as_attachment=False,
		download_name=f"xray-{xray_id}",
	)
	response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
	response.headers["Pragma"] = "no-cache"
	response.headers["Expires"] = "0"
	response.headers["X-Image-Expires-At"] = str(image_content["expires_at"])
	return response
