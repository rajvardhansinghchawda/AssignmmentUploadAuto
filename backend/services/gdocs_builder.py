"""
Google Docs API integration to create and format documents directly in user's Drive.
"""
import os
import io
import logging
from datetime import date
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_FOLDER_MIME = "application/vnd.google-apps.folder"

from services import drive_service

def build_google_doc(
    subject_name: str,
    student_info: dict,
    qa_pairs: dict,
    access_token: str,
    refresh_token: str,
) -> str:
    """
    Creates a formatted Google Doc in the user's Drive.
    Returns the doc ID.
    """
    creds = _get_creds(access_token, refresh_token)
    docs_service = build("docs", "v1", credentials=creds, cache_discovery=False)
    # Note: drive_service from discovery, not our local module name collision
    drive_api = build("drive", "v3", credentials=creds, cache_discovery=False)

    # 1. Create or get folder via our drive_service helper
    root_folder_id = drive_service._get_or_create_folder(drive_api, "PIEMR Assignments")
    subject_folder_id = drive_service._get_or_create_folder(drive_api, subject_name, parent_id=root_folder_id)

    # 2. Create blank document in the folder
    title = f"Assignment — {subject_name} ({date.today().isoformat()})"
    doc_meta = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [subject_folder_id]
    }
    gdoc = drive_api.files().create(body=doc_meta, fields="id").execute()
    doc_id = gdoc.get("id")

    # 3. Assemble content and track formatting regions
    full_text = ""
    formatting_requests = []

    def add_text(text, style=None, align=None):
        nonlocal full_text
        start = len(full_text)
        full_text += text
        end = len(full_text)
        
        # Docs API index mapping: We will insert at index 1 in the document.
        # So range [0, 5] in full_text becomes [1, 6] in the doc.
        doc_start = start + 1
        doc_end = end + 1

        if style:
            formatting_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": doc_start, "endIndex": doc_end},
                    "textStyle": style,
                    "fields": ",".join(style.keys())
                }
            })
        if align:
            formatting_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": doc_start, "endIndex": doc_end},
                    "paragraphStyle": {"alignment": align},
                    "fields": "alignment"
                }
            })

    # Header
    add_text(
        "Prestige Institute of Engineering Management and Research (PIEMR)\n",
        style={"fontSize": {"magnitude": 9, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": {"red": 0.42, "green": 0.45, "blue": 0.5}}}},
        align="CENTER"
    )

    # Title
    add_text(
        f"Assignment — {subject_name}\n",
        style={"bold": True, "fontSize": {"magnitude": 18, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": {"red": 0.1, "green": 0.34, "blue": 0.86}}}},
        align="CENTER"
    )

    # Info
    name = student_info.get("full_name") or student_info.get("name", "N/A")
    enrollment = student_info.get("enrollment", "N/A")
    add_text(
        f"Name: {name}    |    Enrollment: {enrollment}    |    Date: {date.today().strftime('%d %B %Y')}\n\n",
        style={"fontSize": {"magnitude": 10, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": {"red": 0.42, "green": 0.45, "blue": 0.5}}}},
        align="CENTER"
    )

    # Q&A
    for i, (q, a) in enumerate(qa_pairs.items(), 1):
        add_text(f"Q{i}. {q}\n", style={"bold": True, "fontSize": {"magnitude": 12, "unit": "PT"}})
        add_text(f"{a}\n\n")

    # Footer
    # add_text(
    #     f"\nGenerated for: {name}\n",
    #     style={"italic": True, "fontSize": {"magnitude": 8, "unit": "PT"}, "foregroundColor": {"color": {"rgbColor": {"red": 0.6, "green": 0.64, "blue": 0.69}}}},
    #     align="CENTER"
    # )

    # 4. Execute single batch update
    # In Google Docs, index 0 is valid. However, inserting at 1 is also common to preserve the initial \n.
    # We use index 1 because blank doc has \n at 0.
    final_requests = [
        {"insertText": {"location": {"index": 1}, "text": full_text}}
    ] + formatting_requests

    docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": final_requests}).execute()
    
    logger.info(f"[gdocs_builder] Created and formatted Google Doc: {doc_id}")
    return doc_id


def export_to_local_docx(doc_id: str, output_path: str, access_token: str, refresh_token: str):
    """
    Downloads a Google Doc as a local .docx file.
    """
    creds = _get_creds(access_token, refresh_token)
    drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
    
    request = drive_service.files().export_media(fileId=doc_id, mimeType=_DOCX_MIME)
    
    with io.FileIO(output_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    
    logger.info(f"[gdocs_builder] Exported doc {doc_id} to {output_path}")


def _get_creds(access_token, refresh_token):
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
