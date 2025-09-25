# Deployment Guide

This guide covers various deployment options for ForexSmartBot, from local development to production environments.

## Table of Contents

- [Local Development](#local-development)
- [VPS Deployment](#vps-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Security](#security)
- [Backup & Recovery](#backup--recovery)

## Local Development

### Prerequisites

- Python 3.11 or higher
- 4 GB RAM (8 GB recommended)
- 1 GB free disk space
- Git

### Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/voxhash/ForexSmartBot.git
   cd ForexSmartBot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Run application**:
   ```bash
   python app.py
   ```

### Development Features

- **Hot Reload**: Automatic reload on code changes
- **Debug Mode**: Enhanced error reporting
- **Test Mode**: Isolated testing environment
- **Logging**: Detailed development logs

## VPS Deployment

### Prerequisites

- VPS with Ubuntu 20.04+ or CentOS 8+
- 2 GB RAM minimum (4 GB recommended)
- 10 GB free disk space
- Root or sudo access
- Static IP address

### Server Setup

1. **Update system**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python 3.11**:
   ```bash
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

3. **Install system dependencies**:
   ```bash
   sudo apt install build-essential libssl-dev libffi-dev
   sudo apt install python3-pip git curl wget
   ```

4. **Create user**:
   ```bash
   sudo adduser forexsmartbot
   sudo usermod -aG sudo forexsmartbot
   ```

### Application Deployment

1. **Switch to user**:
   ```bash
   sudo su - forexsmartbot
   ```

2. **Clone repository**:
   ```bash
   git clone https://github.com/voxhash/ForexSmartBot.git
   cd ForexSmartBot
   ```

3. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create data directory**:
   ```bash
   mkdir -p ~/.forexsmartbot
   chmod 755 ~/.forexsmartbot
   ```

### Service Configuration

1. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/forexsmartbot.service
   ```

2. **Service file content**:
   ```ini
   [Unit]
   Description=ForexSmartBot Trading Bot
   After=network.target

   [Service]
   Type=simple
   User=forexsmartbot
   WorkingDirectory=/home/forexsmartbot/ForexSmartBot
   Environment=PATH=/home/forexsmartbot/ForexSmartBot/venv/bin
   ExecStart=/home/forexsmartbot/ForexSmartBot/venv/bin/python app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable forexsmartbot
   sudo systemctl start forexsmartbot
   ```

4. **Check status**:
   ```bash
   sudo systemctl status forexsmartbot
   ```

### X11 Forwarding (for GUI)

1. **Install X11 forwarding**:
   ```bash
   sudo apt install xvfb
   ```

2. **Create display script**:
   ```bash
   nano ~/start_forexsmartbot.sh
   ```

3. **Script content**:
   ```bash
   #!/bin/bash
   export DISPLAY=:99
   Xvfb :99 -screen 0 1024x768x24 &
   source ~/ForexSmartBot/venv/bin/activate
   cd ~/ForexSmartBot
   python app.py
   ```

4. **Make executable**:
   ```bash
   chmod +x ~/start_forexsmartbot.sh
   ```

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4 GB RAM
- 10 GB free disk space

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libgconf-2-4 \
    libnss3 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxinerama1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Expose port (if needed)
EXPOSE 8080

# Create non-root user
RUN useradd -m -u 1000 forexsmartbot
RUN chown -R forexsmartbot:forexsmartbot /app
USER forexsmartbot

# Start command
CMD ["python", "app.py"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  forexsmartbot:
    build: .
    container_name: forexsmartbot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ~/.forexsmartbot:/home/forexsmartbot/.forexsmartbot
    environment:
      - PYTHONPATH=/app
      - DISPLAY=:99
    ports:
      - "8080:8080"
    depends_on:
      - xvfb
    networks:
      - forexsmartbot-network

  xvfb:
    image: selenium/standalone-chrome:latest
    container_name: forexsmartbot-xvfb
    restart: unless-stopped
    environment:
      - DISPLAY=:99
    ports:
      - "4444:4444"
    networks:
      - forexsmartbot-network

networks:
  forexsmartbot-network:
    driver: bridge

volumes:
  forexsmartbot-data:
    driver: local
```

### Build and Run

1. **Build image**:
   ```bash
   docker build -t forexsmartbot .
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Check logs**:
   ```bash
   docker-compose logs -f forexsmartbot
   ```

4. **Stop services**:
   ```bash
   docker-compose down
   ```

## Cloud Deployment

### AWS EC2

1. **Launch EC2 instance**:
   - Instance type: t3.medium or larger
   - OS: Ubuntu 20.04 LTS
   - Storage: 20 GB GP3
   - Security group: Allow SSH (22) and HTTP (80/443)

2. **Connect to instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Follow VPS deployment steps**

4. **Configure load balancer** (if needed):
   - Create Application Load Balancer
   - Configure target groups
   - Set up health checks

### Google Cloud Platform

1. **Create Compute Engine instance**:
   - Machine type: e2-medium or larger
   - OS: Ubuntu 20.04 LTS
   - Boot disk: 20 GB SSD

2. **Connect to instance**:
   ```bash
   gcloud compute ssh your-instance-name --zone=your-zone
   ```

3. **Follow VPS deployment steps**

### Azure

1. **Create Virtual Machine**:
   - Size: Standard_B2s or larger
   - OS: Ubuntu 20.04 LTS
   - Disk: 20 GB SSD

2. **Connect to instance**:
   ```bash
   ssh azureuser@your-instance-ip
   ```

3. **Follow VPS deployment steps**

### DigitalOcean

1. **Create Droplet**:
   - Size: 2 GB RAM or larger
   - OS: Ubuntu 20.04 LTS
   - Storage: 20 GB SSD

2. **Connect to instance**:
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Follow VPS deployment steps**

## Production Considerations

### Performance Optimization

1. **Resource allocation**:
   - CPU: 2+ cores recommended
   - RAM: 4+ GB recommended
   - Storage: SSD recommended
   - Network: Stable connection

2. **Application optimization**:
   - Use production Python interpreter
   - Enable JIT compilation
   - Optimize data processing
   - Cache frequently used data

3. **Database optimization**:
   - Use connection pooling
   - Optimize queries
   - Regular maintenance
   - Backup strategies

### Scalability

1. **Horizontal scaling**:
   - Load balancer
   - Multiple instances
   - Shared storage
   - Session management

2. **Vertical scaling**:
   - Increase resources
   - Optimize code
   - Better algorithms
   - Caching strategies

### High Availability

1. **Redundancy**:
   - Multiple instances
   - Load balancer
   - Database replication
   - Backup systems

2. **Monitoring**:
   - Health checks
   - Performance metrics
   - Error tracking
   - Alerting

## Monitoring & Maintenance

### Logging

1. **Configure logging**:
   ```python
   import logging
   from logging.handlers import RotatingFileHandler

   # Create logger
   logger = logging.getLogger('forexsmartbot')
   logger.setLevel(logging.INFO)

   # Create file handler
   handler = RotatingFileHandler(
       'logs/forexsmartbot.log',
       maxBytes=10*1024*1024,  # 10MB
       backupCount=5
   )

   # Create formatter
   formatter = logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   handler.setFormatter(formatter)

   # Add handler to logger
   logger.addHandler(handler)
   ```

2. **Log rotation**:
   ```bash
   # Configure logrotate
   sudo nano /etc/logrotate.d/forexsmartbot
   ```

3. **Log content**:
   ```bash
   /home/forexsmartbot/ForexSmartBot/logs/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       create 644 forexsmartbot forexsmartbot
   }
   ```

### Monitoring

1. **System monitoring**:
   ```bash
   # Install monitoring tools
   sudo apt install htop iotop nethogs
   ```

2. **Application monitoring**:
   ```python
   import psutil
   import time

   def monitor_system():
       while True:
           # CPU usage
           cpu_percent = psutil.cpu_percent()
           
           # Memory usage
           memory = psutil.virtual_memory()
           memory_percent = memory.percent
           
           # Disk usage
           disk = psutil.disk_usage('/')
           disk_percent = disk.percent
           
           # Log metrics
           logger.info(f"CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%")
           
           time.sleep(60)  # Check every minute
   ```

3. **Health checks**:
   ```python
   def health_check():
       try:
           # Check database connection
           # Check broker connection
           # Check data provider
           # Check risk engine
           return True
       except Exception as e:
           logger.error(f"Health check failed: {e}")
           return False
   ```

### Maintenance

1. **Regular updates**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Update application
   cd ~/ForexSmartBot
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database maintenance**:
   ```bash
   # SQLite maintenance
   sqlite3 ~/.forexsmartbot/trades.db "VACUUM;"
   sqlite3 ~/.forexsmartbot/trades.db "ANALYZE;"
   ```

3. **Log cleanup**:
   ```bash
   # Clean old logs
   find ~/.forexsmartbot/logs -name "*.log" -mtime +30 -delete
   ```

## Security

### Access Control

1. **SSH security**:
   ```bash
   # Disable root login
   sudo nano /etc/ssh/sshd_config
   # Set: PermitRootLogin no
   
   # Use key-based authentication
   # Set: PasswordAuthentication no
   
   # Restart SSH
   sudo systemctl restart ssh
   ```

2. **Firewall configuration**:
   ```bash
   # Install UFW
   sudo apt install ufw
   
   # Configure firewall
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

3. **User permissions**:
   ```bash
   # Create dedicated user
   sudo adduser forexsmartbot
   sudo usermod -aG sudo forexsmartbot
   
   # Set proper permissions
   sudo chown -R forexsmartbot:forexsmartbot /home/forexsmartbot/ForexSmartBot
   sudo chmod -R 755 /home/forexsmartbot/ForexSmartBot
   ```

### Data Protection

1. **Encryption**:
   ```bash
   # Encrypt sensitive data
   sudo apt install ecryptfs-utils
   sudo ecryptfs-setup-private
   ```

2. **Backup encryption**:
   ```bash
   # Encrypt backups
   tar -czf - ~/.forexsmartbot | gpg --symmetric --cipher-algo AES256 -o backup.tar.gz.gpg
   ```

3. **API key protection**:
   ```bash
   # Store API keys in environment variables
   echo 'export FOREXSMARTBOT_API_KEY="your_api_key"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Network Security

1. **VPN setup**:
   ```bash
   # Install OpenVPN
   sudo apt install openvpn
   
   # Configure VPN client
   sudo openvpn --config client.ovpn
   ```

2. **SSL/TLS**:
   ```bash
   # Install Let's Encrypt
   sudo apt install certbot
   
   # Generate certificate
   sudo certbot certonly --standalone -d your-domain.com
   ```

## Backup & Recovery

### Backup Strategy

1. **Application backup**:
   ```bash
   # Create backup script
   nano ~/backup_forexsmartbot.sh
   ```

2. **Backup script content**:
   ```bash
   #!/bin/bash
   BACKUP_DIR="/backup/forexsmartbot"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup directory
   mkdir -p $BACKUP_DIR
   
   # Backup application
   tar -czf $BACKUP_DIR/forexsmartbot_$DATE.tar.gz ~/ForexSmartBot
   
   # Backup data
   tar -czf $BACKUP_DIR/data_$DATE.tar.gz ~/.forexsmartbot
   
   # Backup database
   cp ~/.forexsmartbot/trades.db $BACKUP_DIR/trades_$DATE.db
   
   # Clean old backups (keep 30 days)
   find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
   find $BACKUP_DIR -name "*.db" -mtime +30 -delete
   ```

3. **Make executable**:
   ```bash
   chmod +x ~/backup_forexsmartbot.sh
   ```

4. **Schedule backup**:
   ```bash
   # Add to crontab
   crontab -e
   # Add: 0 2 * * * /home/forexsmartbot/backup_forexsmartbot.sh
   ```

### Recovery Process

1. **Application recovery**:
   ```bash
   # Stop service
   sudo systemctl stop forexsmartbot
   
   # Restore application
   tar -xzf /backup/forexsmartbot/forexsmartbot_YYYYMMDD_HHMMSS.tar.gz -C ~/
   
   # Restore data
   tar -xzf /backup/forexsmartbot/data_YYYYMMDD_HHMMSS.tar.gz -C ~/
   
   # Start service
   sudo systemctl start forexsmartbot
   ```

2. **Database recovery**:
   ```bash
   # Stop service
   sudo systemctl stop forexsmartbot
   
   # Restore database
   cp /backup/forexsmartbot/trades_YYYYMMDD_HHMMSS.db ~/.forexsmartbot/trades.db
   
   # Start service
   sudo systemctl start forexsmartbot
   ```

### Disaster Recovery

1. **Complete system recovery**:
   - Provision new server
   - Install operating system
   - Install dependencies
   - Restore application
   - Restore data
   - Configure services
   - Test functionality

2. **Partial recovery**:
   - Identify affected components
   - Restore specific components
   - Verify functionality
   - Update configurations

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   # Check logs
   sudo journalctl -u forexsmartbot -f
   
   # Check permissions
   ls -la ~/ForexSmartBot
   
   # Check dependencies
   source ~/ForexSmartBot/venv/bin/activate
   pip list
   ```

2. **Memory issues**:
   ```bash
   # Check memory usage
   free -h
   htop
   
   # Check swap
   swapon -s
   ```

3. **Disk space issues**:
   ```bash
   # Check disk usage
   df -h
   du -sh ~/.forexsmartbot
   
   # Clean up logs
   find ~/.forexsmartbot/logs -name "*.log" -mtime +7 -delete
   ```

### Performance Issues

1. **Slow performance**:
   - Check CPU usage
   - Check memory usage
   - Check disk I/O
   - Check network latency

2. **High memory usage**:
   - Check for memory leaks
   - Optimize data processing
   - Use appropriate data types
   - Clear unused variables

3. **Database issues**:
   - Check database size
   - Optimize queries
   - Rebuild indexes
   - Vacuum database

## Support

### Getting Help

1. **Documentation**: Check comprehensive documentation
2. **Logs**: Review application and system logs
3. **Community**: Ask questions in GitHub discussions
4. **Issues**: Report bugs on GitHub issues

### Monitoring Tools

1. **System monitoring**: htop, iotop, nethogs
2. **Application monitoring**: Custom logging and metrics
3. **Database monitoring**: SQLite-specific tools
4. **Network monitoring**: netstat, ss, tcpdump

---

**Note**: This deployment guide provides general instructions. Always adapt the steps to your specific environment and requirements. Test thoroughly in a non-production environment before deploying to production.
