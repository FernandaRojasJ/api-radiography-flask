import jwt
import secrets
from datetime import datetime
from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session, url_for
from flasgger import swag_from

from app.core.config import Config
from app.repositories.xray_repository import XRayRepository


auth_bp = Blueprint("auth", __name__)
auth_user_repository = XRayRepository()

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


def _google_is_configured() -> bool:
	return bool(Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET)


def _missing_google_settings():
	missing = []
	if not Config.GOOGLE_CLIENT_ID:
		missing.append("GOOGLE_CLIENT_ID")
	if not Config.GOOGLE_CLIENT_SECRET:
		missing.append("GOOGLE_CLIENT_SECRET")
	return missing


def _resolve_google_redirect_uri() -> str:
	configured_uri = (Config.GOOGLE_REDIRECT_URI or "").strip()
	if configured_uri:
		return configured_uri
	return url_for("auth.google_callback", _external=True)


def _issue_local_jwt(subject: str, email: str = None, google_sub: str = None) -> str:
	now = int(datetime.utcnow().timestamp())
	token_payload = {
		"sub": str(subject),
		"provider": "google",
		"iat": now,
		"exp": now + Config.JWT_ACCESS_TOKEN_EXPIRES,
	}
	if email:
		token_payload["email"] = email
	if google_sub:
		token_payload["google_sub"] = google_sub
	return jwt.encode(token_payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


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

	now = int(datetime.utcnow().timestamp())
	token_payload = {
		"sub": str(user_id),
		"user_id": str(user_id),
		"iat": now,
		"exp": now + Config.JWT_ACCESS_TOKEN_EXPIRES,
	}
	token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
	return jsonify({"access_token": token, "token_type": "bearer"}), 200


@auth_bp.route("/auth/google/login", methods=["GET"])
@swag_from(
	{
		"tags": ["Auth"],
		"summary": "Start Google SSO flow",
		"description": "Builds the Google OAuth URL and redirects the user to consent screen.",
		"parameters": [
			{
				"name": "mode",
				"in": "query",
				"required": False,
				"type": "string",
				"description": "Use mode=json to return the authorization URL instead of redirecting.",
			},
		],
		"responses": {
			"302": {"description": "Redirected to Google OAuth consent screen."},
			"200": {"description": "Authorization URL returned as JSON."},
			"500": {"description": "Google OAuth is not configured."},
		},
	}
)
def google_login():
	if not _google_is_configured():
		return jsonify(
			{
				"message": "Google OAuth is not configured.",
				"missing_settings": _missing_google_settings(),
			}
		), 500

	redirect_uri = _resolve_google_redirect_uri()
	state = secrets.token_urlsafe(24)
	session["google_oauth_state"] = state

	oauth_params = {
		"client_id": Config.GOOGLE_CLIENT_ID,
		"redirect_uri": redirect_uri,
		"response_type": "code",
		"scope": Config.GOOGLE_OAUTH_SCOPES,
		"state": state,
		"access_type": "offline",
		"prompt": "consent",
	}
	authorization_url = f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{urlencode(oauth_params)}"

	if request.args.get("mode", "").lower() == "json":
		return jsonify({"authorization_url": authorization_url, "state": state}), 200

	return redirect(authorization_url)


@auth_bp.route("/auth/google/callback", methods=["GET"])
@swag_from(
	{
		"tags": ["Auth"],
		"summary": "Handle Google SSO callback",
		"description": "Exchanges Google authorization code for user info and issues local JWT.",
		"parameters": [
			{"name": "code", "in": "query", "required": False, "type": "string"},
			{"name": "state", "in": "query", "required": False, "type": "string"},
			{"name": "error", "in": "query", "required": False, "type": "string"},
		],
		"responses": {
			"200": {"description": "Local JWT issued successfully."},
			"400": {"description": "Invalid OAuth callback payload."},
			"500": {"description": "Google OAuth is not configured."},
			"502": {"description": "Google OAuth exchange failed."},
		},
	}
)
def google_callback():
	if not _google_is_configured():
		return jsonify(
			{
				"message": "Google OAuth is not configured.",
				"missing_settings": _missing_google_settings(),
			}
		), 500

	oauth_error = request.args.get("error")
	if oauth_error:
		error_description = request.args.get("error_description")
		return jsonify({"message": f"Google OAuth error: {oauth_error}", "detail": error_description}), 400

	expected_state = session.pop("google_oauth_state", None)
	incoming_state = request.args.get("state", "")
	if not expected_state or incoming_state != expected_state:
		return jsonify({"message": "Invalid OAuth state."}), 400

	authorization_code = request.args.get("code")
	if not authorization_code:
		return jsonify({"message": "Missing Google authorization code."}), 400

	redirect_uri = _resolve_google_redirect_uri()

	try:
		token_response = requests.post(
			GOOGLE_TOKEN_ENDPOINT,
			data={
				"code": authorization_code,
				"client_id": Config.GOOGLE_CLIENT_ID,
				"client_secret": Config.GOOGLE_CLIENT_SECRET,
				"redirect_uri": redirect_uri,
				"grant_type": "authorization_code",
			},
			timeout=Config.GOOGLE_OAUTH_TIMEOUT_SECONDS,
		)
	except requests.RequestException as exc:
		return jsonify({"message": "Google token exchange failed.", "detail": str(exc)}), 502

	if token_response.status_code >= 400:
		return jsonify(
			{
				"message": "Google token exchange failed.",
				"status_code": token_response.status_code,
				"detail": token_response.text,
			}
		), 502

	token_payload = token_response.json()
	google_access_token = token_payload.get("access_token")
	if not google_access_token:
		return jsonify({"message": "Google token response does not include access_token."}), 502

	try:
		userinfo_response = requests.get(
			GOOGLE_USERINFO_ENDPOINT,
			headers={"Authorization": f"Bearer {google_access_token}"},
			timeout=Config.GOOGLE_OAUTH_TIMEOUT_SECONDS,
		)
	except requests.RequestException as exc:
		return jsonify({"message": "Failed to fetch Google user profile.", "detail": str(exc)}), 502

	if userinfo_response.status_code >= 400:
		return jsonify(
			{
				"message": "Failed to fetch Google user profile.",
				"status_code": userinfo_response.status_code,
				"detail": userinfo_response.text,
			}
		), 502

	google_user = userinfo_response.json()
	google_sub = google_user.get("sub")
	email = google_user.get("email")
	if not google_sub and not email:
		return jsonify({"message": "Google profile does not include sub/email."}), 502

	local_subject = email or google_sub
	local_access_token = _issue_local_jwt(
		subject=local_subject,
		email=email,
		google_sub=google_sub,
	)

	return jsonify(
		{
			"access_token": local_access_token,
			"token_type": "bearer",
			"provider": "google",
			"user": {
				"sub": google_sub,
				"email": email,
				"name": google_user.get("name"),
				"picture": google_user.get("picture"),
			},
		}
	), 200