# 🚀 OMR Evaluation System - Deployment Guide

## 📋 Project Status: READY FOR DEPLOYMENT ✅

Your OMR Evaluation System is fully functional and ready to deploy!

### ✅ What's Working:
- Backend API (Flask) - All endpoints functional
- Frontend (HTML/CSS/JS) - Complete UI
- OMR Sheet Processing - YOLOv8 bubble detection
- Answer Key Upload - CSV format support
- Batch Evaluation - Parallel processing
- Results Export - CSV and Excel formats
- Student Database Linking - Name mapping

---

## 🎯 QUICK DEPLOY (Choose ONE method)

### Method 1: Render.com (RECOMMENDED - FREE)

**One-Click Deploy:**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**Manual Deploy:**

1. Visit: https://dashboard.render.com/register
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect repository: `https://github.com/Jagadeesh-Surendran/omr-evaluation-system`
5. Configure:
   ```
   Name: omr-evaluation-system
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
   ```
6. Click "Create Web Service"
7. Wait 5-10 minutes
8. Your app will be live at: `https://omr-evaluation-system.onrender.com`

**Test your deployment:**
```bash
curl https://your-app.onrender.com/api/health
```

---

### Method 2: Railway.app (FREE)

1. Visit: https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose: `omr-evaluation-system`
5. Railway auto-detects Python
6. Add environment variable: `PORT=8080`
7. Deploy!

Your app: `https://your-app.up.railway.app`

---

### Method 3: Heroku (FREE tier available)

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Login:
   ```bash
   heroku login
   ```
3. Create app:
   ```bash
   heroku create omr-evaluation-system
   ```
4. Deploy:
   ```bash
   git push heroku master
   ```
5. Open:
   ```bash
   heroku open
   ```

---

## 💻 Local Development

### Prerequisites:
- Python 3.10+
- Git

### Setup:

1. **Clone repository:**
   ```bash
   git clone https://github.com/Jagadeesh-Surendran/omr-evaluation-system.git
   cd omr-evaluation-system
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open browser: http://localhost:5000
   - API health check: http://localhost:5000/api/health

### Quick Start (Windows):
```bash
start.bat
```

---

## 📁 Project Structure

```
omr-evaluation-system/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── omr_engine.py         # OMR processing logic
│   ├── best.pt               # YOLOv8 model weights
│   └── ...
├── frontend/
│   ├── index.html            # Main HTML file
│   ├── style.css             # Styles
│   ├── app.js                # Main JavaScript
│   └── js/
│       ├── components/       # UI components
│       ├── utils/            # Utility functions
│       └── api.js            # API integration
├── docs/                     # Documentation
├── Procfile                  # Heroku/Render deployment
├── render.yaml               # Render.com configuration
└── README.md                 # This file
```

---

## 🔧 Configuration

### Environment Variables:

For production deployment, set these variables:

```bash
PORT=10000                    # Server port
PYTHON_VERSION=3.10          # Python version
FLASK_ENV=production         # Flask environment
```

### Frontend API Configuration:

The frontend automatically uses the deployment URL. No changes needed!

File: `frontend/js/api.js`
```javascript
const API_BASE = window.location.origin;  // Auto-detects deployment URL
```

---

## 🧪 Testing

### Run API Tests:
```bash
python test_api.py
```

### Expected Output:
```
✅ PASS - Health Check
✅ PASS - Evaluate Batch Validation
✅ PASS - Extract Key Validation
✅ PASS - Export Validation
✅ PASS - Link DB Validation
```

### Test Endpoints:

1. **Health Check:**
   ```bash
   curl http://localhost:5000/api/health
   ```

2. **Evaluate OMR Sheets:**
   ```bash
   curl -X POST http://localhost:5000/api/evaluate_batch \
     -F "omr_files=@sheet1.jpg" \
     -F "answer_key_json={\"1\":\"A\",\"2\":\"B\"}" \
     -F "num_options=4"
   ```

---

## 📊 API Endpoints

### Core Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/evaluate_batch` | POST | Evaluate multiple OMR sheets |
| `/api/extract_key` | POST | Extract answer key from question paper (AI) |
| `/api/export` | POST | Export results to CSV/Excel |
| `/api/link_db` | POST | Link student names from database |

### Request Examples:

**Evaluate Batch:**
```javascript
const formData = new FormData();
formData.append('omr_files', file1);
formData.append('omr_files', file2);
formData.append('answer_key_json', JSON.stringify({"1":"A","2":"B"}));
formData.append('num_options', '4');

fetch('/api/evaluate_batch', {
  method: 'POST',
  body: formData
});
```

---

## 🎓 For Final Year Project Demo

### What to Demonstrate:

1. **Live Deployment**
   - Show the deployed URL
   - Demonstrate responsive design

2. **Core Features**
   - Upload OMR sheets (single/batch)
   - Upload answer key CSV
   - Automatic bubble detection
   - Real-time evaluation
   - Results display with statistics
   - Export to CSV/Excel
   - Student database linking

3. **Technical Highlights**
   - YOLOv8 for bubble detection
   - Flask REST API
   - Parallel processing for batch evaluation
   - Responsive frontend design
   - GitHub version control

4. **Code Quality**
   - Well-documented code
   - Modular architecture
   - Error handling
   - API testing

### Demo Data:

Sample files are in the repository:
- `sample_omr_sheets/` - Example OMR sheets
- `sample_answer_key.csv` - Example answer key
- `sample_student_db.csv` - Example student database

---

## 🐛 Troubleshooting

### Common Issues:

**1. "Module not found" error**
```bash
pip install -r backend/requirements.txt
```

**2. "Port already in use"**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**3. "Model file not found"**
- Ensure `backend/best.pt` exists
- Download from: [model link if available]

**4. Deployment fails on Render/Railway**
- Check logs in dashboard
- Verify `requirements.txt` is complete
- Ensure `gunicorn` is installed

---

## 📞 Support

### Resources:
- **Documentation:** See `docs/` folder
- **API Docs:** `docs/api/ai-question-solver-api.md`
- **User Guide:** `docs/user-guide.md`
- **Troubleshooting:** `docs/troubleshooting.md`

### GitHub:
- Repository: https://github.com/Jagadeesh-Surendran/omr-evaluation-system
- Issues: Report bugs on GitHub Issues
- Wiki: Check for updates

---

## 📝 License

This project is for educational purposes (Final Year Project).

---

## 🎉 Success Checklist

Before your demo:

- [ ] Backend deployed and accessible
- [ ] Frontend loads correctly
- [ ] Health endpoint responds: `/api/health`
- [ ] Can upload OMR sheets
- [ ] Can upload answer key
- [ ] Evaluation works
- [ ] Results display correctly
- [ ] Export to CSV works
- [ ] GitHub repository is public
- [ ] README is updated
- [ ] Demo data is prepared

---

## 🚀 Deploy NOW!

**Fastest method:** Render.com (5 minutes)

1. Go to: https://dashboard.render.com/register
2. Connect GitHub
3. Deploy `omr-evaluation-system`
4. Done!

**Your project will be live at:**
`https://omr-evaluation-system.onrender.com`

---

**Good luck with your final year project! 🎓✨**

