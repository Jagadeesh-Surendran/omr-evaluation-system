# Free Deployment Options for OMR Evaluation System

## Overview

This guide provides step-by-step instructions for deploying your OMR Evaluation System using **completely free** hosting platforms. We'll cover multiple options suitable for different needs.

## Quick Start - Run Locally (Recommended for Testing)

### Prerequisites
- Python 3.8+ installed
- Git installed

### Steps

1. **Install Ollama** (for AI features):
```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

2. **Start Ollama and Install Models**:
```bash
# Start Ollama service
ollama serve

# In a new terminal, install required models
ollama pull llama3.2:latest
ollama pull moondream:latest
```

3. **Set Up Python Environment**:
```bash
# Navigate to your project
cd "c:\Users\jaag1\Desktop\desktop\siva omr project"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

4. **Run the Application**:
```bash
# Start the backend
python backend/app.py
```

5. **Access the Application**:
- Open browser: `http://localhost:5000`
- The application is now running locally!

---

## Free Deployment Options

### Option 1: Render.com (Recommended - Easy & Free)

**Pros**: Free tier, easy setup, automatic deployments, supports Python
**Cons**: AI features limited (Ollama requires significant resources)
**Best For**: Basic OMR evaluation without AI question solver

#### Steps:

1. **Create Account**:
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Prepare Your Repository**:
```bash
# Create render.yaml in project root
```

Create `render.yaml`:
```yaml
services:
  - type: web
    name: omr-evaluation
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 2 --bind 0.0.0.0:$PORT --chdir backend app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: FLASK_ENV
        value: production
```

3. **Deploy**:
   - Push code to GitHub
   - In Render dashboard, click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` and deploy

4. **Access Your App**:
   - Render provides a free URL: `https://your-app.onrender.com`

**Note**: Free tier sleeps after 15 minutes of inactivity. First request may be slow.

---

### Option 2: Railway.app (Good for Full Features)

**Pros**: Free $5/month credit, supports Docker, can run Ollama
**Cons**: Credit-based (may run out), requires Docker knowledge
**Best For**: Full application with AI features

#### Steps:

1. **Create Account**:
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create Dockerfile**:

Create `Dockerfile` in project root:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent-websocket

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create directories
RUN mkdir -p backend/uploads backend/solver_sessions backend/logs

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--workers", "2", "--bind", "0.0.0.0:5000", "--chdir", "backend", "app:app"]
```

3. **Deploy**:
   - Push to GitHub
   - In Railway, click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will build and deploy automatically

4. **Configure Environment**:
   - In Railway dashboard, add environment variables:
     - `PORT=5000`
     - `FLASK_ENV=production`

**Note**: Without Ollama, AI features won't work. For AI features, you'd need to run Ollama separately (not feasible on free tier).

---

### Option 3: PythonAnywhere (Simple & Reliable)

**Pros**: Free tier, Python-focused, easy setup, persistent storage
**Cons**: Limited resources, no WebSocket support on free tier
**Best For**: Basic OMR evaluation, learning/testing

#### Steps:

1. **Create Account**:
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Sign up for free account

2. **Upload Code**:
```bash
# In PythonAnywhere console
git clone <your-repo-url>
cd omr-evaluation-system
```

3. **Set Up Virtual Environment**:
```bash
mkvirtualenv --python=/usr/bin/python3.10 omr-env
pip install -r backend/requirements.txt
```

4. **Configure Web App**:
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration" → Python 3.10
   - Set source code: `/home/yourusername/omr-evaluation-system/backend`
   - Set WSGI file to point to your Flask app

Edit WSGI file:
```python
import sys
path = '/home/yourusername/omr-evaluation-system'
if path not in sys.path:
    sys.path.append(path)

from backend.app import app as application
```

5. **Reload and Access**:
   - Click "Reload"
   - Access at: `https://yourusername.pythonanywhere.com`

