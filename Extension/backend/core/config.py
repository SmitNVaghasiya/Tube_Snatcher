# core/config.py - Configuration settings
"""
Application configuration and settings
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings:
    """Application settings and configuration"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")  # Changed to 0.0.0.0 for external access
    PORT: int = int(os.getenv("PORT", "2004"))  # Changed to 2004 for Render
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "tubesnatcher")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-default-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Download settings
    MAX_CONCURRENT_DOWNLOADS: int = 2
    SHUTDOWN_DELAY: int = int(os.getenv("SHUTDOWN_DELAY", "3600"))  # Changed to 1 hour for online use
    
    # Directory settings
    DEFAULT_DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
    
    # yt-dlp settings
    YTDL_DEFAULT_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'get_filesize': True,
    }
    
    # Format preferences
    VIDEO_FORMAT_PREFERENCE = 'bestvideo+bestaudio/best'
    AUDIO_FORMAT_PREFERENCE = 'bestaudio/best'
    
    # File size estimation (bytes per pixel for rough calculation)
    FILESIZE_ESTIMATION_FACTOR = 0.1
    
    # Cookie encryption key
    COOKIE_ENCRYPTION_KEY: str = os.getenv("COOKIE_ENCRYPTION_KEY")
    
    def __init__(self):
        """Initialize settings and create default directories"""
        self.DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        # Generate encryption key if not provided
        if not self.COOKIE_ENCRYPTION_KEY:
            from cryptography.fernet import Fernet
            import os
            key = Fernet.generate_key().decode()
            os.environ['COOKIE_ENCRYPTION_KEY'] = key
            self.COOKIE_ENCRYPTION_KEY = key
    
    def get_download_directory(self, custom_location: Optional[str] = None) -> Path:
        """Get download directory path"""
        if custom_location and custom_location.strip() != "default":
            return Path(custom_location)
        return self.DEFAULT_DOWNLOAD_DIR
    
    def validate_download_directory(self, directory: Path) -> bool:
        """Validate if directory is writable"""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Test write permission
            test_file = directory / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            
            return True
        except Exception:
            return False

# Global settings instance
settings = Settings()