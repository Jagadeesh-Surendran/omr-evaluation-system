# AI Question Solver Deployment Guide

## Overview

This guide covers deploying the AI Question Solver feature for the OMR Evaluation System. It includes Ollama service setup, model installation, dependency management, configuration, and scaling considerations.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Ollama Service Setup](#ollama-service-setup)
4. [Model Installation](#model-installation)
5. [Backend Dependencies](#backend-dependencies)
6. [Configuration](#configuration)
7. [Database Setup](#database-setup)
8. [Running the Application](#running-the-application)
9. [Production Deployment](#production-deployment)
10. [Scaling Considerations](#scaling-considerations)
11. [Monitoring and Maintenance](#monitoring-and-maintenance)
12. [Security Considerations](#security-considerations)

---

## System Requirements

### Minimum Requirements

**Hardware**:
- CPU: 4 cores (8 recommended)
- RAM: 16 GB (32 GB recommended)
- Storage: 50 GB free space (100 GB recommended)
- GPU: Optional but recommended for faster processing

**Software**:
- Operating System: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- Python: 3.8 or higher
- Node.js: 14.x or higher (for frontend)
- Docker: 20.10+ (optional, for containerized deployment)

### Recommended Requirements

**Hardware**:
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 100 GB SSD
- GPU: NVIDIA GPU with 8+ GB VRAM (for faster AI processing)

**Software**:
- Operating System: Ubuntu 22.04 LTS
- Python: 3.10+
- Node.js: 18.x LTS
- Docker: Latest stable version

---

## Prerequisites

### Install Python

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS**:
```bash
brew install python@3.10
```

**Windows**:
Download and install from [python.org](https://www.python.org/downloads/)

### Install Node.js (for frontend)

**Ubuntu/Debian**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS**:
```bash
brew install node@18
```

**Windows**:
Download and install from [nodejs.org](https://nodejs.org/)

---

## Ollama Service Setup

Ollama is the AI model service that powers question solving. It must be installed and running before using the AI Question Solver.

### Install Ollama

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS**:
```bash
brew install ollama
```

**Windows**:
Download and install from [ollama.com](https://ollama.com/download)

### Start Ollama Service

**Linux/macOS**:
```bash
# Start as a service
ollama serve
```

**Windows**:
Ollama runs automatically as a service after installation.

### Verify Ollama Installation

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Expected output: JSON list of installed models
```

### Configure Ollama

**Environment Variables** (optional):
```bash
# Set custom host/port
export OLLAMA_HOST=0.0.0.0:11434

# Set model storage location
export OLLAMA_MODELS=/path/to/models

# Enable GPU acceleration (if available)
export OLLAMA_GPU=1
```

**Systemd Service** (Linux):
```bash
# Create systemd service file
sudo nano /etc/systemd/system/ollama.service
```


Add the following content:
```ini
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=ollama
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/var/lib/ollama/models"

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

---

## Model Installation

The AI Question Solver uses different models for different question types.

### Required Models

**1. llama3.2 (General and Math Questions)**:
```bash
ollama pull llama3.2:latest
```

**2. moondream (Visual Questions with Images)**:
```bash
ollama pull moondream:latest
```

### Verify Model Installation

```bash
# List installed models
ollama list

# Expected output:
# NAME              ID              SIZE      MODIFIED
# llama3.2:latest   abc123def456    4.7 GB    2 hours ago
# moondream:latest  def456ghi789    1.7 GB    2 hours ago
```

### Test Models

**Test llama3.2**:
```bash
ollama run llama3.2 "What is 2 + 2?"
```

**Test moondream**:
```bash
ollama run moondream "Describe this image" --image /path/to/test/image.jpg
```

### Optional Models

For specialized question types, you can install additional models:

**Mathematics (Advanced)**:
```bash
ollama pull deepseek-math:latest
```

**Code/Programming Questions**:
```bash
ollama pull codellama:latest
```

### Model Storage

Models are stored in:
- **Linux**: `/usr/share/ollama/.ollama/models`
- **macOS**: `~/.ollama/models`
- **Windows**: `C:\Users\<username>\.ollama\models`

**Disk Space**: Each model requires 1-7 GB of storage.

---

## Backend Dependencies

### Clone Repository

```bash
git clone <repository-url>
cd omr-evaluation-system
```

### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### Install Python Dependencies

```bash
# Install from requirements.txt
pip install -r backend/requirements.txt
```

### Key Dependencies

The following packages are required for AI Question Solver:

```txt
# Core dependencies
Flask==2.3.0
Flask-SocketIO==5.3.0
PyMuPDF==1.23.0
Pillow==10.0.0

# AI and testing
hypothesis==6.92.0
requests==2.31.0

# Existing dependencies
opencv-python==4.8.0
numpy==1.24.0
```

### Verify Installation

```bash
# Test imports
python -c "import fitz; import hypothesis; print('Dependencies OK')"
```

---

## Configuration

### Application Configuration

Create or update `backend/config.py`:

```python
import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Ollama configuration
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', 30))
    
    # AI Solver configuration
    SOLVER_MAX_CONCURRENT_SESSIONS = int(os.environ.get('SOLVER_MAX_CONCURRENT_SESSIONS', 2))
    SOLVER_QUESTION_TIMEOUT = int(os.environ.get('SOLVER_QUESTION_TIMEOUT', 30))
    SOLVER_MAX_RETRIES = int(os.environ.get('SOLVER_MAX_RETRIES', 2))
    SOLVER_MIN_CONFIDENCE = float(os.environ.get('SOLVER_MIN_CONFIDENCE', 0.6))
    
    # Model configuration
    MODEL_MATH = os.environ.get('MODEL_MATH', 'llama3.2:latest')
    MODEL_VISUAL = os.environ.get('MODEL_VISUAL', 'moondream:latest')
    MODEL_GENERAL = os.environ.get('MODEL_GENERAL', 'llama3.2:latest')
    MODEL_DEFAULT = os.environ.get('MODEL_DEFAULT', 'llama3.2:latest')
    
    # Storage configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'backend/uploads')
    SESSION_FOLDER = os.environ.get('SESSION_FOLDER', 'backend/solver_sessions')
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 50 * 1024 * 1024))  # 50 MB
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'backend/logs/solver_main.log')
    
    # WebSocket configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Override with secure values
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production

class TestingConfig(Config):
    TESTING = True
    SOLVER_MAX_CONCURRENT_SESSIONS = 1
```

### Environment Variables

Create `.env` file in the project root:

```bash
# Flask
FLASK_APP=backend/app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=30

# AI Solver
SOLVER_MAX_CONCURRENT_SESSIONS=2
SOLVER_QUESTION_TIMEOUT=30
SOLVER_MAX_RETRIES=2
SOLVER_MIN_CONFIDENCE=0.6

# Models
MODEL_MATH=llama3.2:latest
MODEL_VISUAL=moondream:latest
MODEL_GENERAL=llama3.2:latest
MODEL_DEFAULT=llama3.2:latest

# Storage
UPLOAD_FOLDER=backend/uploads
SESSION_FOLDER=backend/solver_sessions
MAX_UPLOAD_SIZE=52428800

# Logging
LOG_LEVEL=INFO
LOG_FILE=backend/logs/solver_main.log

# CORS (for frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### Create Required Directories

```bash
# Create directories
mkdir -p backend/uploads
mkdir -p backend/solver_sessions
mkdir -p backend/logs
mkdir -p backend/tests/fixtures/pdfs

# Set permissions (Linux/macOS)
chmod 755 backend/uploads
chmod 755 backend/solver_sessions
chmod 755 backend/logs
```

---

## Database Setup

The AI Question Solver uses file-based storage for session data. No database setup is required, but ensure proper file permissions.

### Session Storage Structure

```
backend/solver_sessions/
  {session_id}/
    session.json
    questions.json
    results.json
    validation.json
    answer_key.json
    answer_key.csv
    answer_key_report.pdf
    logs/
      extraction.log
      solving.log
      validation.log
      errors.log
```

### Backup Strategy

```bash
# Create backup script
nano backup_sessions.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/backups/solver_sessions"
SOURCE_DIR="backend/solver_sessions"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/sessions_$DATE.tar.gz $SOURCE_DIR

# Keep only last 30 days of backups
find $BACKUP_DIR -name "sessions_*.tar.gz" -mtime +30 -delete
```

Make executable and schedule:
```bash
chmod +x backup_sessions.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/backup_sessions.sh
```

---

## Running the Application

### Development Mode

**Start Backend**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run Flask development server
python backend/app.py
```

The backend will start on `http://localhost:5000`

**Start Frontend** (if separate):
```bash
cd frontend
npm install
npm start
```

The frontend will start on `http://localhost:3000`

### Production Mode

**Using Gunicorn** (recommended for production):

```bash
# Install Gunicorn
pip install gunicorn gevent-websocket

# Run with Gunicorn
gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
         --workers 4 \
         --bind 0.0.0.0:5000 \
         --timeout 120 \
         --access-logfile backend/logs/access.log \
         --error-logfile backend/logs/error.log \
         backend.app:app
```

**Using systemd** (Linux):

Create `/etc/systemd/system/omr-solver.service`:
```ini
[Unit]
Description=OMR AI Question Solver
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/omr-evaluation-system
Environment="PATH=/var/www/omr-evaluation-system/.venv/bin"
ExecStart=/var/www/omr-evaluation-system/.venv/bin/gunicorn \
          --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
          --workers 4 \
          --bind 0.0.0.0:5000 \
          --timeout 120 \
          backend.app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable omr-solver
sudo systemctl start omr-solver
sudo systemctl status omr-solver
```

---

## Production Deployment

### Using Docker

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/

# Create directories
RUN mkdir -p backend/uploads backend/solver_sessions backend/logs

# Expose ports
EXPOSE 5000 11434

# Start script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
```

**docker-entrypoint.sh**:
```bash
#!/bin/bash
set -e

# Start Ollama in background
ollama serve &

# Wait for Ollama to be ready
sleep 5

# Pull required models
ollama pull llama3.2:latest
ollama pull moondream:latest

# Start application
exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
     --workers 4 \
     --bind 0.0.0.0:5000 \
     --timeout 120 \
     backend.app:app
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  omr-solver:
    build: .
    ports:
      - "5000:5000"
      - "11434:11434"
    volumes:
      - ./backend/uploads:/app/backend/uploads
      - ./backend/solver_sessions:/app/backend/solver_sessions
      - ./backend/logs:/app/backend/logs
      - ollama-models:/root/.ollama
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - OLLAMA_HOST=http://localhost:11434
      - SOLVER_MAX_CONCURRENT_SESSIONS=2
    restart: unless-stopped

volumes:
  ollama-models:
```

**Build and run**:
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Nginx Reverse Proxy

**Install Nginx**:
```bash
sudo apt install nginx
```

**Configure Nginx** (`/etc/nginx/sites-available/omr-solver`):
```nginx
upstream omr_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    # Frontend
    location / {
        root /var/www/omr-evaluation-system/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://omr_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket
    location /api/solve/progress {
        proxy_pass http://omr_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/omr-solver /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS Configuration

**Using Let's Encrypt**:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## Scaling Considerations

### Resource Requirements per Session

**Single Session**:
- CPU: 1-2 cores
- RAM: 4-8 GB (depending on model)
- Processing: 2 questions/minute (text), 1 question/minute (images)

**Two Concurrent Sessions** (default limit):
- CPU: 4 cores minimum
- RAM: 16 GB minimum
- Storage: 10 GB for models + session data

### Horizontal Scaling

For high-volume deployments:

**Load Balancer Configuration**:
- Use sticky sessions for WebSocket connections
- Distribute sessions across multiple backend instances
- Share session storage via NFS or S3

**Example with Multiple Backends**:
```nginx
upstream omr_backend {
    ip_hash;  # Sticky sessions
    server backend1:5000;
    server backend2:5000;
    server backend3:5000;
}
```

**Shared Storage**:
```yaml
# docker-compose.yml
services:
  omr-solver-1:
    # ... config ...
    volumes:
      - nfs-sessions:/app/backend/solver_sessions
  
  omr-solver-2:
    # ... config ...
    volumes:
      - nfs-sessions:/app/backend/solver_sessions

volumes:
  nfs-sessions:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server,rw
      device: ":/path/to/sessions"
```

### Vertical Scaling

**Increase Concurrent Sessions**:
```bash
# In .env or config
SOLVER_MAX_CONCURRENT_SESSIONS=4  # Requires more CPU/RAM
```

**GPU Acceleration**:
- Install NVIDIA drivers and CUDA
- Configure Ollama to use GPU
- Expect 3-5x faster processing

**Optimize Model Selection**:
- Use smaller models for simple questions
- Use larger models only for complex questions
- Implement model caching

---

## Monitoring and Maintenance

### Health Checks

**Ollama Health**:
```bash
curl http://localhost:11434/api/tags
```

**Application Health**:
```bash
curl http://localhost:5000/api/health
```

**Implement Health Endpoint** (`backend/app.py`):
```python
@app.route('/api/health')
def health_check():
    # Check Ollama
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=5)
        ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        ollama_status = "unhealthy"
    
    # Check disk space
    import shutil
    disk = shutil.disk_usage("/")
    disk_free_gb = disk.free / (1024**3)
    
    return jsonify({
        "status": "healthy" if ollama_status == "healthy" else "degraded",
        "ollama": ollama_status,
        "disk_free_gb": round(disk_free_gb, 2),
        "active_sessions": len(session_manager.active_sessions)
    })
```

### Log Monitoring

**View Logs**:
```bash
# Application logs
tail -f backend/logs/solver_main.log

# Ollama logs (systemd)
sudo journalctl -u ollama -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

**Log Rotation** (`/etc/logrotate.d/omr-solver`):
```
/var/www/omr-evaluation-system/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload omr-solver > /dev/null 2>&1 || true
    endscript
}
```

### Performance Monitoring

**Install monitoring tools**:
```bash
# System monitoring
sudo apt install htop iotop

# Python profiling
pip install py-spy memory_profiler
```

**Monitor Resource Usage**:
```bash
# CPU and memory
htop

# Disk I/O
iotop

# GPU usage (if applicable)
nvidia-smi -l 1
```

### Maintenance Tasks

**Weekly**:
- Review error logs
- Check disk space
- Verify backup completion
- Review session statistics

**Monthly**:
- Update Ollama models
- Update Python dependencies
- Review and archive old sessions
- Performance optimization review

**Quarterly**:
- Security audit
- Capacity planning review
- Update documentation

---

## Security Considerations

### Authentication

- Implement strong authentication (OAuth2, JWT)
- Use HTTPS in production
- Rotate secrets regularly

### Authorization

- Restrict approval endpoint to administrators
- Implement role-based access control
- Log all privileged operations

### File Upload Security

```python
# Validate file types
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Sanitize filenames
from werkzeug.utils import secure_filename
filename = secure_filename(file.filename)
```

### Network Security

- Use firewall to restrict Ollama access
- Enable CORS only for trusted origins
- Use rate limiting to prevent abuse

**Firewall Rules** (UFW):
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block external Ollama access
sudo ufw deny 11434/tcp

# Enable firewall
sudo ufw enable
```

### Data Privacy

- Encrypt sensitive data at rest
- Implement data retention policies
- Provide data export/deletion for users
- Comply with GDPR/privacy regulations

---

## Troubleshooting Deployment

**Issue: Ollama not starting**
```bash
# Check logs
sudo journalctl -u ollama -n 50

# Verify installation
which ollama
ollama --version

# Reinstall if needed
curl -fsSL https://ollama.com/install.sh | sh
```

**Issue: Models not downloading**
```bash
# Check disk space
df -h

# Check network
curl -I https://ollama.com

# Manual download
ollama pull llama3.2:latest --verbose
```

**Issue: Application won't start**
```bash
# Check Python version
python --version

# Verify dependencies
pip list

# Check configuration
python -c "from backend.config import Config; print(Config.OLLAMA_HOST)"

# Check ports
sudo netstat -tulpn | grep 5000
```

**Issue: WebSocket not connecting**
```bash
# Check Nginx WebSocket config
sudo nginx -t

# Test WebSocket
wscat -c ws://localhost:5000/api/solve/progress

# Check firewall
sudo ufw status
```

---

**Last Updated**: January 2024  
**Version**: 1.0
