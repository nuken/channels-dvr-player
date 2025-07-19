# Channels DVR Player - Production Deployment Guide

## Quick Deploy on Remote Server

### Option 1: Standard Port Mapping (Recommended)
```bash
# Download the production compose file
wget https://raw.githubusercontent.com/kolns/channels-dvr-player/main/docker-compose.production.yml

# Start the container
docker compose -f docker-compose.production.yml up -d

# Access at: http://YOUR-SERVER-IP:7734
```

### Option 2: Alternative Port (if 7734 is in use)
Edit `docker-compose.production.yml` and change the ports section:
```yaml
ports:
  - "8080:7734"  # Use port 8080 instead
```

Then access at: `http://YOUR-SERVER-IP:8080`

### Option 3: Host Networking (for mDNS discovery)
If your Channels DVR server is on the same network as your Docker server:
```yaml
# Comment out the ports section and uncomment:
network_mode: host
```

## Troubleshooting Connection Issues

### 1. Check if container is running:
```bash
docker ps | grep channels-dvr-player
```

### 2. Check container logs:
```bash
docker logs channels-dvr-player
```

### 3. Test local connectivity on server:
```bash
curl -I http://localhost:7734
```

### 4. Check if port is open:
```bash
# On the Docker server
ss -tlnp | grep :7734
```

### 5. Check firewall (Ubuntu/Debian):
```bash
sudo ufw status
sudo ufw allow 7734  # If needed
```

### 6. Check firewall (CentOS/RHEL):
```bash
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=7734/tcp --permanent  # If needed
sudo firewall-cmd --reload
```

## Common Port Alternatives
- **8080** - `"8080:7734"`
- **3000** - `"3000:7734"`  
- **9090** - `"9090:7734"`
- **7735** - `"7735:7734"`

## Environment Variables
```bash
# Optional: Set custom secret key
export SECRET_KEY="your-super-secret-key-here"
docker compose -f docker-compose.production.yml up -d
```

## Persistent Data
The configuration and database will be stored in `./config/` directory on your server.

## Updates
```bash
# Pull latest image
docker pull kolnsdocker/channels-dvr-player:latest

# Restart with new image
docker compose -f docker-compose.production.yml up -d
```
