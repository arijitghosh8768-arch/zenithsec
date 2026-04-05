# File: api/index.py
import sys
import os

# Add the parent directory to sys.path so we can import 'backend'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the FastAPI app from backend.main
from main import app as application

# Vercel needs 'app' or 'handler'
app = application
