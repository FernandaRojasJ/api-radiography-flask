import time

import cloudinary
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.uploader import upload
from cloudinary.utils import private_download_url


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
		if upload_type != "authenticated":
			raise CloudinaryUploadError(
				"Invalid CLOUDINARY_UPLOAD_TYPE. Only 'authenticated' is allowed."
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

		try:
			result = upload(
				file_stream,
				folder=self.folder,
				public_id=public_id,
				resource_type="image",
				type=self.upload_type,
				overwrite=True,
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
