#!/usr/bin/env python3
"""Direct test of Flask app without running server"""

import sys
sys.path.insert(0, 'backend')

from app import app

# Create a test client
client = app.test_client()

# Test the health endpoint
response = client.get('/api/health')
print(f"Status Code: {response.status_code}")
print(f"Response: {response.get_json()}")
print(f"Data: {response.data}")
