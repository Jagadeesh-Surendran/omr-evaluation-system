#!/usr/bin/env python3
"""Test Ollama integration"""

import sys
sys.path.insert(0, 'backend')

try:
    import ollama
    
    print("Testing Ollama connection...")
    
    # Test simple text generation
    response = ollama.chat(
        model='moondream',
        messages=[{
            'role': 'user',
            'content': 'What is 2+2? Answer in one word.'
        }]
    )
    
    print(f"✅ Ollama is working!")
    print(f"Response: {response['message']['content']}")
    
    # Test if we can list models
    models = ollama.list()
    print(f"\n✅ Available models:")
    for model in models['models']:
        print(f"  - {model['name']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
