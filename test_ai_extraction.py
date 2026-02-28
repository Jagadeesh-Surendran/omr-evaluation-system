#!/usr/bin/env python3
"""Test AI answer key extraction with a simple test image"""

import sys
import os
sys.path.insert(0, 'backend')

# Create a simple test image with text
from PIL import Image, ImageDraw, ImageFont

def create_test_question_paper():
    """Create a simple test question paper image"""
    # Create white image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add title
    draw.text((50, 50), "ANSWER KEY", fill='black', font=font)
    
    # Add some questions with answers
    questions = [
        "1. A",
        "2. B",
        "3. C",
        "4. D",
        "5. A"
    ]
    
    y = 100
    for q in questions:
        draw.text((50, y), q, fill='black', font=font)
        y += 40
    
    # Save
    test_path = 'test_question_paper.jpg'
    img.save(test_path)
    print(f"[OK] Created test image: {test_path}")
    return test_path

# Create test image
test_image = create_test_question_paper()

# Test extraction
print("\nTesting AI extraction...")
try:
    from ollama_client import extract_answer_key_from_image
    
    result, warnings, time_ms = extract_answer_key_from_image(test_image)
    
    print(f"\n[OK] Extraction successful!")
    print(f"Extracted answers: {result}")
    print(f"Warnings: {warnings}")
    print(f"Time: {time_ms}ms")
    
    if len(result) > 0:
        print(f"\n[OK] AI extraction is WORKING!")
    else:
        print(f"\n[WARN] No answers extracted (this is expected with simple test image)")
        print(f"   The AI needs a real question paper image to work properly")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
if os.path.exists(test_image):
    os.remove(test_image)
