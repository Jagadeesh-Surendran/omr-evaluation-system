# Detailed Setup Guide

This guide provides step-by-step instructions for setting up the OMR Evaluation System on your local machine.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Python**: 3.8 or higher
- **Internet**: Required for initial setup and Ollama model download

### Recommended Requirements
- **RAM**: 8GB or more
- **CPU**: Multi-core processor (4+ cores)
- **GPU**: Optional, but improves processing speed

## Step-by-Step Installation

### 1. Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```

#### macOS
```bash
# Using Homebrew
brew install python@3.11

# Verify installation
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

### 2. Install Git

#### Windows
Download and install from [git-scm.com](https://git-scm.com/download/win)

#### macOS
```bash
brew install git
```

#### Linux
```bash
sudo apt install git
```

### 3. Clone the Repository

```bash
git clone https://github.com/Jagadeesh-Surendran/omr-evaluation-system.git
cd omr-evaluation-system
```

### 4. Set Up Virtual Environment

#### Windows
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 5. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

This will install:
- Flask (web framework)
- OpenCV (computer vision)
- PyTorch (deep learning)
- Ollama (AI model client)
- NumPy, Pandas (data processing)
- And other dependencies

### 6. Install Ollama

#### Windows
1. Download from [ollama.ai/download](https://ollama.ai/download)
2. Run the installer
3. Ollama will start automatically

#### macOS
```bash
# Download and install
curl https://ollama.ai/install.sh | sh

# Or using Homebrew
brew install ollama
```

#### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

### 7. Download Vision Model

```bash
# Pull the moondream vision model (required for answer key extraction)
ollama pull moondream

# Verify model is installed
ollama list
```

The model download is approximately 1.7GB and may take several minutes.

### 8. Verify Installation

```bash
# Navigate to backend
cd backend

# Run a quick test
python -c "import cv2, torch, flask; print('All dependencies installed successfully!')"
```

### 9. Start the Application

```bash
# Make sure you're in the backend directory
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Running on http://[your-ip]:5000
```

### 10. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## Troubleshooting Installation

### Python Not Found

**Windows**:
- Reinstall Python and ensure "Add to PATH" is checked
- Restart your terminal/command prompt

**macOS/Linux**:
- Use `python3` instead of `python`
- Add to PATH: `export PATH="/usr/local/bin/python3:$PATH"`

### pip Install Fails

**Issue**: Permission denied
```bash
# Use --user flag
pip install --user -r backend/requirements.txt
```

**Issue**: SSL Certificate error
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend/requirements.txt
```

### OpenCV Installation Issues

**Windows**:
```cmd
pip install opencv-python-headless
```

**Linux**:
```bash
sudo apt install python3-opencv
pip install opencv-python
```

### Ollama Connection Issues

1. **Check if Ollama is running**:
   ```bash
   # Windows/macOS/Linux
   ollama serve
   ```

2. **Verify model is downloaded**:
   ```bash
   ollama list
   ```

3. **Test Ollama**:
   ```bash
   ollama run moondream "describe this image" < test_image.jpg
   ```

### Port 5000 Already in Use

Change the port in `backend/app.py`:
```python
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
```

Then access at `http://localhost:5001`

## Optional: GPU Acceleration

### NVIDIA GPU (CUDA)

1. Install CUDA Toolkit from [NVIDIA](https://developer.nvidia.com/cuda-downloads)
2. Install PyTorch with CUDA:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

### Apple Silicon (M1/M2/M3)

PyTorch automatically uses Metal Performance Shaders (MPS) on Apple Silicon.

## Development Setup

### Install Development Dependencies

```bash
pip install pytest hypothesis black flake8
```

### Run Tests

```bash
cd backend
pytest
```

### Code Formatting

```bash
black backend/
flake8 backend/
```

## Firebase Authentication Setup (Optional)

If you want to use Firebase authentication:

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Authentication → Email/Password and Google Sign-In
3. Get your Firebase config
4. Update the config in `frontend/index.html`

## Next Steps

- Read the [API Documentation](API.md)
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Try the example OMR sheets in `backend/synthetic_omr_data/`

## Getting Help

If you encounter issues not covered here:
1. Check the main [README.md](../README.md)
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Open an issue on GitHub with:
   - Your OS and Python version
   - Error messages
   - Steps to reproduce
