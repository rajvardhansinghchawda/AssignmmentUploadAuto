"""
Google Drive API v3 — upload generated answer docs to the student's Drive.
Folder structure: PIEMR Assignments / <subject_name> / <file>
"""
import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

_FOLDER_MIME = "application/vnd.google-apps.folder"
_DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def upload_to_drive(
    filepath: str,
    access_token: str,
    refresh_token: str,
    subject_name: str,
) -> str:
    """
    Upload a .docx file to the student's Google Drive.
    Returns the web-view URL of the uploaded file.
    """
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )

    # Refresh token if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        logger.info("[drive_service] Access token refreshed successfully")

    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    root_id = _get_or_create_folder(service, "PIEMR Assignments")
    subject_id = _get_or_create_folder(service, subject_name, parent_id=root_id)

    filename = os.path.basename(filepath)
    media = MediaFileUpload(filepath, mimetype=_DOCX_MIME, resumable=True)
    file_meta = {"name": filename, "parents": [subject_id]}

    uploaded = (
        service.files()
        .create(body=file_meta, media_body=media, fields="id,webViewLink")
        .execute()
    )

    drive_url = uploaded.get("webViewLink", "")
    logger.info(f"[drive_service] Uploaded '{filename}' → {drive_url}")
    return drive_url


def _get_or_create_folder(service, name: str, parent_id: str = None) -> str:
    """Return existing folder ID or create it and return the new ID."""
    query = f"name='{name}' and mimeType='{_FOLDER_MIME}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id)", pageSize=1).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    meta = {"name": name, "mimeType": _FOLDER_MIME}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    logger.debug(f"[drive_service] Created Drive folder '{name}' (id={folder['id']})")
    return folder["id"]