**Limitations**: No AI features (Ollama not supported), no WebSocket (real-time updates won't work).

---

### Option 4: Heroku (Classic Choice)

**Pros**: Well-documented, easy deployment, add-ons available
**Cons**: Free tier discontinued (now requires credit card), limited free hours
**Best For**: If you have a credit card for verification

#### Steps:

1. **Install Heroku CLI**:
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

2. **Create Heroku App**:
```bash
heroku login
heroku create omr-evaluation-app
```

3. **Create Procfile**:
```
web: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 2 --bind 0.0.0.0:$PORT --chdir backend app:app
```

4. **Deploy**:
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

5. **Open App**:
```bash
heroku open
```

**Note**: Heroku no longer offers a completely free tier.

---

### Option 5: Vercel (Frontend Only)

**Pros**: Excellent for static sites, free, fast CDN
**Cons**: Backend requires serverless functions (complex for this app)
**Best For**: Deploying frontend only, backend elsewhere

#### Steps:

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Deploy Frontend**:
```bash
cd frontend
vercel
```

3. **Configure API**:
   - Set backend URL in frontend config
   - Backend must be deployed separately

---

## Recommended Free Setup

### For Testing/Development:
**Run Locally** (Option 0)
- Full features including AI
- No deployment complexity
- Free and unlimited

### For Production (Basic Features):
**Render.com** (Option 1)
- Free and reliable
- Automatic deployments
- Good for basic OMR evaluation
- No AI features

### For Production (Full Features):
**Railway.app** (Option 2) + **Local Ollama**
- Deploy main app on Railway
- Run Ollama on your own server/computer
- Configure app to connect to remote Ollama
- Use $5 free credit wisely

---

## Running Your Application Now

Let's get your application running locally right now:

### Step 1: Check Python Installation
```bash
python --version
# Should show Python 3.8 or higher
```

### Step 2: Install Ollama (for AI features)
```bash
# Windows: Download from https://ollama.com/download
# After installation, open a new terminal and run:
ollama serve
```

### Step 3: Install Models (in a new terminal)
```bash
ollama pull llama3.2:latest
ollama pull moondream:latest
```

### Step 4: Set Up Python Environment
```bash
# Navigate to your project
cd "c:\Users\jaag1\Desktop\desktop\siva omr project"

# Create virtual environment (if not exists)
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 5: Run the Application
```bash
# Make sure you're in the project root
python backend/app.py
```

### Step 6: Access the Application
Open your browser and go to:
```
http://localhost:5000
```

You should see your OMR Evaluation System running!

---

## Troubleshooting Local Setup

### Issue: "Python not found"
**Solution**:
```bash
# Install Python from python.org
# Or use Microsoft Store (Windows)
```

### Issue: "pip not found"
**Solution**:
```bash
python -m ensurepip --upgrade
```

### Issue: "Module not found"
**Solution**:
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue: "Port 5000 already in use"
**Solution**:
```bash
# Find and kill process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in backend/app.py:
# app.run(port=5001)
```

### Issue: "Ollama not connecting"
**Solution**:
```bash
# Make sure Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Check if models are installed
ollama list
```

---

## Next Steps

1. **Test Locally First**: Always test your application locally before deploying
2. **Choose Deployment Platform**: Based on your needs (AI features vs basic)
3. **Set Up CI/CD**: Automate deployments with GitHub Actions
4. **Monitor Performance**: Use platform monitoring tools
5. **Scale as Needed**: Upgrade to paid tiers when you outgrow free tiers

---

## Cost Comparison

| Platform | Free Tier | AI Support | Best For |
|----------|-----------|------------|----------|
| Local | Unlimited | ✅ Yes | Development, Testing |
| Render | 750 hours/month | ❌ No | Basic OMR |
| Railway | $5 credit/month | ⚠️ Limited | Full features (short term) |
| PythonAnywhere | Always free | ❌ No | Learning, Simple apps |
| Heroku | Requires card | ⚠️ Limited | Production (paid) |
| Vercel | Unlimited | ❌ No | Frontend only |

---

## Support

For deployment help:
- Check `/docs/deployment.md` for detailed deployment guide
- Check `/docs/troubleshooting.md` for common issues
- Open GitHub issue for specific problems

---

**Last Updated**: January 2024  
**Version**: 1.0
