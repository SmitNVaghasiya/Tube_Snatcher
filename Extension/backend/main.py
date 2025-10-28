# main.py - Main entry point for Tube Snatcher Extension Backend
"""
Tube Snatcher Extension Backend
Main application entry point with improved structure and error handling
"""

import uvicorn
import sys
import os
from pathlib import Path
from core.config import settings

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main function to start the FastAPI server"""
    try:
        print("=" * 60)
        print("🚀 Tube Snatcher Extension Backend v3.0.0")
        print("=" * 60)
        print(f"🔗 Server: http://{settings.HOST}:{settings.PORT}")
        print("📝 API Docs: /docs")
        print("🔄 Auto-shutdown: 1 hour after last activity")
        print("⏹️  Manual stop: Ctrl+C")
        print("=" * 60)
        
        # Start the server
        uvicorn.run(
            "app:app",
            host=settings.HOST,
            port=settings.PORT,
            log_level="info" if settings.DEBUG else "warning",
            reload=settings.DEBUG,
            access_log=True  # Show access logs
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        print("💡 Set environment variables for production deployment")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)