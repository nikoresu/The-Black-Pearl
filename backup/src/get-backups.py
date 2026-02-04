import requests
import os
import sys

from dotenv import load_dotenv

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
                serviceObject.backup_path = body[0][backup_path].removeprefix("/config/data")
            else:
                serviceObject.backup_path = f"http://{serviceObject.host}{body[0][backup_path]}"


if __name__ == "__main__":
    services = define_services()
    get_backups(services)

    for service in services:
        print(service)
