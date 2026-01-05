import os
import os.path
import argparse
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Full drive scope (allows reading and writing). If you change scopes,
# delete `token.json` so the consent flow runs again.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service() -> object:
  load_dotenv()
  # Store credentials/token under CONFIG_PATH/backuper for protection.
  config_root = os.environ.get("CONFIG_PATH")
  if not config_root:
    # Fall back to XDG or user config if CONFIG_PATH not set.
    config_root = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
  backuper_dir = os.path.join(config_root, "backuper")
  os.makedirs(backuper_dir, exist_ok=True)

  token_path = os.path.join(backuper_dir, "token.json")
  credentials_path = os.path.join(backuper_dir, "credentials.json")

  creds = None
  if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      # Prefer credentials stored in CONFIG_PATH/backuper/credentials.json
      if os.path.exists(credentials_path):
        secret_file = credentials_path
      elif os.path.exists("credentials.json"):
        # fallback to current dir for convenience
        secret_file = "credentials.json"
      else:
        raise FileNotFoundError(
            f"credentials.json not found in {backuper_dir} or current directory"
        )
      flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials/token to protected location
    with open(token_path, "w") as token:
      token.write(creds.to_json())
  return build("drive", "v3", credentials=creds)


def list_files(service, page_size: int = 10):
  results = (
      service.files()
      .list(pageSize=page_size, fields="nextPageToken, files(id, name)")
      .execute()
  )
  items = results.get("files", [])
  if not items:
    print("No files found.")
    return
  print("Files:")
  for item in items:
    print(f"{item['name']} ({item['id']})")


def find_folder(service, name: str, parent_id: Optional[str] = None) -> Optional[str]:
  q = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
  if parent_id:
    q += f" and '{parent_id}' in parents"
  resp = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
  files = resp.get("files", [])
  return files[0]["id"] if files else None


def create_folder(service, name: str, parent_id: Optional[str] = None) -> str:
  metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
  if parent_id:
    metadata["parents"] = [parent_id]  # type: ignore
  folder = service.files().create(body=metadata, fields="id").execute()
  return folder["id"]


def find_or_create_folder_by_path(service, path: str, root_id: Optional[str] = None) -> str:
  # path like "Backups/2026/arr"
  parts = [p for p in path.split("/") if p]
  parent = root_id
  for part in parts:
    found = find_folder(service, part, parent)
    if found:
      parent = found
    else:
      parent = create_folder(service, part, parent)
  if parent is None:
    raise RuntimeError(f"failed to find or create folder for path: {path}")
  return parent


def upload_file(service, file_path: str, parent_id: str) -> str:
  name = os.path.basename(file_path)
  media = MediaFileUpload(file_path, mimetype="application/zip", resumable=True)
  metadata = {"name": name, "parents": [parent_id]}
  uploaded = service.files().create(body=metadata, media_body=media, fields="id").execute()
  return uploaded.get("id")


def main():
  parser = argparse.ArgumentParser(description="Drive helper: list or upload files")
  parser.add_argument("--list", action="store_true", help="List files (default behavior)")
  parser.add_argument("--upload", "-u", help="Path to zip file to upload")
  parser.add_argument("--folder-id", help="Target Drive folder ID (optional)")
  parser.add_argument("--folder-path", help="Target Drive folder path, e.g. Backups/2026 (optional)")
  args = parser.parse_args()

  try:
    service = get_service()
    if args.upload:
      if not os.path.exists(args.upload):
        print(f"Local file not found: {args.upload}")
        return
      if args.folder_id:
        parent_id = args.folder_id
      elif args.folder_path:
        parent_id = find_or_create_folder_by_path(service, args.folder_path)
      else:
        print("Specify --folder-id or --folder-path for upload target")
        return
      file_id = upload_file(service, args.upload, parent_id)
      print(f"Uploaded {args.upload} -> fileId: {file_id}")
    else:
      list_files(service)
  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()