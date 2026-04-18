import requests
import os
import sys

from dotenv import load_dotenv

class JellyService:
    def __init__(self, host: str, api_key: str):
        self.host = host
        self.api_key = api_key

    def __str__(self):
        return f"{self.host}"
    
JELLYFIN_SERVICE = "JELLYFIN"

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
def initialize_service() -> JellyService:
    load_dotenv()

    api_key = os.getenv(JELLYFIN_SERVICE.upper() + "_APIKEY") or ""
    host = os.getenv(JELLYFIN_SERVICE.upper() + "_HOST")

    if host is None or not host.strip():
        print(f"No host given for {JELLYFIN_SERVICE} service")
        sys.exit(1)
    
    if not api_key:
        print(f"No api key given for {JELLYFIN_SERVICE} service")
        sys.exit(1)

    return JellyService(host, api_key)

def create_backup(service: JellyService):
    url = f"http://{service.host}/Backup"
    
    headers = {
            "Accept": "application/json"
        }
    
    params = {"api_key": service.api_key}
    
    backupParameters = """
        {
            "Database": true,
            "Metadata": false,
            "Subtitles": false,
            "Trickplay": false
        }
    """
    
    response = requests.post(url=url, headers=headers, params=params, json=backupParameters)
    
    if response.status_code != 200:
        print(f"Error creating backup for {service.host}")
    
    body: list[dict] = response.json()
    backupPath: str = body[0]["Path"]
    print(f"Backup successfully created and saved to {backupPath}")
    

def main():
    service = initialize_service()
    create_backup(service)
    

if __name__ == "__main__":
    main()