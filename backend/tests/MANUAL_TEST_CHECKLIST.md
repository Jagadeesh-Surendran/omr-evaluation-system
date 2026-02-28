# Manual Testing Checklist for Answer Key Extraction

**Feature:** Improve Answer Key Extraction and GitHub Setup  
**Task:** 13.2 End-to-End Integration Testing - Manual Verification  
**Date:** 2024

## Prerequisites

- [ ] Ollama is installed and running (`ollama serve`)
- [ ] Moondream model is available (`ollama pull moondream`)
- [ ] Backend server is running (`python backend/app.py`)
- [ ] Frontend is accessible at `http://localhost:5000`

## Test Scenarios

### 1. Complete Extraction Flow with Real Images

#### Test 1.1: High Quality Question Paper Image
- [ ] Prepare a clear, high-resolution image of a question paper with answer key
- [ ] Upload the image through the frontend
- [ ] Verify extraction completes successfully
- [ ] Verify answer key is displayed correctly
- [ ] Verify processing time is shown
- [ ] Check `backend/debug_ollama.log` for extraction logs

**Expected Result:** Answer key extracted correctly, displayed in UI, logs show successful extraction

#### Test 1.2: Medium Quality Image
- [ ] Take a photo of a question paper with a mobile phone (good lighting)
- [ ] Upload the image
- [ ] Verify extraction works
- [ ] Check if preprocessing improved the image quality

**Expected Result:** Extraction succeeds, possibly with warnings about image quality

#### Test 1.3: Low Quality Image
- [ ] Take a blurry or poorly lit photo
- [ ] Upload the image
- [ ] Verify system attempts extraction with preprocessing
- [ ] Check if error message provides helpful suggestions

**Expected Result:** May fail with actionable error message suggesting better image quality

### 2. Various Image Formats

#### Test 2.1: JPEG Format
- [ ] Upload a .jpg or .jpeg file
- [ ] Verify extraction works

**Expected Result:** ✅ Successful extraction

#### Test 2.2: PNG Format
- [ ] Upload a .png file
- [ ] Verify extraction works

**Expected Result:** ✅ Successful extraction

#### Test 2.3: PDF Format
- [ ] Upload a PDF file containing answer key
- [ ] Verify PDF is converted to image
- [ ] Verify extraction works
- [ ] Check logs for PDF conversion entry

**Expected Result:** ✅ PDF converted at 200+ DPI, extraction succeeds

#### Test 2.4: Unsupported Format
- [ ] Try uploading a .txt or .doc file
- [ ] Verify appropriate error message

**Expected Result:** ⚠️ Error message about unsupported format

### 3. Error Scenarios

#### Test 3.1: No File Provided
- [ ] Click "Extract Answer Key" without selecting a file
- [ ] Verify error message appears
- [ ] Check error message has suggestions

**Expected Result:** 
- HTTP 400 error
- Error message: "No question paper file provided"
- Suggestion: "Please select a file to upload"

#### Test 3.2: No Answers Found
- [ ] Upload an image with no visible answer key (e.g., blank page)
- [ ] Verify error message appears
- [ ] Check suggestions are helpful

**Expected Result:**
- HTTP 422 error
- Error message: "AI could not extract any answers from this file"
- Suggestions include:
  - "Ensure the image clearly shows question numbers and answers"
  - "Try uploading a higher resolution or clearer image"
  - "Verify the answer key section is visible"

#### Test 3.3: Ollama Service Down
- [ ] Stop Ollama service (`Ctrl+C` on ollama serve)
- [ ] Try to extract answer key
- [ ] Verify error message mentions Ollama

**Expected Result:**
- HTTP 500 error
- Error message mentions Ollama service
- Suggestions include starting Ollama

#### Test 3.4: Corrupted Image File
- [ ] Create a corrupted image file (rename .txt to .jpg)
- [ ] Try to upload
- [ ] Verify graceful error handling

**Expected Result:**
- HTTP 422 or 500 error
- Error message about file processing
- No server crash

### 4. PDF File Handling

#### Test 4.1: Single Page PDF
- [ ] Upload a single-page PDF with answer key
- [ ] Verify conversion to image
- [ ] Verify extraction works
- [ ] Check logs for "PDF conversion" entry

**Expected Result:** ✅ PDF converted, extraction succeeds

#### Test 4.2: Multi-Page PDF
- [ ] Upload a multi-page PDF
- [ ] Verify only first page is processed
- [ ] Check extraction results

**Expected Result:** ✅ First page processed, extraction from first page only

#### Test 4.3: High Resolution PDF
- [ ] Upload a PDF with high DPI
- [ ] Verify conversion maintains quality
- [ ] Check extraction accuracy

