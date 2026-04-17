import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///./"):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        relative_path = database_url.replace("sqlite:///./", "", 1)
        absolute_path = os.path.join(project_root, relative_path)
        return f"sqlite:///{absolute_path}"
    return database_url


class Config:
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./xray_database.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "xray_records")
    CLOUDINARY_UPLOAD_TYPE = os.getenv("CLOUDINARY_UPLOAD_TYPE", "authenticated")
    CLOUDINARY_SIGNED_URL_TTL_SECONDS = int(
        os.getenv("CLOUDINARY_SIGNED_URL_TTL_SECONDS", "600")
    )
    SECURE_IMAGE_TOKEN_TTL_SECONDS = int(
        os.getenv("SECURE_IMAGE_TOKEN_TTL_SECONDS", "600")
    )
    CLOUDINARY_MIN_SIGNED_URL_TTL_SECONDS = int(
        os.getenv("CLOUDINARY_MIN_SIGNED_URL_TTL_SECONDS", "10")
    )
    CLOUDINARY_MAX_SIGNED_URL_TTL_SECONDS = int(
        os.getenv("CLOUDINARY_MAX_SIGNED_URL_TTL_SECONDS", "600")
    )
    IMAGE_PRIVACY_SCHEDULER_ENABLED = os.getenv("IMAGE_PRIVACY_SCHEDULER_ENABLED", "true").lower() == "true"
    IMAGE_DELETE_REMOTE_ON_RECORD_DELETE = os.getenv(
        "IMAGE_DELETE_REMOTE_ON_RECORD_DELETE", "true"
    ).lower() == "true"
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024