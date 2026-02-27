# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the OMR Evaluation System, particularly focusing on AI-powered answer key extraction, Ollama connection problems, and performance optimization.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Ollama Connection Problems](#ollama-connection-problems)
- [Answer Key Extraction Failures](#answer-key-extraction-failures)
- [Image Quality Issues](#image-quality-issues)
- [Performance Optimization](#performance-optimization)
- [OMR Sheet Processing Issues](#omr-sheet-processing-issues)
- [File Upload Problems](#file-upload-problems)
- [Debug Logging](#debug-logging)
- [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

Before diving into specific issues, run these quick checks:

### 1. Check Ollama Status

```bash
# Check if Ollama is running
ollama list

# If not running, start Ollama
ollama serve
```

### 2. Verify Model Installation

```bash
# Check if moondream model is installed
ollama list | grep moondream

# If not installed, pull the model
ollama pull moondream
```

### 3. Check Backend Server

```bash
# Ensure Flask server is running
cd backend
python app.py

# Server should start on http://localhost:5000
```

### 4. Review Debug Logs

```bash
# Check the debug log for recent errors
tail -n 50 backend/debug_ollama.log
```

---

## Ollama Connection Problems

### Symptom: "Could not connect to Ollama AI service"

**Cause**: The Ollama service is not running or not accessible.

**Solutions**:

1. **Start Ollama Service**
   ```bash
   ollama serve
   ```
   Keep this terminal window open while using the application.

2. **Verify Ollama Installation**
   ```bash
   # Check if Ollama is installed
   ollama --version
   
   # If not installed, download from https://ollama.ai
   ```

3. **Check Port Availability**
   - Ollama runs on port 11434 by default
   - Ensure no other service is using this port
   ```bash
   # Windows
   netstat -ano | findstr :11434
   
   # Linux/Mac
   lsof -i :11434
   ```

4. **Restart Ollama**
   ```bash
   # Stop any running Ollama processes
   # Windows: Use Task Manager to end ollama.exe
   # Linux/Mac: pkill ollama
   
   # Start fresh
   ollama serve
   ```

### Symptom: "Model 'moondream' not found"

**Cause**: The required vision model is not installed.

**Solutions**:

1. **Pull the Model**
   ```bash
   ollama pull moondream
   ```
   This downloads the moondream vision model (~1.7GB).

2. **Verify Model Installation**
   ```bash
   ollama list
   ```
   You should see `moondream` in the list.

3. **Test Model Directly**
   ```bash
   ollama run moondream
   ```
   Type a test message to verify the model works.

### Symptom: Ollama Starts but Crashes Immediately

**Cause**: Insufficient system resources or corrupted installation.

**Solutions**:

1. **Check System Requirements**
   - Minimum 8GB RAM recommended
   - At least 4GB free disk space
   - Modern CPU with AVX support

2. **Reinstall Ollama**
   ```bash
   # Uninstall current version
   # Download latest version from https://ollama.ai
   # Install fresh copy
   ```

3. **Check Ollama Logs**
   ```bash
   # Windows: Check Event Viewer
   # Linux/Mac: Check system logs
   journalctl -u ollama
   ```

---

## Answer Key Extraction Failures

### Symptom: "AI could not extract any answers from this file"

**Cause**: The AI model cannot identify answer patterns in the image.

**Solutions**:

1. **Verify Answer Key Format**
   
   The AI looks for patterns like:
   - `Q1: A` or `1. A` or `1) A`
   - `Question 1: A`
   - `1 A` (number followed by letter)
   
   Ensure your question paper clearly shows these patterns.

2. **Improve Image Quality**
   - Use a scanner instead of a camera
   - Ensure good lighting (no shadows)
   - Hold camera steady (avoid blur)
   - Minimum 200 DPI for scanned images
   - Take photo straight-on (avoid angles)

3. **Try Different File Formats**
   ```
   Supported formats:
   - JPG/JPEG (recommended)
   - PNG
   - PDF (automatically converted to image)
   ```

4. **Crop to Answer Key Section**
   - If the image contains multiple pages or sections
   - Crop to show only the answer key area
   - Remove unnecessary borders or margins

5. **Check Debug Logs**
   ```bash
   # View extraction attempts
   grep "EXTRACTION_START" backend/debug_ollama.log
   grep "PASS_" backend/debug_ollama.log
   ```
   
   The logs show:
   - How many extraction passes were attempted
   - What the AI model returned
   - Why each pass failed

### Symptom: Only Partial Answers Extracted

**Cause**: Some answers are visible but others are missed.

**Solutions**:

1. **Check Warning Messages**
   - The system warns if fewer than 5 answers are extracted
   - Review the warnings in the response

2. **Verify Answer Visibility**
   - Ensure all answers are clearly visible
   - Check for faded text or poor contrast
   - Verify no answers are cut off at edges

3. **Manual Review**
   - Use the extracted answers as a starting point
   - Manually add missing answers in the UI
   - Save the complete answer key

4. **Adjust Image Preprocessing**
   - The system automatically enhances contrast
   - If preprocessing fails, try pre-processing the image externally:
   ```python
   # Example: Enhance image before upload
   import cv2
   img = cv2.imread('question_paper.jpg')
   gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
   enhanced = cv2.equalizeHist(gray)
   cv2.imwrite('enhanced_qp.jpg', enhanced)
   ```

### Symptom: Wrong Answers Extracted

**Cause**: AI misreads the answer letters or question numbers.

**Solutions**:

1. **Verify Source Image**
   - Double-check the original image
   - Ensure answer key is correct in the source

2. **Check for Ambiguity**
   - Ensure letters are clearly printed (not handwritten)
   - Avoid fonts where letters look similar (O vs 0, I vs 1)
   - Use standard fonts (Arial, Times New Roman)

3. **Manual Correction**
   - Review extracted answers before processing OMR sheets
   - Correct any errors in the UI
   - Save corrected answer key for future use

---

## Image Quality Issues

### Symptom: "Image quality is too low for reliable extraction"

**Cause**: The uploaded image has insufficient resolution or clarity.

**Solutions**:

1. **Increase Resolution**
   - Minimum: 1024px width
   - Recommended: 1920px width or higher
   - For PDFs: 200 DPI minimum, 300 DPI recommended

2. **Use Scanner Instead of Camera**
   - Scanners provide consistent quality
   - Set scanner to 300 DPI
   - Use color or grayscale mode (not black & white)

3. **Improve Camera Photos**
   - Use good lighting (natural light or bright indoor lighting)
   - Avoid shadows across the document
   - Hold camera parallel to document (not at angle)
   - Use camera's document mode if available
   - Ensure focus is sharp (tap to focus on phone cameras)

4. **Pre-process Images**
   - Adjust brightness and contrast
   - Remove color casts
   - Sharpen slightly if blurry
   - Use photo editing software or apps

### Symptom: PDF Conversion Fails

**Cause**: PDF file is corrupted, password-protected, or unsupported format.

**Solutions**:

1. **Verify PDF File**
   - Open PDF in a PDF reader to ensure it's valid
   - Check file size (should be reasonable, not 0 bytes)

2. **Remove Password Protection**
   ```bash
   # Use PDF tools to remove password
   # Or print to PDF to create unprotected copy
   ```

3. **Convert PDF to Image Manually**
   ```bash
   # Use online tools or software to convert PDF to JPG
   # Upload the JPG instead of PDF
   ```

4. **Check PDF Version**
   - Very old or very new PDF versions may have issues
   - Try re-saving PDF in standard format (PDF 1.7)

---

## Performance Optimization

### Symptom: Extraction Takes Too Long (>30 seconds)

**Cause**: Large images, slow hardware, or Ollama performance issues.

**Solutions**:

1. **Optimize Image Size**
   ```python
   # Resize large images before upload
   from PIL import Image
   
   img = Image.open('large_image.jpg')
   img.thumbnail((1920, 1920))  # Max 1920px on longest side
   img.save('optimized_image.jpg', quality=85)
   ```

2. **Adjust Timeout Configuration**
   ```python
   # In backend/ollama_client.py
   config = ExtractionConfig(
       extraction_timeout_seconds=60,  # Increase timeout
       max_extraction_passes=2  # Reduce passes for speed
   )
   ```

3. **Hardware Acceleration**
   - Ollama can use GPU if available
   - Check Ollama documentation for GPU setup
   - Ensure latest GPU drivers installed

4. **Reduce Extraction Passes**
   - Default: 3 passes for reliability
   - For speed: Reduce to 1-2 passes
   - Edit `ExtractionConfig` in `ollama_client.py`

### Symptom: High Memory Usage

**Cause**: Large images or multiple concurrent extractions.

**Solutions**:

1. **Limit Concurrent Requests**
   - Process one extraction at a time
   - Wait for completion before starting next

2. **Reduce Image Size**
   - Target width: 1024px (default)
   - Larger images use more memory
   - Preprocessing automatically resizes

3. **Restart Services Periodically**
   ```bash
   # Restart Ollama
   pkill ollama
   ollama serve
   
   # Restart Flask backend
   # Stop with Ctrl+C, then restart
   python app.py
   ```

4. **Monitor System Resources**
   ```bash
   # Windows: Task Manager
   # Linux: htop or top
   # Mac: Activity Monitor
   ```

### Symptom: Slow OMR Sheet Processing

**Cause**: Large batch processing or complex bubble detection.

**Solutions**:

1. **Process in Smaller Batches**
   - Instead of 100 sheets at once
   - Process 20-30 sheets per batch
   - Reduces memory usage and improves responsiveness

2. **Optimize OMR Sheet Images**
   - Use consistent image size
   - Ensure good contrast (dark bubbles, white background)
   - Remove unnecessary margins

3. **Disable Preprocessing for OMR Sheets**
   - Preprocessing is for question papers
   - OMR sheets don't need preprocessing
   - Saves processing time

---

## OMR Sheet Processing Issues

### Symptom: Bubbles Not Detected

**Cause**: Poor image quality, incorrect bubble format, or model issues.

**Solutions**:

1. **Check Bubble Format**
   - Bubbles should be clearly filled (dark)
   - Use standard OMR sheet format
   - Ensure bubbles are circular or oval

2. **Verify Image Quality**
   - High contrast between filled and empty bubbles
   - No shadows or glare
   - Straight scan (not skewed)

3. **Review Manual Mode**
   - Use Manual mode to see detected bubbles
   - Check if detection is working
   - Manually correct misdetections

4. **Retrain Bubble Detection Model**
   - If many sheets have issues
   - Consider retraining the bubble detection model
   - See `backend/train_model.py`

### Symptom: Wrong Answers Detected

**Cause**: Multiple bubbles filled, faint marks, or detection errors.

**Solutions**:

1. **Check Original Sheets**
   - Verify students filled bubbles correctly
   - Look for multiple marks or erasures
   - Check for stray marks

2. **Use Manual Review**
   - Review flagged answers in Manual mode
   - Correct any misdetections
   - Save corrected results

3. **Adjust Detection Threshold**
   - Edit bubble detection sensitivity
   - See `backend/omr_engine.py`
   - Balance between false positives and false negatives

---

## File Upload Problems

### Symptom: "File upload failed" or "File too large"

**Cause**: File size exceeds limit or network issues.

**Solutions**:

1. **Check File Size Limit**
   - Default limit: 16MB per file
   - Compress large images
   - Use JPG instead of PNG (smaller file size)

2. **Compress Images**
   ```python
   from PIL import Image
   
   img = Image.open('large_file.jpg')
   img.save('compressed.jpg', quality=70, optimize=True)
   ```

3. **Check Network Connection**
   - Ensure stable internet connection
   - Try uploading again
   - Use wired connection if possible

4. **Increase Upload Limit**
   ```python
   # In backend/app.py
   app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
   ```

### Symptom: "Invalid file format"

**Cause**: Unsupported file type uploaded.

**Solutions**:

1. **Use Supported Formats**
   - Question Papers: JPG, PNG, PDF
   - OMR Sheets: JPG, PNG
   - Answer Keys: CSV, JSON

2. **Convert File Format**
   - Use image editing software
   - Convert to JPG or PNG
   - Ensure proper file extension

---

## Debug Logging

### Understanding Debug Logs

The system logs all extraction attempts to `backend/debug_ollama.log`.

**Log Entry Format**:
```
2024-01-15 10:30:45 - [EXTRACTION_START] File: question_paper.jpg
2024-01-15 10:30:45 - [PREPROCESSING] PDF conversion: 245ms
2024-01-15 10:30:45 - [PREPROCESSING] Image enhancement: 123ms
2024-01-15 10:30:46 - [PASS_1] Model: moondream, Strategy: detailed_json
2024-01-15 10:30:48 - [PASS_1] Raw output: {"1":"A","2":"C"...
2024-01-15 10:30:48 - [PASS_1] Result: SUCCESS, Count: 25, Duration: 2134ms
2024-01-15 10:30:48 - [VALIDATION] Warning: Duplicate question 5 removed
2024-01-15 10:30:48 - [EXTRACTION_COMPLETE] Total: 2502ms, Final count: 24
```

**Key Log Tags**:
- `[EXTRACTION_START]` - New extraction attempt begins
- `[PREPROCESSING]` - Image preprocessing operations
- `[PASS_N]` - Extraction pass number (1, 2, 3)
- `[VALIDATION]` - Validation warnings
- `[EXTRACTION_COMPLETE]` - Final result
- `[CLEANUP]` - Temporary file cleanup

### Enabling Verbose Logging

```python
# In backend/ollama_client.py
# Change log level for more details
config = ExtractionConfig(
    log_path="debug_ollama.log"
)

# View logs in real-time
tail -f backend/debug_ollama.log
```

### Common Log Patterns

**Successful Extraction**:
```
[PASS_1] Result: SUCCESS, Count: 25, Duration: 2134ms
[EXTRACTION_COMPLETE] Total: 2502ms, Final count: 25
```

**All Passes Failed**:
```
[PASS_1] Result: FAILED, Count: 0, Duration: 2134ms
[PASS_2] Result: FAILED, Count: 0, Duration: 1876ms
[PASS_3] Result: FAILED, Count: 0, Duration: 2001ms
All extraction passes failed — returning {}
```

**Partial Extraction**:
```
[PASS_1] Result: SUCCESS, Count: 3, Duration: 2134ms
[VALIDATION] Warning: Only 3 answers extracted (< 5)
```

---

## Common Error Messages

### Error: "No question paper file provided"

**HTTP Status**: 400 Bad Request

**Cause**: No file was uploaded in the request.

**Solution**: Ensure you select a file before clicking upload.

---

### Error: "The uploaded file could not be found"

**HTTP Status**: 404 Not Found

**Cause**: File was not saved properly or was deleted.

**Solutions**:
1. Try uploading again
2. Check disk space
3. Verify write permissions on `temp_uploads/` directory

---

### Error: "AI could not extract any answers from this file"

**HTTP Status**: 422 Unprocessable Entity

**Cause**: All extraction passes failed to find answers.

**Solutions**: See [Answer Key Extraction Failures](#answer-key-extraction-failures) section above.

---

### Error: "An error occurred while processing the file"

**HTTP Status**: 500 Internal Server Error

**Cause**: Unexpected error during processing.

**Solutions**:
1. Check debug logs for details
2. Verify file is not corrupted
3. Try a different file
4. Restart backend server

---

### Error: "Could not connect to Ollama AI service"

**HTTP Status**: 500 Internal Server Error

**Cause**: Ollama service is not running or not accessible.

**Solutions**: See [Ollama Connection Problems](#ollama-connection-problems) section above.

---

## Advanced Troubleshooting

### Testing Ollama Directly

Test if Ollama is working independently of the application:

```bash
# Test text model
ollama run llama2 "Hello, how are you?"

# Test vision model with an image
ollama run moondream "Describe this image" --image question_paper.jpg
```

### Testing Extraction Function Directly

Test the extraction function from command line:

```bash
cd backend
python ollama_client.py path/to/question_paper.jpg
```

This runs extraction and prints results directly.

### Checking Python Dependencies

Ensure all required packages are installed:

```bash
cd backend
pip install -r requirements.txt

# Verify specific packages
python -c "import ollama; print(ollama.__version__)"
python -c "import cv2; print(cv2.__version__)"
python -c "import fitz; print(fitz.__version__)"
```

### Network Diagnostics

Check if Ollama API is accessible:

```bash
# Test Ollama API endpoint
curl http://localhost:11434/api/tags

# Should return list of installed models
```

### Clearing Temporary Files

Clean up temporary files that may cause issues:

```bash
# Remove temporary uploads
rm -rf backend/temp_uploads/*

# Remove temporary preprocessed images
rm -rf backend/*_preprocessed.jpg
rm -rf backend/*_converted.jpg

# Clear debug log (optional)
> backend/debug_ollama.log
```

---

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check Debug Logs**
   - Review `backend/debug_ollama.log`
   - Look for error messages and stack traces

2. **Gather Information**
   - What were you trying to do?
   - What error message did you see?
   - What have you tried already?
   - System information (OS, RAM, Python version)

3. **Create an Issue**
   - Visit the GitHub repository
   - Create a new issue with details above
   - Include relevant log excerpts (remove sensitive data)

4. **Community Support**
   - Check existing GitHub issues
   - Search for similar problems
   - Ask in discussions

---

## Preventive Maintenance

### Regular Maintenance Tasks

1. **Clear Temporary Files Weekly**
   ```bash
   rm -rf backend/temp_uploads/*
   ```

2. **Rotate Debug Logs**
   ```bash
   # Archive old logs
   mv backend/debug_ollama.log backend/debug_ollama_$(date +%Y%m%d).log
   
   # Keep only last 7 days
   find backend/ -name "debug_ollama_*.log" -mtime +7 -delete
   ```

3. **Update Ollama Models**
   ```bash
   # Check for model updates
   ollama pull moondream
   ```

4. **Update Python Dependencies**
   ```bash
   cd backend
   pip install --upgrade -r requirements.txt
   ```

### Performance Monitoring

Monitor these metrics for optimal performance:

- **Extraction Success Rate**: Should be >90%
- **Average Processing Time**: Should be <10 seconds
- **Memory Usage**: Should stay under 2GB
- **Disk Space**: Keep at least 5GB free

### Best Practices

1. **Image Quality**
   - Always use high-resolution images (1920px+ width)
   - Prefer scanned images over photos
   - Ensure good lighting and contrast

2. **File Management**
   - Clean up temporary files regularly
   - Archive old debug logs
   - Keep backups of important answer keys

3. **System Resources**
   - Close unnecessary applications
   - Ensure adequate RAM (8GB+ recommended)
   - Keep disk space available (5GB+ free)

4. **Regular Updates**
   - Update Ollama regularly
   - Update Python packages
   - Check for application updates

---

## Quick Reference

### Essential Commands

```bash
# Start Ollama
ollama serve

# Check Ollama status
ollama list

# Pull moondream model
ollama pull moondream

# Start Flask backend
cd backend
python app.py

# View debug logs
tail -f backend/debug_ollama.log

# Test extraction directly
python backend/ollama_client.py question_paper.jpg
```

### Configuration Files

- `backend/ollama_client.py` - Extraction configuration
- `backend/app.py` - API endpoints and error messages
- `backend/debug_ollama.log` - Debug logs
- `backend/requirements.txt` - Python dependencies

### Important Directories

- `backend/temp_uploads/` - Temporary file storage
- `backend/tests/` - Test files
- `docs/` - Documentation
- `frontend/` - Web interface

---

**Last Updated**: January 2024  
**Version**: 1.0