**Expected Result:** ✅ High quality maintained, accurate extraction

### 5. Logging Output Verification

#### Test 5.1: Check Log File Creation
- [ ] Delete `backend/debug_ollama.log` if it exists
- [ ] Perform an extraction
- [ ] Verify log file is created
- [ ] Open log file and check contents

**Expected Log Entries:**
- Timestamp for each entry
- `[EXTRACTION_START]` with file name
- `[PASS_1]`, `[PASS_2]`, `[PASS_3]` entries
- `[PREPROCESSING]` entries
- `[VALIDATION]` warnings if applicable
- `[EXTRACTION_COMPLETE]` with total time

#### Test 5.2: Multi-Pass Logging
- [ ] Upload an image that might fail on first pass
- [ ] Check logs for multiple pass attempts
- [ ] Verify each pass is logged with:
  - Pass number
  - Model used
  - Strategy name
  - Success/failure status
  - Count of extracted answers
  - Duration

**Expected Result:** All passes logged with complete information

#### Test 5.3: Validation Warnings
- [ ] Upload an image that extracts < 5 answers
- [ ] Check logs for validation warning
- [ ] Verify warning mentions the threshold

**Expected Result:** Log contains `[VALIDATION] Warning: Only X answers extracted (< 5)`

### 6. Frontend Error Display

#### Test 6.1: Error Message Display
- [ ] Trigger each error type (no file, extraction failed, etc.)
- [ ] Verify error message appears in red/warning style
- [ ] Verify error icon is displayed
- [ ] Verify suggestions list is shown

**Expected Result:** 
- Error container becomes visible
- Error message is clear and readable
- Suggestions are displayed as bullet points
- Styling matches design (red border, warning icon)

#### Test 6.2: Error Dismissal
- [ ] Trigger an error
- [ ] Upload a new file
- [ ] Verify previous error is cleared

**Expected Result:** Error message disappears when new upload starts

#### Test 6.3: Success Message Display
- [ ] Successfully extract answer key
- [ ] Verify success message or answer key display
- [ ] Verify no error messages are shown

**Expected Result:** Answer key displayed, no errors visible

### 7. Performance Testing

#### Test 7.1: Processing Time
- [ ] Upload various images
- [ ] Note the processing time displayed
- [ ] Verify times are reasonable (< 30 seconds)

**Expected Result:** 
- Small images: < 5 seconds
- Large images: < 15 seconds
- PDFs: < 20 seconds

#### Test 7.2: Concurrent Requests
- [ ] Open multiple browser tabs
- [ ] Upload files simultaneously from different tabs
- [ ] Verify all requests complete successfully

**Expected Result:** All requests handled correctly, no crashes

#### Test 7.3: Large File Handling
- [ ] Upload a very large image (> 5MB)
- [ ] Verify preprocessing handles it
- [ ] Check memory usage doesn't spike excessively

**Expected Result:** Large files processed successfully, reasonable memory usage

### 8. Edge Cases

#### Test 8.1: Special Characters in Filename
- [ ] Upload a file with special characters in name (e.g., "test@#$.jpg")
- [ ] Verify file is handled correctly

**Expected Result:** ✅ File processed successfully

#### Test 8.2: Very Long Filename
- [ ] Upload a file with a very long filename (> 100 characters)
- [ ] Verify no errors

**Expected Result:** ✅ File processed successfully

#### Test 8.3: Rapid Successive Uploads
- [ ] Upload a file
- [ ] Immediately upload another file before first completes
- [ ] Verify both are handled correctly

**Expected Result:** Both requests complete, no conflicts

#### Test 8.4: Image with No Text
- [ ] Upload a completely blank white image
- [ ] Verify appropriate error message

**Expected Result:** Extraction fails with helpful error message

#### Test 8.5: Image with Wrong Content
- [ ] Upload an image of something other than a question paper (e.g., landscape photo)
- [ ] Verify system handles gracefully

**Expected Result:** Extraction fails, error message suggests checking content

## Test Results

### Summary
- **Total Test Cases:** 30+
- **Passed:** _____
- **Failed:** _____
- **Blocked:** _____
- **Not Tested:** _____

### Issues Found
| Issue # | Description | Severity | Status |
|---------|-------------|----------|--------|
| | | | |

### Notes
_Add any additional observations or comments here_

---

## Sign-off

**Tested By:** ___________________  
**Date:** ___________________  
**Environment:** ___________________  
**Ollama Version:** ___________________  
**Browser:** ___________________  

**Overall Status:** ⬜ PASS / ⬜ FAIL / ⬜ PASS WITH ISSUES

**Tester Signature:** ___________________
