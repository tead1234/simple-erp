import io
import os
import threading

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

# googleapiclient 서비스 객체는 스레드 세이프하지 않음(내부 http transport 공유 불가).
# FastAPI 동기 라우트는 스레드풀에서 실행되므로 스레드별로 별도 서비스를 캐시한다.
_local = threading.local()


def _get_service():
    if getattr(_local, "service", None) is None:
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
        _local.service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    return _local.service


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
    try:
        return _get_service().files().get_media(fileId=file_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(f"드라이브 파일을 찾을 수 없습니다: {file_id}") from e
        raise


def delete(file_id: str) -> None:
    try:
        _get_service().files().delete(fileId=file_id).execute()
    except HttpError as e:
        if e.resp.status != 404:
            raise
