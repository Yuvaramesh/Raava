"""
Vercel Serverless Function Handler
Wraps the Flask app for Vercel deployment
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel's Python runtime looks for 'app' variable at module level
app = app
