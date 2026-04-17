import os
import time
import uuid
from typing import Dict

import jwt
from flask import Request


class SecurityError(Exception):
	pass


def resolve_authenticated_user_identifier(request: Request) -> str:
	authorization_header = request.headers.get("Authorization", "")
	if authorization_header.startswith("Bearer "):
		incoming_token = authorization_header.removeprefix("Bearer ").strip()
		try:
			payload = jwt.decode(
				incoming_token,
				os.getenv("SECRET_KEY", "default_secret"),
				algorithms=["HS256"],
			)
		except jwt.PyJWTError as exc:
			raise SecurityError("Invalid authentication token.") from exc

		user_identifier = payload.get("sub") or payload.get("user_id")
		if not user_identifier:
			raise SecurityError("Authentication token does not identify a user.")
		if payload.get("purpose") == "xray_image_access":
			raise SecurityError("Image access tokens cannot be used for authentication.")
		return str(user_identifier)

	user_identifier = request.headers.get("X-User-Id") or request.headers.get("X-User-Email")
	if user_identifier:
		return str(user_identifier).strip()

	raise SecurityError("Missing authenticated user information.")


def create_image_access_token(
	secret_key: str,
	user_identifier: str,
	xray_id: int,
	expires_in_seconds: int,
) -> Dict[str, object]:
	issued_at = int(time.time())
	expires_at = issued_at + int(expires_in_seconds)
	payload = {
		"sub": str(user_identifier),
		"purpose": "xray_image_access",
		"xray_id": int(xray_id),
		"iat": issued_at,
		"exp": expires_at,
		"jti": uuid.uuid4().hex,
	}
	token = jwt.encode(payload, secret_key, algorithm="HS256")
	return {"token": token, "expires_at": expires_at}