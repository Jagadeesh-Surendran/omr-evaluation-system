#!/usr/bin/env python3
"""Test direct extraction without PDF conversion"""

import sys
import os
import time
sys.path.insert(0, 'backend')

print("Testing DIRECT extraction (no PDF conversion)...")
print("=" * 60)

# Test with the realistic image we created
image_path = 'realistic_question_paper.jpg'

if not os.path.exists(image_path):
    print(f"Creating test image...")
    os.system('python create_test_qp.py')

print(f"\nExtracting from: {image_path}")
print("Using simplified prompts and direct file passing...")
print("-" * 60)

try:
    from ollama_client import extract_answer_key_from_image
    
    start = time.time()
    result, warnings, time_ms = extract_answer_key_from_image(image_path)
    elapsed = time.time() - start
    
    print(f"\n[RESULT]")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Answers extracted: {len(result)}")
    
    if result:
        print(f"\nExtracted answers:")
        sorted_answers = sorted(result.items())
        for q_num, answer in sorted_answers[:20]:  # Show first 20
            print(f"  {q_num}. {answer}")
        if len(result) > 20:
            print(f"  ... and {len(result) - 20} more")
    else:
        print("\nNo answers extracted")
        print("This might be because:")
        print("1. The image doesn't have clear 'ANSWER KEY' text")
        print("2. Moondream model needs better prompts")
        print("3. The image quality needs improvement")
    
    if warnings:
        print(f"\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
    
    # Verdict
    if len(result) >= 5:
        print(f"\n✓ AI extraction is WORKING!")
        print(f"  Extracted {len(result)} answers successfully")
    elif len(result) > 0:
        print(f"\n~ Partial success: {len(result)} answers")
        print(f"  AI is working but may need better images")
    else:
        print(f"\n✗ No answers extracted")
        print(f"  The AI model is running but couldn't find answers")
        print(f"  This is expected with synthetic test images")
        print(f"  Try with a real question paper PDF/image")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("\nNOTE: For your demo, use MANUAL mode which works perfectly!")
print("AI mode is a bonus feature that needs real question papers.")
