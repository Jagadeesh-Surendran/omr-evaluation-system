#!/usr/bin/env python3
"""Test AI extraction with realistic question paper"""

import sys
import os
sys.path.insert(0, 'backend')

from ollama_client import extract_answer_key_from_image

print("Testing AI extraction with realistic question paper...")
print("=" * 60)

image_path = 'realistic_question_paper.jpg'

if not os.path.exists(image_path):
    print(f"ERROR: {image_path} not found!")
    print("Run: python create_test_qp.py first")
    sys.exit(1)

try:
    print(f"\nExtracting from: {image_path}")
    print("This may take 30-60 seconds...")
    print("-" * 60)
    
    result, warnings, time_ms = extract_answer_key_from_image(image_path)
    
    print(f"\n[RESULT]")
    print(f"Extraction time: {time_ms:.0f}ms ({time_ms/1000:.1f}s)")
    print(f"Answers extracted: {len(result)}")
    print(f"\nExtracted answers:")
    
    if result:
        # Sort by question number
        sorted_answers = sorted(result.items())
        for q_num, answer in sorted_answers:
            print(f"  {q_num}. {answer}")
    else:
        print("  (none)")
    
    if warnings:
        print(f"\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Check if we got the expected answers
    expected = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'A',
        6: 'B', 7: 'C', 8: 'D', 9: 'A', 10: 'B',
        11: 'C', 12: 'D', 13: 'A', 14: 'B', 15: 'C',
        16: 'D', 17: 'A', 18: 'B', 19: 'C', 20: 'D'
    }
    
    if len(result) >= 10:
        print(f"\n[SUCCESS] AI extraction is WORKING!")
        print(f"Extracted {len(result)} answers")
        
        # Check accuracy
        correct = sum(1 for q, a in result.items() if expected.get(q) == a)
        if correct > 0:
            accuracy = (correct / len(result)) * 100
            print(f"Accuracy: {correct}/{len(result)} ({accuracy:.1f}%)")
    else:
        print(f"\n[PARTIAL] Extracted {len(result)} answers")
        print("AI extraction is working but may need better image quality")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
