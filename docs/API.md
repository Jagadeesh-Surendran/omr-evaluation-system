# API Documentation

## Overview

The OMR Evaluation System provides a REST API for extracting answer keys from question paper images using AI-powered vision models. This document describes the available endpoints, request/response formats, error codes, and usage examples.

## Base URL

When running locally:
```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible when the server is running.

## Endpoints

### Extract Answer Key

Extract answer keys from question paper images or PDFs using AI vision models.

**Endpoint:** `/api/extract_key`

**Method:** `POST`

**Content-Type:** `multipart/form-data`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `qp_file` | File | Yes | Question paper image or PDF file. Supported formats: JPG, PNG, PDF |

#### Request Example

```bash
curl -X POST http://localhost:5000/api/extract_key \
  -F "qp_file=@question_paper.jpg"
```

```javascript
// JavaScript/Fetch API
const formData = new FormData();
formData.append('qp_file', fileInput.files[0]);

fetch('http://localhost:5000/api/extract_key', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

```python
# Python/Requests
import requests

with open('question_paper.jpg', 'rb') as f:
    files = {'qp_file': f}
    response = requests.post('http://localhost:5000/api/extract_key', files=files)
    print(response.json())
```

#### Success Response

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "success": true,
  "answer_key": {
    "1": "A",
    "2": "C",
    "3": "B",
    "4": "D",
    "5": "E",
    "6": "A",
    "7": "C",
    "8": "B",
    "9": "D",
    "10": "E"
  },
  "count": 10,
  "warnings": [],
  "processing_time_ms": 2502.45
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` for successful responses |
| `answer_key` | object | Dictionary mapping question numbers (as strings) to answer letters (A-E) |
| `count` | integer | Total number of extracted question-answer pairs |
| `warnings` | array | List of warning messages (e.g., low answer count, validation issues) |
| `processing_time_ms` | float | Total processing time in milliseconds |

#### Success Response with Warnings

When extraction succeeds but produces fewer than 5 answers or has validation issues:

```json
{
  "success": true,
  "answer_key": {
    "1": "A",
    "2": "C",
    "3": "B"
  },
  "count": 3,
  "warnings": [
    "Only 3 answers extracted (< 5)"
  ],
  "processing_time_ms": 1845.23
}
```

#### Error Responses

All error responses follow this structure:

```json
{
  "error": "Human-readable error message",
  "error_type": "error_category_identifier",
  "suggestions": [
    "Actionable suggestion 1",
    "Actionable suggestion 2"
  ]
}
```

##### 400 Bad Request - No File Provided

**Status Code:** `400 Bad Request`

**Response Body:**

```json
{
  "error": "No question paper file provided",
  "error_type": "missing_file",
  "suggestions": [
    "Please select a file to upload"
  ]
}
```

**Cause:** The request did not include a file in the `qp_file` parameter.

##### 404 Not Found - File Not Found

**Status Code:** `404 Not Found`

**Response Body:**

```json
{
  "error": "The uploaded file could not be found",
  "error_type": "file_not_found",
  "suggestions": [
    "Try uploading the file again"
  ]
}
```

**Cause:** The uploaded file could not be saved or accessed on the server.

##### 422 Unprocessable Entity - Extraction Failed

**Status Code:** `422 Unprocessable Entity`

**Response Body:**

```json
{
  "error": "AI could not extract any answers from this file",
  "error_type": "extraction_failed",
  "suggestions": [
    "Ensure the image clearly shows question numbers and answers (e.g., Q1: A, Q2: C)",
    "Try uploading a higher resolution or clearer image",
    "Verify the answer key section is visible and not obscured",
    "If using a photo, ensure good lighting and focus"
  ]
}
```

**Cause:** The AI model attempted extraction using multiple strategies but could not identify any valid question-answer pairs in the image.

**Common Reasons:**
- Poor image quality (blurry, low resolution, poor lighting)
- Answer key not visible or formatted in an unrecognizable way
- Image does not contain an answer key
- Text is too small or obscured

##### 500 Internal Server Error - Service Unavailable

**Status Code:** `500 Internal Server Error`

**Response Body (Ollama Connection Error):**

```json
{
  "error": "Could not connect to Ollama AI service",
  "error_type": "service_unavailable",
  "suggestions": [
    "Ensure Ollama is installed and running",
    "Try running 'ollama serve' in a terminal",
    "Check if the moondream model is available"
  ]
}
```

**Cause:** The Ollama AI service is not running or not accessible.

**Resolution:**
1. Ensure Ollama is installed: [https://ollama.ai](https://ollama.ai)
2. Start Ollama service: `ollama serve`
3. Pull the required model: `ollama pull moondream`

##### 500 Internal Server Error - Processing Error

**Status Code:** `500 Internal Server Error`

**Response Body:**

```json
{
  "error": "An error occurred while processing the file",
  "error_type": "processing_error",
  "suggestions": [
    "Verify the file is a valid image or PDF",
    "Try a different file format",
    "Check if the file is corrupted"
  ]
}
```

**Cause:** An unexpected error occurred during file processing (e.g., corrupted file, unsupported format).

##### 500 Internal Server Error - Unexpected Error

**Status Code:** `500 Internal Server Error`

**Response Body:**

```json
{
  "error": "An unexpected error occurred while processing the file",
  "error_type": "server_error",
  "suggestions": [
    "Try uploading the file again",
    "Verify the file is not corrupted",
    "Contact support if the problem persists"
  ]
}
```

**Cause:** An unexpected server error occurred.

## HTTP Status Code Summary

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| `200` | Success | Answer key successfully extracted |
| `400` | Bad Request | No file provided in request |
| `404` | Not Found | Uploaded file could not be found |
| `422` | Unprocessable Entity | Extraction failed - no answers found |
| `500` | Internal Server Error | Server error, Ollama unavailable, or processing error |

## Extraction Process

The API uses a multi-pass extraction strategy to maximize success rates:

1. **Image Preprocessing**
   - PDF files are converted to high-resolution images (200+ DPI)
   - Images are enhanced for contrast and brightness
   - Images are resized to optimal dimensions for the AI model

2. **Multi-Pass Extraction**
   - Pass 1: Detailed JSON prompt with primary model
   - Pass 2: Simplified prompt with primary model
   - Pass 3: Alternative prompt strategy
   - Each pass includes JSON parsing with regex fallback

3. **Validation**
   - Question numbers validated as positive integers
   - Answers validated as single letters (A-E only)
   - Duplicate questions removed (first occurrence kept)
   - Low count warnings generated (< 5 answers)

4. **Response**
   - Validated results returned with metadata
   - Processing time and warnings included
   - Detailed error messages if extraction fails

## Best Practices

### Image Quality

For best results, provide high-quality images:

- **Resolution:** Minimum 1024px width, higher is better
- **Format:** JPG or PNG for images, PDF for scanned documents
- **Clarity:** Clear, focused images with good lighting
- **Contrast:** High contrast between text and background
- **Orientation:** Upright, not rotated or skewed

### Answer Key Format

The AI model works best with clearly formatted answer keys:

- **Explicit numbering:** Q1, Q2, Q3 or 1., 2., 3.
- **Clear answers:** A, B, C, D, or E next to question numbers
- **Consistent format:** Same format throughout the document
- **Visible text:** Large enough to read clearly

### Error Handling

Always handle errors gracefully in your client code:

```javascript
fetch('http://localhost:5000/api/extract_key', {
  method: 'POST',
  body: formData
})
  .then(response => {
    if (!response.ok) {
      return response.json().then(error => {
        throw new Error(error.error || 'Extraction failed');
      });
    }
    return response.json();
  })
  .then(data => {
    if (data.warnings && data.warnings.length > 0) {
      console.warn('Extraction warnings:', data.warnings);
    }
    console.log('Extracted answers:', data.answer_key);
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

### Performance Considerations

- **Timeout:** Extraction typically completes within 5-10 seconds
- **File Size:** Keep files under 10MB for optimal performance
- **Concurrent Requests:** The server can handle multiple concurrent requests
- **Retry Logic:** Implement retry logic for transient failures (500 errors)

## Rate Limiting

Currently, there is no rate limiting implemented. However, be mindful of:

- Server resource constraints
- Ollama model inference time
- Concurrent request handling

## Troubleshooting

### Common Issues

**Issue:** "Could not connect to Ollama AI service"

**Solution:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull the required model
ollama pull moondream
```

**Issue:** "AI could not extract any answers from this file"

**Solution:**
- Verify the image contains a visible answer key
- Ensure good image quality (resolution, lighting, focus)
- Try preprocessing the image manually (increase contrast, crop to answer key section)
- Use a scanner instead of a camera for better quality

**Issue:** "Only X answers extracted (< 5)"

**Solution:**
- This is a warning, not an error - extraction succeeded but found few answers
- Verify the answer key contains more questions
- Check if some answers are obscured or unclear
- Try uploading a clearer image

## Support

For issues, questions, or contributions:

- **GitHub:** [https://github.com/Jagadeesh-Surendran/omr-evaluation-system](https://github.com/Jagadeesh-Surendran/omr-evaluation-system)
- **Documentation:** See `docs/TROUBLESHOOTING.md` for more help

## Version History

- **v1.0** - Initial API release with basic extraction
- **v2.0** - Enhanced extraction with multi-pass strategies, preprocessing, and validation
