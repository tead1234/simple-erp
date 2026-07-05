import io
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

_service = None


def _get_service():
    global _service
    if _service is None:
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN")
        if not (client_id and client_secret and refresh_token):
            raise RuntimeError(
                "GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET / GOOGLE_OAUTH_REFRESH_TOKEN "
                "환경변수가 설정되지 않았습니다"
            )
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        _service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    return _service


def _folder_id() -> str:
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID 환경변수가 설정되지 않았습니다")
    return folder_id


def upload(filename: str, content_type: str, data: bytes) -> str:
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=content_type)
    file = _get_service().files().create(
        body={"name": filename, "parents": [_folder_id()]},
        media_body=media,
        fields="id",
    ).execute()
    return file["id"]


def download(file_id: str) -> bytes:
    return _get_service().files().get_media(fileId=file_id).execute()


def delete(file_id: str) -> None:
    _get_service().files().delete(fileId=file_id).execute()
