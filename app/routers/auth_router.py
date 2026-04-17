import jwt
from flask import Blueprint, jsonify, request
from flasgger import swag_from

from app.core.config import Config
from app.repositories.xray_repository import XRayRepository


auth_bp = Blueprint("auth", __name__)
auth_user_repository = XRayRepository()


@auth_bp.route("/auth/token", methods=["POST"])
@swag_from(
	{
		"tags": ["Auth"],
		"summary": "Issue a JWT access token",
		"description": "Creates a JWT token for an existing user_id in the database.",
		"consumes": ["application/json"],
		"parameters": [
			{
				"name": "body",
				"in": "body",
				"required": True,
				"schema": {
					"type": "object",
					"properties": {
						"user_id": {"type": "integer"},
					},
					"required": ["user_id"],
				},
			}
		],
		"responses": {
			"200": {"description": "JWT issued successfully."},
			"400": {"description": "Missing or invalid user_id."},
			"404": {"description": "user_id not found in database."},
		},
	}
)
def auth_token():
	payload = request.get_json(silent=True) or {}
	user_identifier = payload.get("user_id")

	if user_identifier is None:
		return jsonify({"message": "user_id is required."}), 400

	try:
		user_id = int(user_identifier)
	except (TypeError, ValueError):
		return jsonify({"message": "user_id must be an integer."}), 400

	user_record = auth_user_repository.get_by_id(user_id)
	if user_record is None:
		return jsonify({"message": "User not found in database."}), 404

	token_payload = {
		"sub": str(user_id),
		"user_id": str(user_id),
	}
	token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm="HS256")
	return jsonify({"access_token": token, "token_type": "bearer"}), 200