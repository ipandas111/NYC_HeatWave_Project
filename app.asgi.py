"""
ASGI wrapper for Shiny app to run on Render.com
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the Shiny app
from app import app as shiny_app

# Create ASGI app
def application():
    return shiny_app.to_asgi()

# For uvicorn
app = shiny_app.to_asgi()
