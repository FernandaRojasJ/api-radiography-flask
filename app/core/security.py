import time
import uuid
from typing import Dict

import jwt

from app.core.config import Config


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
	token = jwt.encode(payload, secret_key, algorithm=Config.JWT_ALGORITHM)
	return {"token": token, "expires_at": expires_at}