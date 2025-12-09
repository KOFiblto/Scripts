SERVICES = [
    {
        "id": "sabnzbd",
        "name": "Sabnzbd",
        "port": 9006,
        "description": "Newsreader",
        "container_name": "sabnzbd",
        "image": "sabnzbd.webp"
    },
    {
        "id": "radarr",
        "name": "Radarr",
        "port": 9004,
        "description": "Movie Manager",
        "container_name": "radarr",
        "image": "radarr.webp"
    },
    {
        "id": "sonarr",
        "name": "Sonarr",
        "port": 9005,
        "description": "TV Series Manager",
        "container_name": "sonarr",
        "image": "sonarr.webp"
    },
    {
        "id": "whisparr",
        "name": "Whisparr",
        "port": 9008,
        "description": "Adult Movie Manager",
        "container_name": "whisparr",
        "image": "whisparr.webp"
    },
    {
        "id": "bazarr",
        "name": "Bazarr",
        "port": 9003,
        "description": "Subtitle Manager",
        "container_name": "bazarr",
        "image": "bazarr.webp"
    },
    {
        "id": "tdarr",
        "name": "Tdarr",
        "port": 9007,
        "description": "Transcoding Manager",
        "container_name": "tdarr",
        "image": "tdarr.webp"
    },
    {
        "id": "jellyfin",
        "name": "Jellyfin",
        "port": 9001,
        "description": "Media Server",
        "container_name": "jellyfin",
        "image": "jellyfin.webp"
    },
    {
        "id": "plex",
        "name": "Plex",
        "port": 9002,
        "description": "Media Server",
        "container_name": "plex",
        "image": "plex.webp"
    },
    {
        "id": "organizr",
        "name": "Organizr",
        "port": 9009,
        "description": "Service Organizer",
        "container_name": "organizr",
        "image": "organizr.webp"
    },
    {
        "id": "synapse",
        "name": "Synapse",
        "port": 8008,
        "description": "Matrix Homeserver",
        "container_name": "synapse",
        "image": "message-square" 
    },
    {
        "id": "portainer",
        "name": "Portainer",
        "port": 9000,
        "description": "Docker Management",
        "container_name": "portainer",
        "image": "container"
    }
]

SERVER_IP = "192.168.178.62"
