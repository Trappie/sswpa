#!/usr/bin/env python3
"""
Local development server for SSWPA website.
Sets up environment for local development with .env file.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment to local
os.environ['ENVIRONMENT'] = 'local'

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting SSWPA website in local development mode...")
    print("📝 Make sure to fill in your .env file with the correct values!")
    print("🔗 Website will be available at: http://localhost:8000")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Check if SSL certificates exist
    ssl_keyfile = "localhost+2-key.pem"
    ssl_certfile = "localhost+2.pem"
    
    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        print("🔒 Running with HTTPS (required for Square payments)")
        print("🔗 Website will be available at: https://localhost:8000")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app", "templates", "static"],
            log_level="info",
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        print("⚠️  Running without HTTPS - Square payments won't work")
        print("💡 To enable HTTPS: run 'mkcert localhost' to generate certificates")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app", "templates", "static"],
            log_level="info"
        )