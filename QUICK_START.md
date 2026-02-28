# 🚀 Quick Start Guide - OMR Evaluation System

## ✅ Your Application is Running!

Your OMR Evaluation System is now live and accessible at:

**🌐 http://localhost:5000**

---

## 📋 What's Working

✅ Backend server is running on port 5000  
✅ All Python dependencies installed  
✅ Flask application is healthy  
✅ API endpoints are accessible  

---

## 🎯 How to Use Your Application

### 1. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

### 2. Basic OMR Evaluation (Works Now)

You can immediately use these features:

**Upload OMR Sheets**:
- Upload student answer sheets (images/PDFs)
- Upload answer key (CSV or JSON format)
- Get instant evaluation results

**Features Available**:
- ✅ Automatic OMR sheet evaluation
- ✅ Bubble detection and grading
- ✅ Student database linking
- ✅ Results export (CSV/Excel)
- ✅ Real-time progress tracking
- ✅ Multi-sheet batch processing

### 3. AI Question Solver (Requires Ollama)

For AI-powered answer key generation from question banks:

**Install Ollama** (one-time setup):
```bash
# Download from: https://ollama.com/download
# After installation, run:
ollama serve

# In a new terminal, install models:
ollama pull llama3.2:latest
ollama pull moondream:latest
```

Then you can:
- Upload question bank PDFs
- AI automatically solves questions
- Generate answer keys with confidence scores
- Review and correct AI answers
- Export in multiple formats

---

## 🛠️ Managing Your Application

### Stop the Application

To stop the server:
```bash
# Press Ctrl+C in the terminal where it's running
# Or close the terminal window
```

### Start the Application Again

```bash
# Navigate to project directory
cd "c:\Users\jaag1\Desktop\desktop\siva omr project"

# Activate virtual environment
.venv\Scripts\activate

# Run the application
python backend/app.py
```

### Check if Application is Running

```bash
# Test the health endpoint
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "EvalGenius AI Backend"
}
```

---

## 📁 Project Structure

```
siva omr project/
├── backend/              # Backend Python code
│   ├── app.py           # Main Flask application
│   ├── omr_engine.py    # OMR processing engine
│   ├── ollama_client.py # AI integration
│   └── requirements.txt # Python dependencies
├── frontend/            # Frontend HTML/CSS/JS
├── docs/               # Documentation
│   ├── FREE_DEPLOYMENT_GUIDE.md  # Deployment options
│   ├── user-guide.md             # User manual
│   ├── deployment.md             # Deployment guide
│   └── troubleshooting.md        # Troubleshooting
├── .venv/              # Python virtual environment
└── QUICK_START.md      # This file
```

---

## 🔧 Common Tasks

### Upload Answer Key (CSV Format)

Create a CSV file with this format:
```csv
1,A
2,B
3,C
4,D
5,A
```

Or with headers:
```csv
Question,Answer
1,A
2,B
3,C
```

### Upload Answer Key (JSON Format)

```json
{
  "0": 0,
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 0
}
```
Note: JSON uses 0-based indexing (0=A, 1=B, 2=C, 3=D, 4=E)

### Test with Sample Data

1. Use the provided `100_MCQ_Question_Bank.pdf` for testing
2. Create a sample answer key CSV
3. Upload both and see results

---

## 🌐 Free Deployment Options

Want to deploy your application online? Check out:

**📖 See `docs/FREE_DEPLOYMENT_GUIDE.md` for:**
- Render.com (Free, easy, recommended)
- Railway.app (Free $5 credit, supports Docker)
- PythonAnywhere (Free tier, Python-focused)
- Vercel (Free, for frontend)
- Heroku (Requires credit card)

**Quick Deploy to Render.com:**
1. Push code to GitHub
2. Sign up at render.com
3. Connect your repository
4. Deploy automatically!

---

## 📚 Documentation

- **User Guide**: `docs/user-guide.md` - How to use all features
- **API Documentation**: `docs/api/ai-question-solver-api.md` - API reference
- **Deployment Guide**: `docs/deployment.md` - Production deployment
- **Troubleshooting**: `docs/troubleshooting.md` - Common issues and solutions
- **Free Deployment**: `docs/FREE_DEPLOYMENT_GUIDE.md` - Free hosting options

---

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Port 5000 Already in Use

```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process
taskkill /PID <PID> /F

# Or change port in backend/app.py
```

### Module Not Found Errors

```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### AI Features Not Working

```bash
# Install Ollama from https://ollama.com/download
# Start Ollama service
ollama serve

# Install required models
ollama pull llama3.2:latest
ollama pull moondream:latest

# Test connection
curl http://localhost:11434/api/tags
```

---

## 🎓 Next Steps

1. **Test Basic Features**: Upload some OMR sheets and evaluate them
2. **Set Up AI (Optional)**: Install Ollama for AI question solving
3. **Read Documentation**: Check out the user guide for advanced features
4. **Deploy Online**: Use the free deployment guide to make it accessible online
5. **Customize**: Modify the frontend or add new features

---

## 💡 Tips

- **Keep Terminal Open**: Don't close the terminal where the app is running
- **Use Chrome/Firefox**: For best compatibility
- **Check Logs**: Look at terminal output for errors
- **Save Work**: Export results regularly
- **Backup Data**: Keep copies of important answer keys

---

## 📞 Support

- **Documentation**: Check `docs/` folder
- **Troubleshooting**: See `docs/troubleshooting.md`
- **GitHub Issues**: Report bugs on GitHub
- **Community**: Join user forums for help

---

## 🎉 Success!

Your OMR Evaluation System is ready to use!

**Current Status**: ✅ Running on http://localhost:5000

**What You Can Do Now**:
1. Open http://localhost:5000 in your browser
2. Upload OMR sheets and answer keys
3. Get instant evaluation results
4. Export results to CSV/Excel

**For AI Features**:
1. Install Ollama (see above)
2. Upload question bank PDFs
3. Let AI generate answer keys automatically

---

**Last Updated**: February 28, 2026  
**Version**: 1.0  
**Status**: ✅ Running Successfully
