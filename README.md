# OMR Evaluation System - EvalGenius AI

Next-generation Optical Mark Recognition system with AI-powered answer key extraction and automated grading.

## Features

- 🤖 **AI-Powered Answer Key Extraction** - Automatically extract answer keys from question paper images using Ollama vision models
- 📊 **Automated OMR Sheet Evaluation** - Advanced bubble detection with deep learning (BubbleCNN-V2) and computer vision
- 📈 **Real-Time Grading & Analytics** - Instant scoring with detailed performance insights and statistics
- 🔄 **Multi-Set Exam Support** - Handle Set A and Set B question papers with automatic form type detection
- 📱 **Modern Web Interface** - Clean, responsive UI with Firebase authentication
- 🔌 **Hardware Integration** - Support for physical OMR scanning machines via USB/Serial
- 📤 **Export Capabilities** - Export results to CSV or Excel with detailed question-by-question breakdown
- 🎯 **Manual Review Mode** - Review and correct AI bubble readings when needed

## Prerequisites

- **Python 3.8+**
- **Ollama** (for AI answer key extraction)
- **OpenCV dependencies**
- **Modern web browser** (Chrome, Firefox, Edge, Safari)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Jagadeesh-Surendran/omr-evaluation-system.git
cd omr-evaluation-system
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

Pull the required vision model:
```bash
ollama pull moondream
```

### 4. Run the Application

```bash
# Navigate to backend directory
cd backend

# Start the Flask server
python app.py
```

The server will start on `http://localhost:5000`

Open your browser and navigate to `http://localhost:5000`

## Usage

### Automatic Evaluation Mode

1. **Upload Question Papers** - Upload Set A and/or Set B question paper images for AI extraction
2. **Upload OMR Sheets** - Upload student answer sheets (supports multiple files)
3. **Process** - Click "Process Sheets" to evaluate all submissions
4. **View Results** - See scores, analytics, grade distribution, and AI insights
5. **Export** - Download results as CSV or Excel

### Manual Evaluation Mode

1. Process sheets in automatic mode first
2. Click "Manual" on any student result to review bubble detections
3. Correct any misreadings if necessary
4. Save changes to recalculate scores

### Hardware Mode

1. Connect your OMR scanning machine via USB/Serial
2. Click "Connect OMR" in the dashboard
3. Sheets will be processed automatically as they're scanned

## Project Structure

```
omr-evaluation-system/
├── backend/                    # Flask API server
│   ├── app.py                 # Main Flask application
│   ├── ollama_client.py       # AI answer key extraction
│   ├── omr_engine.py          # Core OMR processing
│   ├── pipeline.py            # Unified processing pipeline
│   ├── dl_model.py            # Deep learning bubble classifier
│   ├── full_evaluator.py     # Complete evaluation logic
│   ├── hardware_handler.py   # Hardware integration
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Web interface
│   ├── index.html             # Main application UI
│   └── style.css              # Styling
├── .kiro/                      # Kiro AI specifications
│   └── specs/                 # Feature specifications
└── README.md                   # This file
```

## Configuration

### Answer Key Extraction

Edit `backend/ollama_client.py` to configure:
- Vision model selection (default: moondream)
- Extraction timeout
- Image preprocessing options
- Logging level

### OMR Processing

Edit `backend/pipeline.py` to configure:
- YOLO confidence levels
- Bubble detection thresholds
- Number of answer options (3, 4, or 5)

## Troubleshooting

### Ollama Connection Issues

**Problem**: "Ollama server not responding" error

**Solution**:
```bash
# Ensure Ollama is running
ollama serve

# Verify model is installed
ollama list
```

### Answer Key Extraction Failures

**Problem**: "Set A extraction failed" or "AI could not extract any answers"

**Solutions**:
- Use high-resolution images (200+ DPI for PDFs)
- Ensure good lighting and contrast
- Verify answer key format is clearly visible (e.g., Q1: A, Q2: C)
- Try scanning instead of photographing
- Ensure the answer key section is not obscured

### Bubble Detection Issues

**Problem**: Incorrect bubble readings

**Solutions**:
- Use the Manual Review mode to correct misreadings
- Ensure OMR sheets are properly aligned
- Check that bubbles are filled darkly and completely
- Avoid stray marks near bubbles

### Performance Issues

**Problem**: Slow processing

**Solutions**:
- Reduce image resolution before upload
- Process fewer sheets at once
- Ensure adequate system resources (RAM, CPU)
- Close other applications

For more detailed troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Technology Stack

- **Backend**: Python, Flask, OpenCV, PyTorch
- **AI/ML**: Ollama (moondream), YOLOv8, Custom CNN
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Authentication**: Firebase Auth
- **Real-time**: Socket.IO
- **Data Processing**: NumPy, Pandas, PyMuPDF

## API Endpoints

### `/api/extract_key` - Extract Answer Key
- **Method**: POST
- **Input**: Question paper image/PDF
- **Output**: Extracted answer key JSON

### `/api/evaluate` - Evaluate OMR Sheets
- **Method**: POST
- **Input**: OMR sheet images + answer key
- **Output**: Grading results with analytics

### `/api/evaluate_batch` - Batch Evaluation
- **Method**: POST
- **Input**: Multiple OMR sheets
- **Output**: Parallel processing results

For complete API documentation, see [docs/API.md](docs/API.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

**Jagadeesh Surendran**
- GitHub: [@Jagadeesh-Surendran](https://github.com/Jagadeesh-Surendran)

## Acknowledgments

- Ollama team for the vision model infrastructure
- OpenCV community for computer vision tools
- YOLOv8 for object detection capabilities

## Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Review [API Documentation](docs/API.md)
3. Open an issue on GitHub

---

Made with ❤️ for educators and students
