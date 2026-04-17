import time
import logging
import re
from urllib.parse import quote

import cloudinary
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.uploader import destroy, rename, upload
from cloudinary.utils import cloudinary_url, private_download_url


logger = logging.getLogger(__name__)


class CloudinaryUploadError(Exception):
	pass


class CloudinaryService:
	def __init__(
		self,
		cloud_name: str,
		api_key: str,
		api_secret: str,
		folder: str,
		upload_type: str,
	):
		self.cloud_name = cloud_name
		self.api_key = api_key
		self.api_secret = api_secret
		self.folder = folder
		if upload_type not in {"upload", "authenticated"}:
			raise CloudinaryUploadError(
				"Invalid CLOUDINARY_UPLOAD_TYPE. Allowed: 'upload' or 'authenticated'."
			)
		self.upload_type = upload_type
		self._configure()

	def _configure(self):
		if not all([self.cloud_name, self.api_key, self.api_secret]):
			return
		cloudinary.config(
			cloud_name=self.cloud_name,
			api_key=self.api_key,
			api_secret=self.api_secret,
			secure=True,
		)

	def upload_authenticated_image(self, file_stream, public_id: str):
		if not all([self.cloud_name, self.api_key, self.api_secret]):
			raise CloudinaryUploadError("Cloudinary credentials are not configured.")

		# Exam flow: image is uploaded public during daytime, then scheduler hardens it at 23:59.
		initial_type = "upload"
		try:
			upload_options = {
				"folder": self.folder,
				"public_id": public_id,
				"resource_type": "image",
				"type": initial_type,
				"overwrite": True,
			}
			result = upload(
				file_stream,
				**upload_options,
			)
		except CloudinaryError as exc:
			raise CloudinaryUploadError(
				f"Failed to upload image to Cloudinary. Detail: {exc}"
			) from exc
		except Exception as exc:
			raise CloudinaryUploadError(
				f"Unexpected Cloudinary upload error: {exc}"
			) from exc

		stored_public_id = result.get("public_id")
		if not stored_public_id:
			raise CloudinaryUploadError("Cloudinary response does not include public_id.")
		return stored_public_id

	def generate_signed_image_url(self, public_id: str, expires_in_seconds: int):
		if not all([self.cloud_name, self.api_key, self.api_secret]):
			raise CloudinaryUploadError("Cloudinary credentials are not configured.")
		if expires_in_seconds <= 0:
			raise CloudinaryUploadError("Signed URL ttl must be greater than 0.")

		expires_at = int(time.time()) + expires_in_seconds

		try:
			resource_info = cloudinary.api.resource(
				public_id,
				resource_type="image",
				type="authenticated",
			)
		except CloudinaryError as exc:
			raise CloudinaryUploadError(
				f"Failed to fetch Cloudinary resource metadata. Detail: {exc}"
			) from exc

		file_format = resource_info.get("format")
		if not file_format:
			raise CloudinaryUploadError("Cloudinary resource does not include format.")

		signed_url = private_download_url(
			public_id,
			file_format,
			resource_type="image",
			type="authenticated",
			expires_at=expires_at,
			attachment=False,
		)

		return {
			"signed_url": signed_url,
			"expires_at": expires_at,
			"expires_in_seconds": expires_in_seconds,
		}

	def ensure_private_delivery(self, public_id: str):
		if not public_id:
			return None

		try:
			cloudinary.api.resource(
				public_id,
				resource_type="image",
				type="authenticated",
			)
			updated_resource = cloudinary.api.update(
				public_id,
				resource_type="image",
				type="authenticated",
				access_control=[{"access_type": "token"}],
			)
			return updated_resource
		except CloudinaryError:
			pass

		try:
			cloudinary.api.resource(
				public_id,
				resource_type="image",
				type="upload",
			)
		except CloudinaryError as exc:
			raise CloudinaryUploadError(
				f"Could not find Cloudinary resource {public_id}. Detail: {exc}"
			) from exc

		# Convert from public delivery to authenticated delivery at end-of-day.
		try:
			rename(
				public_id,
				public_id,
				resource_type="image",
				type="upload",
				to_type="authenticated",
				overwrite=True,
				invalidate=True,
			)
			updated_resource = cloudinary.api.update(
				public_id,
				resource_type="image",
				type="authenticated",
				access_control=[{"access_type": "token"}],
			)
			logger.info("Image delivery converted to authenticated for public_id=%s", public_id)
			return updated_resource
		except CloudinaryError as exc:
			raise CloudinaryUploadError(
				f"Failed to convert image delivery for {public_id}. Detail: {exc}"
			) from exc

	def extract_public_id(self, image_reference: str) -> str:
		if not image_reference:
			raise CloudinaryUploadError("Image reference is empty.")

		if image_reference.startswith("http://") or image_reference.startswith("https://"):
			match = re.search(r"/image/(?:upload|authenticated)/v\d+/(.+)$", image_reference)
			if not match:
				match = re.search(r"/image/(?:upload|authenticated)/(.+)$", image_reference)
			if not match:
				raise CloudinaryUploadError("Could not extract Cloudinary public_id from URL.")
			path = match.group(1)
			if "." in path:
				path = path.rsplit(".", 1)[0]
			return path

		return image_reference

	def resolve_image_access_url(self, image_reference: str, expires_in_seconds: int, user_token: str):
		public_id = self.extract_public_id(image_reference)

		try:
			cloudinary.api.resource(
				public_id,
				resource_type="image",
				type="authenticated",
			)
			signed = self.generate_signed_image_url(public_id, expires_in_seconds)
			token_param = quote(user_token)
			separator = "&" if "?" in signed["signed_url"] else "?"
			return f"{signed['signed_url']}{separator}user_token={token_param}"
		except CloudinaryError:
			try:
				resource_info = cloudinary.api.resource(
					public_id,
					resource_type="image",
					type="upload",
				)
			except CloudinaryError as exc:
				raise CloudinaryUploadError(
					f"Could not resolve image visibility for {public_id}. Detail: {exc}"
				) from exc

			secure_url = resource_info.get("secure_url")
			if secure_url:
				return secure_url

			file_format = resource_info.get("format", "jpg")
			public_url, _ = cloudinary_url(
				public_id,
				resource_type="image",
				type="upload",
				format=file_format,
				secure=True,
			)
			return public_url

	def delete_image(self, image_reference: str):
		if not image_reference:
			return {"deleted": False, "reason": "empty_image_reference"}

		public_id = self.extract_public_id(image_reference)

		for upload_type in ("authenticated", "upload"):
			try:
				result = destroy(
					public_id,
					resource_type="image",
					type=upload_type,
					invalidate=True,
				)
				if result.get("result") in {"ok", "not found"}:
					return {"deleted": result.get("result") == "ok", "result": result.get("result")}
			except CloudinaryError:
				continue

		raise CloudinaryUploadError(f"Failed to delete Cloudinary image for public_id={public_id}.")
