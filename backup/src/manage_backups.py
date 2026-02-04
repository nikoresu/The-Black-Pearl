import os
import requests
import shutil
import sys

from datetime import date
from dotenv import load_dotenv
from urllib.parse import urlparse

from drive_backup import get_service, find_or_create_folder_by_path, upload_file

# Not supported (yet): Jellyseerr, qBittorrent, Bazarr
SUPPORTED_SERVICES = ["prowlarr", "radarr", "sonarr", "jellyfin"]


class Service:
    def __init__(self, name: str, host: str, api_key: str):
        self.name = name
        self.host = host
        self.api_key = api_key
        self.backup_path = ""

    def __str__(self):
        return f"{self.name}: {self.host} - path: {self.backup_path}"


# Get config path
def get_backuper_dir() -> str:
    config_root = os.environ.get("CONFIG_PATH")
    if not config_root:
        # Fall back to XDG or user config if CONFIG_PATH not set.
        config_root = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")

    backuper_dir = os.path.join(config_root, "backuper")
    os.makedirs(backuper_dir, exist_ok=True)

    return backuper_dir


# Get hosts and api keys from services
def define_services() -> list[Service]:
    load_dotenv()
    service_names = os.getenv("SERVICES").split(",")

    service_objects = []

    for listedService in service_names:
        name = listedService
        api_key = os.getenv(name.upper() + "_APIKEY")
        host = os.getenv(name.upper() + "_HOST")

        # No special host, use general
        if host is None or not host.strip():
            print(f"No host given for {name} service")
            sys.exit(1)

        service_objects.append(Service(name, host, api_key))

    return service_objects


# Get backup paths depending on the service type
def get_backups(service_list: list[Service]):
    for serviceObject in service_list:
        url = ""
        headers = {
            "Accept": "application/json"
        }
        params = {}
        backup_path = "path"

        match serviceObject.name:
            case name if "prowlarr" in name:
                url = f"http://{serviceObject.host}/api/v1/system/backup"
                headers["X-Api-Key"] = serviceObject.api_key

            case name if "radarr" in name or "sonarr" in name:
                url = f"http://{serviceObject.host}/api/v3/system/backup"
                headers["X-Api-Key"] = serviceObject.api_key

            case name if "jellyfin" in name:
                url = f"http://{serviceObject.host}/Backup"
                params["api_key"] = serviceObject.api_key
                backup_path = "Path"

            case _:
                print(f"Getting an UNSUPPORTED service... {serviceObject}")
                continue

        response = requests.get(url=url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"No backup found for {serviceObject.name}")

        # Get the latest backup path if present
        body: list[dict] = response.json()
        if body:
            if "jellyfin" in serviceObject.name:
                """
                Jellyfin does not allow downloading backups from API
                Supported only if jellyfin instance is in the same host that runs this script
                """
                serviceObject.backup_path = body[0][backup_path].removeprefix("/config/")
            else:
                serviceObject.backup_path = f"http://{serviceObject.host}{body[0][backup_path]}"


# Download backups to the working folder
def download_backups(service_list: list[Service]):
    backuper_dir = get_backuper_dir()
    working_dir = os.path.join(backuper_dir, "working")
    os.makedirs(working_dir, exist_ok=True)

    for serviceObject in service_list:
        # Download from service API
        if "http" in serviceObject.backup_path:
            url = serviceObject.backup_path
            filename = os.path.basename(urlparse(url).path)
            dest = os.path.join(working_dir, filename)

            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

            print(f"Downloaded backup for {serviceObject.name}: {dest}")

        # Get from arr's data path
        else:
            data_path = os.getenv("CONFIG_PATH")
            if not data_path:
                print(f"No CONFIG_PATH found. Unable to extract backup for {serviceObject.name}")
                continue

            source = os.path.join(data_path + "/" + serviceObject.name, serviceObject.backup_path)
            filename = os.path.basename(urlparse(serviceObject.backup_path).path)
            dest = os.path.join(working_dir, filename)

            shutil.copy(source, dest)

            print(f"Moved backup from filesystem for {serviceObject.name}: {dest}")


# Zip all backups
def zip_working_dir() -> str:
    backuper_dir = get_backuper_dir()
    working_dir = os.path.join(backuper_dir, "working")
    timestamp = date.today().isoformat()

    filename = os.path.join(backuper_dir, f"arr-data-{timestamp}")

    shutil.make_archive(filename, 'zip', working_dir)

    print(f"Working folder zipped into {filename}.zip")

    try:
        shutil.rmtree(working_dir)
        print(f"Deleted working folder")
    except OSError as e:
        print(f"Error deleting {working_dir}: {e.strerror}")

    return f"{filename}.zip"

# Upload to Google Drive - Might add other strategies later
def upload_to_drive(file: str):
    folder_path = os.getenv("GDRIVE_FOLDER_PATH", "Backups/arr")

    try:
        drive_service = get_service()
        parent_id = find_or_create_folder_by_path(drive_service, folder_path)
        file_id = upload_file(drive_service, file, parent_id)
        print(f"Uploaded to Google Drive: {file_id} - {urlparse(file).path}/{file}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    services = define_services()
    get_backups(services)
    download_backups(services)
    zip_file = zip_working_dir()
    upload_to_drive(zip_file)
