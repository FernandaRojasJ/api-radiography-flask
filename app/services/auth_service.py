from datetime import datetime
from functools import wraps
from typing import Any

from flask import g, jsonify, request
import jwt
from jwt import PyJWTError

from app.core.config import Config


class AuthServiceError(Exception):
    pass


class TokenValidationError(AuthServiceError):
    pass


class AuthService:
    """Service for JWT creation and validation."""

    def generate_token(self, user_id: int) -> str:
        issued_at = int(datetime.utcnow().timestamp())
        expires_at = issued_at + Config.JWT_ACCESS_TOKEN_EXPIRES
        payload = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "iat": issued_at,
            "exp": expires_at,
        }
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
        return token

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
                options={"require_exp": True, "verify_iat": False},
            )
        except PyJWTError as exc:
            raise TokenValidationError("Invalid or expired authentication token.") from exc
        return payload


auth_service = AuthService()


def token_required(function):
    """Decorator that enforces JWT authentication on a Flask route."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        authorization_header = request.headers.get("Authorization", "")
        if not authorization_header.startswith("Bearer "):
            return jsonify({"message": "Authentication required."}), 401

        token = authorization_header.removeprefix("Bearer ").strip()
        try:
            payload = auth_service.decode_token(token)
        except TokenValidationError as exc:
            return jsonify({"message": str(exc)}), 401

        if payload.get("purpose") == "xray_image_access":
            return jsonify({"message": "Image access tokens cannot be used for authentication."}), 401

        g.current_user = payload.get("sub") or payload.get("user_id")
        return function(*args, **kwargs)

    return wrapper
