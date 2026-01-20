
# Arr Stack - Media Automation Suite

A complete Docker-based media automation stack featuring torrent management, content discovery, and streaming services.

## Services Overview

This stack includes the following services:

### Core Services
- **qBittorrent** (Port 8085) - Torrent client with web interface
- **Sonarr** (Port 8989) - TV show automation and management
- **Sonarr Anime** (Port 8990) - Dedicated Sonarr instance for anime content
- **Radarr** (Port 7878) - Movie automation and management
- **Prowlarr** (Port 9696) - Indexer management for Sonarr and Radarr

### Support Services
- **FlareSolverr** (Port 8191) - Cloudflare challenge solver for indexers
- **Jellyseerr** (Port 5055) - Request management for movies and TV shows
- **Jellyfin** (Port 8096) - Media streaming server

## Prerequisites

- Docker and Docker Compose installed
- Sufficient storage space for media files
- Basic understanding of media automation workflows

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd arr-stack
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
3. **Edit the `.env` file with your settings**

## Environment Variables

### System Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `PUID` | User ID for file permissions | `1000` |
| `PGID` | Group ID for file permissions | `1000` |
| `TIMEZONE` | System timezone | `America/New_York` |

### Storage Paths
| Variable | Description | Example |
|----------|-------------|---------|
| `CONFIG_PATH` | Path for application configurations | `/home/user/arr-stack/config` |
| `MEDIA_PATH` | Path for media files storage | `/home/user/media` |

### qBittorrent Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `QBITTORRENT_WEBUI_PORT` | Web interface port | `8085` |
| `QBITTORRENT_CONNECT_PORT` | Connection port for torrent traffic | `6881` |

## Getting Started

1. **Start the services**
   ```bash
   docker-compose up -d
   ```

2. **Access the web interfaces**
   - qBittorrent: http://localhost:8085
   - Sonarr: http://localhost:8989
   - Sonarr Anime: http://localhost:8990
   - Radarr: http://localhost:7878
   - Prowlarr: http://localhost:9696
   - Jellyseerr: http://localhost:5055
   - Jellyfin: http://localhost:8096

3. **Initial Configuration**
   - Configure Prowlarr indexers first
   - Set up download clients in Sonarr/Radarr pointing to qBittorrent
   - Configure media libraries in Jellyfin
   - Connect Jellyseerr to your *arr services

> **_NOTE:_** If using podman, make sure to activate podman-restart service to ensure containers restart on system reboot.

## Network Configuration

All services run on the `arr-network` Docker network, enabling secure inter-service communication.

## Backup

The project includes a backup script at `backup/src/drive-backup.py` for backing up your configuration and data.

## Troubleshooting

- Ensure all required environment variables are set in `.env`
- Check container logs: `docker-compose logs <service-name>`
- Verify file permissions match your `PUID` and `PGID` settings
- Ensure sufficient disk space for media and configuration files

## Security Notes

- Change default passwords after initial setup
- Consider using a VPN for torrent traffic
- Regularly update container images for security patches

## Contributing

Feel free to submit issues and pull requests to improve this stack configuration.