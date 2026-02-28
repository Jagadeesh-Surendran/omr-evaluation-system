#!/usr/bin/env python3
"""Check what routes are registered in the Flask app"""

import sys
sys.path.insert(0, 'backend')

from app import app

print("Registered Routes:")
print("=" * 60)
for rule in app.url_map.iter_rules():
    print(f"{rule.rule:50} {list(rule.methods)}")
