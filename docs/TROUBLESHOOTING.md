# AI Question Solver Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with the AI Question Solver feature. It covers service issues, processing errors, performance problems, and provides debugging steps.

## Table of Contents

1. [Service Issues](#service-issues)
2. [Upload and Classification Issues](#upload-and-classification-issues)
3. [Question Extraction Issues](#question-extraction-issues)
4. [AI Solving Issues](#ai-solving-issues)
5. [Session Management Issues](#session-management-issues)
6. [Performance Issues](#performance-issues)
7. [Export Issues](#export-issues)
8. [WebSocket Issues](#websocket-issues)
9. [Authentication Issues](#authentication-issues)
10. [Log File Locations](#log-file-locations)
11. [Debugging Steps](#debugging-steps)
12. [Performance Tuning](#performance-tuning)

---

## Service Issues

### Issue: Ollama Service Not Available

**Symptoms**:
- Error message: "Ollama service is not available"
- Cannot start solver sessions
- Upload fails immediately

**Diagnosis**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check Ollama process
ps aux | grep ollama

# Check Ollama logs (Linux)
sudo journalctl -u ollama -n 50
```

**Solutions**:

1. **Start Ollama Service**:
```bash
# Linux/macOS
ollama serve

# Windows (should start automatically)
# Check Services app for "Ollama" service
```

2. **Verify Ollama Installation**:
```bash
# Check version
ollama --version

# Reinstall if needed
curl -fsSL https://ollama.com/install.sh | sh
```

3. **Check Port Availability**:
```bash
# Check if port 11434 is in use
netstat -tulpn | grep 11434

# If blocked, change port in config
export OLLAMA_HOST=0.0.0.0:11435
```

4. **Check Firewall**:
```bash
# Allow Ollama port
sudo ufw allow 11434/tcp
```

---

### Issue: Models Not Available

**Symptoms**:
- Error: "Model not found"
- Fallback to default model warnings
- Slow processing with wrong model

**Diagnosis**:
```bash
# List installed models
ollama list

# Check model storage
ls -lh ~/.ollama/models  # macOS/Linux
dir %USERPROFILE%\.ollama\models  # Windows
```

**Solutions**:

1. **Install Required Models**:
```bash
# Install llama3.2 (general/math)
ollama pull llama3.2:latest

# Install moondream (visual)
ollama pull moondream:latest

# Verify installation
ollama list
```

2. **Test Models**:
```bash
# Test llama3.2
ollama run llama3.2 "What is 2+2?"

# Test moondream with image
ollama run moondream "Describe this" --image test.jpg
```

3. **Check Disk Space**:
```bash
# Check available space
df -h  # Linux/macOS
```

---

## Upload and Classification Issues

### Issue: PDF Upload Fails

**Symptoms**:
- Upload button doesn't work
- Error: "Invalid PDF file"
- Upload progress stuck at 0%

**Diagnosis**:
```bash
# Check file size
ls -lh your-file.pdf

# Check file type
file your-file.pdf

# Try opening in PDF reader
```

**Solutions**:

1. **Check File Size**:
   - Maximum: 50 MB
   - Compress large PDFs using online tools or:
```bash
# Using Ghostscript
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=compressed.pdf input.pdf
```

2. **Remove Password Protection**:
```bash
# Using qpdf
qpdf --password=PASSWORD --decrypt input.pdf output.pdf
```

3. **Check PDF Validity**:
   - Try opening in Adobe Reader or browser
   - Re-save the PDF
   - Convert to PDF/A format

4. **Check Upload Folder Permissions**:
```bash
# Ensure upload directory is writable
chmod 755 backend/uploads
chown www-data:www-data backend/uploads  # Linux
```

---

### Issue: Low Classification Confidence

**Symptoms**:
- System asks to manually select document type
- Confidence score < 0.7
- Incorrect document type detected

**Diagnosis**:
- Review first 3 pages of PDF
- Check for clear question numbers and options
- Look for answer indicators (filled bubbles, answer lists)

**Solutions**:

1. **Manually Select Type**:
   - Choose "Question Bank" if PDF has questions without answers
   - Choose "Answer Key" if PDF has answers marked

2. **Improve PDF Quality**:
   - Ensure questions are clearly numbered (1, 2, 3...)
   - Verify options are labeled (A, B, C, D, E)
   - Remove any answer markings from question bank

3. **Check PDF Structure**:
   - First 3 pages should be representative
   - Avoid cover pages or instructions in first 3 pages

---

## Question Extraction Issues

### Issue: Incomplete Question Extraction

**Symptoms**:
- Fewer questions extracted than expected
- Some questions missing
- Error: "Failed to extract questions"

**Diagnosis**:
```bash
# Check extraction logs
tail -f backend/solver_sessions/{session_id}/logs/extraction.log

# Check for page conversion errors
grep "ERROR" backend/solver_sessions/{session_id}/logs/extraction.log
```

**Solutions**:

1. **Check PDF Quality**:
   - Minimum 300 DPI for scanned PDFs
   - Clear, readable text
   - No handwritten questions

2. **Verify Question Format**:
   - Questions must be numbered
   - Options must be labeled A-E
   - Consistent formatting throughout

3. **Check for Multi-Page Questions**:
   - System should combine them automatically
   - Verify in question list

4. **Review Error Log**:
```bash
# View specific page errors
grep "page" backend/solver_sessions/{session_id}/logs/extraction.log
```

---

### Issue: Mathematical Notation Corrupted

**Symptoms**:
- Math symbols appear as boxes or gibberish
- Equations not readable
- Special characters missing

**Diagnosis**:
- Check if PDF uses embedded fonts
- Verify Unicode support

**Solutions**:

1. **Use Digital PDFs**:
   - Prefer digitally created PDFs over scanned
   - Use LaTeX or MathType for equations

2. **Check Font Embedding**:
```bash
# Check PDF fonts
pdffonts your-file.pdf
```

3. **Convert to Images**:
   - For scanned PDFs, ensure high resolution
   - Use OCR-friendly fonts

---

## AI Solving Issues

### Issue: Many Low Confidence Answers

**Symptoms**:
- Most answers have confidence < 0.6
- Many questions flagged for review
- Average confidence very low

**Diagnosis**:
```bash
# Check solving logs
tail -f backend/solver_sessions/{session_id}/logs/solving.log

# Check model being used
grep "model" backend/solver_sessions/{session_id}/logs/solving.log
```

**Solutions**:

1. **Review Question Quality**:
   - Are questions clearly worded?
   - Are options distinct and unambiguous?
   - Is required knowledge within AI's scope?

2. **Check Model Selection**:
   - Verify correct model for question type
   - Math questions should use math-optimized model
   - Visual questions should use vision model

3. **Improve Question Clarity**:
   - Rephrase ambiguous questions
   - Ensure all necessary information is provided
   - Remove trick questions or overly complex wording

4. **Manual Review**:
   - Review and correct low-confidence answers
   - Add notes for future reference

---

### Issue: AI Selects Wrong Answers

**Symptoms**:
- Obviously incorrect answers selected
- Explanation doesn't match answer
- Consistent errors on certain topics

**Diagnosis**:
- Review AI explanations
- Check question type detection
- Verify answer options are correct

**Solutions**:

1. **Manually Correct**:
   - Use the correction interface
   - Document why AI was wrong

2. **Check Question Type**:
   - Verify question is categorized correctly
   - Math questions should be detected as "math"

3. **Report Patterns**:
   - Note common failure patterns
   - Report to system administrator

4. **Verify Options**:
   - Ensure all options are extracted correctly
   - Check for missing or corrupted options

---

### Issue: Timeouts on Questions

**Symptoms**:
- Questions marked as "timeout"
- Processing takes > 30 seconds per question
- Session progress very slow

**Diagnosis**:
```bash
# Check processing times
grep "timeout" backend/solver_sessions/{session_id}/logs/solving.log

# Check system resources
htop  # or top
```

**Solutions**:

1. **Check System Resources**:
```bash
# CPU usage
top

# Memory usage
free -h

# Disk I/O
iotop
```

2. **Reduce Concurrent Sessions**:
   - Limit to 1 session if resources constrained
   - Wait for current session to complete

3. **Optimize Model**:
   - Use smaller models for simple questions
   - Enable GPU acceleration if available

4. **Increase Timeout** (if appropriate):
```python
# In config.py
SOLVER_QUESTION_TIMEOUT = 60  # Increase to 60 seconds
```

---

## Session Management Issues

### Issue: Session Stuck or Frozen

**Symptoms**:
- Progress not updating
- Session status shows "processing" but no activity
- Cannot pause or cancel

**Diagnosis**:
```bash
# Check session status
curl http://localhost:5000/api/solve/session/{session_id}

# Check backend logs
tail -f backend/logs/solver_main.log

# Check for hung processes
ps aux | grep python
```

**Solutions**:

1. **Refresh Browser**:
   - Reload the page
   - Check session status again

2. **Check Session State**:
```bash
# View session file
cat backend/solver_sessions/{session_id}/session.json
```

3. **Resume from Checkpoint**:
   - Sessions save every 10 questions
   - Use resume functionality

4. **Restart Backend** (last resort):
```bash
# Stop backend
pkill -f "python.*app.py"

# Start backend
python backend/app.py
```

---

### Issue: Cannot Pause Session

**Symptoms**:
- Pause button doesn't work
- Error: "Cannot pause session"
- Session continues processing

**Diagnosis**:
- Check session status
- Verify session is in "processing" state

**Solutions**:

1. **Wait for Current Question**:
   - Pause waits for current question to complete
   - May take up to 30 seconds

2. **Check Session Lock**:
```bash
# Check for lock files
ls backend/solver_sessions/{session_id}/*.lock
```

3. **Force Stop** (if needed):
   - Use cancel instead of pause
   - Note: This discards partial results

---

## Performance Issues

### Issue: Very Slow Processing

**Symptoms**:
- < 1 question per minute
- High CPU/memory usage
- System becomes unresponsive

**Diagnosis**:
```bash
# Monitor resources
htop

# Check I/O wait
iostat -x 1

# Check network (if Ollama is remote)
ping ollama-host
```

**Solutions**:

1. **Optimize System Resources**:
```bash
# Close unnecessary applications
# Increase swap space if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. **Use GPU Acceleration**:
```bash
# Install NVIDIA drivers
# Configure Ollama to use GPU
export OLLAMA_GPU=1
```

3. **Reduce Concurrent Sessions**:
```python
# In config.py
SOLVER_MAX_CONCURRENT_SESSIONS = 1
```

4. **Use Smaller Models**:
```bash
# Use quantized models
ollama pull llama3.2:7b-q4_0
```

---

## Export Issues

### Issue: Export Fails

**Symptoms**:
- Download doesn't start
- Error: "Export failed"
- Corrupted export files

**Diagnosis**:
```bash
# Check session completion
curl http://localhost:5000/api/solve/session/{session_id}

# Check export directory
ls -lh backend/solver_sessions/{session_id}/
```

**Solutions**:

1. **Ensure Session Complete**:
   - Session must be in "completed" status
   - All questions must be processed

2. **Check Disk Space**:
```bash
df -h
```

3. **Try Different Format**:
   - If PDF fails, try JSON or CSV
   - PDF generation requires more resources

4. **Check Permissions**:
```bash
chmod 755 backend/solver_sessions/{session_id}/
```

---

## WebSocket Issues

### Issue: Progress Updates Not Working

**Symptoms**:
- Progress bar doesn't update
- No real-time updates
- Connection errors in console

**Diagnosis**:
```javascript
// Check browser console for errors
// Look for WebSocket connection errors
```

**Solutions**:

1. **Check WebSocket Connection**:
```javascript
// Test WebSocket manually
const ws = new WebSocket('ws://localhost:5000/api/solve/progress');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
```

2. **Check Firewall**:
```bash
# Allow WebSocket port
sudo ufw allow 5000/tcp
```

3. **Check Nginx Config** (if using reverse proxy):
```nginx
location /api/solve/progress {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

4. **Reconnect**:
   - Refresh the page
   - WebSocket should reconnect automatically

---

## Authentication Issues

### Issue: 401 Unauthorized

**Symptoms**:
- Error: "Authentication required"
- Cannot access endpoints
- Token invalid

**Solutions**:

1. **Check Token**:
   - Verify token is included in Authorization header
   - Format: `Bearer <token>`

2. **Refresh Token**:
   - Log out and log back in
   - Request new token

3. **Check Token Expiry**:
   - Tokens may expire after certain time
   - Implement token refresh logic

---

### Issue: 403 Forbidden (Approval)

**Symptoms**:
- Error: "Admin privileges required"
- Cannot approve answer keys
- Insufficient permissions

**Solutions**:

1. **Verify Role**:
   - Check user role in database
   - Ensure user has "administrator" role

2. **Contact Administrator**:
   - Request admin privileges
   - Verify account permissions

---

## Log File Locations

### Main Application Logs

```
backend/logs/solver_main.log          # Main application log
backend/logs/access.log               # HTTP access log (production)
backend/logs/error.log                # Error log (production)
```

### Session-Specific Logs

```
backend/solver_sessions/{session_id}/logs/extraction.log   # Question extraction
backend/solver_sessions/{session_id}/logs/solving.log      # AI solving
backend/solver_sessions/{session_id}/logs/validation.log   # Validation
backend/solver_sessions/{session_id}/logs/errors.log       # Session errors
```

### System Logs

```
# Ollama logs (Linux)
sudo journalctl -u ollama -n 100

# Nginx logs
/var/log/nginx/access.log
/var/log/nginx/error.log

# System logs
/var/log/syslog  # Linux
/var/log/messages  # Some Linux distros
```

---

## Debugging Steps

### Step 1: Check Service Status

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check backend
curl http://localhost:5000/api/health

# Check models
ollama list
```

### Step 2: Review Logs

```bash
# Main log
tail -f backend/logs/solver_main.log

# Session log
tail -f backend/solver_sessions/{session_id}/logs/solving.log

# System log
sudo journalctl -f
```

### Step 3: Test Components

```bash
# Test Ollama
ollama run llama3.2 "Test"

# Test PDF processing
python -c "import fitz; print('PyMuPDF OK')"

# Test imports
python -c "from backend.question_parser import QuestionParser; print('Imports OK')"
```

### Step 4: Check Resources

```bash
# CPU and memory
htop

# Disk space
df -h

# Network
netstat -tulpn | grep 5000
```

### Step 5: Enable Debug Mode

```python
# In backend/app.py or config.py
app.config['DEBUG'] = True
LOG_LEVEL = 'DEBUG'
```

---

## Performance Tuning

### Optimize Processing Speed

1. **Use GPU**:
```bash
export OLLAMA_GPU=1
ollama serve
```

2. **Increase Workers**:
```bash
gunicorn --workers 4 backend.app:app
```

3. **Use Faster Models**:
```bash
# Quantized models are faster
ollama pull llama3.2:7b-q4_0
```

4. **Optimize Timeout**:
```python
# Balance between speed and accuracy
SOLVER_QUESTION_TIMEOUT = 20  # Reduce from 30
```

### Optimize Memory Usage

1. **Limit Concurrent Sessions**:
```python
SOLVER_MAX_CONCURRENT_SESSIONS = 1
```

2. **Clear Old Sessions**:
```bash
# Remove sessions older than 30 days
find backend/solver_sessions -type d -mtime +30 -exec rm -rf {} +
```

3. **Use Swap**:
```bash
# Add swap space
sudo fallocate -l 4G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Optimize Disk I/O

1. **Use SSD**:
   - Store sessions on SSD if possible
   - Faster read/write speeds

2. **Compress Old Sessions**:
```bash
# Compress completed sessions
tar -czf session_{id}.tar.gz backend/solver_sessions/{id}/
```

---

## Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Ollama service is not available" | Ollama not running | Start Ollama: `ollama serve` |
| "Model not found" | Model not installed | Install model: `ollama pull llama3.2` |
| "Invalid PDF file" | Corrupted or encrypted PDF | Check PDF validity, remove password |
| "Extraction failed" | Poor PDF quality | Improve PDF quality, use digital PDF |
| "Timeout" | Question too complex | Increase timeout or simplify question |
| "Session not found" | Invalid session ID | Check session ID, verify session exists |
| "Cannot approve" | Flagged questions not reviewed | Review all flagged questions first |
| "Export failed" | Disk space or permissions | Check disk space and permissions |

---

## Getting Help

### Before Contacting Support

1. Check this troubleshooting guide
2. Review relevant log files
3. Try basic debugging steps
4. Gather error messages and session IDs

### Information to Provide

When reporting issues, include:
- Session ID (if applicable)
- Error messages (exact text)
- Steps to reproduce
- Log file excerpts
- System information (OS, Python version, etc.)
- Screenshots (if UI issue)

### Support Channels

- Documentation: `/docs/`
- GitHub Issues: [repository-url]/issues
- Email: support@example.com
- User Forum: [forum-url]

---

**Last Updated**: January 2024  
**Version**: 1.0
