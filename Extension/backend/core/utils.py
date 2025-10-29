from cryptography.fernet import Fernet
from core.config import settings
from fastapi import Request
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize cipher for cookie encryption
cipher = Fernet(settings.COOKIE_ENCRYPTION_KEY.encode())

def encrypt_cookies(cookie_data: str) -> bytes:
    """Encrypt cookie string"""
    try:
        return cipher.encrypt(cookie_data.encode('utf-8'))
    except Exception as e:
        logger.error(f"Cookie encryption error: {e}")
        raise

def decrypt_cookies(encrypted_data: bytes) -> str:
    """Decrypt cookie string"""
    try:
        return cipher.decrypt(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Cookie decryption error: {e}")
        raise

def get_client_ip(request: Request) -> str:
    """
    Get real client IP address
    Handles proxy headers: X-Forwarded-For, X-Real-IP
    """
    # Check proxy headers first
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, first one is the real client
        return x_forwarded_for.split(',')[0].strip()
    
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip
    
    # Fallback to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"

def get_user_agent(request: Request) -> str:
    """Get user agent from request headers"""
    return request.headers.get('User-Agent', 'unknown')

def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube URL"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    return bool(re.match(youtube_regex, url))

def clean_cookie_string(cookie_data: str) -> str:
    """Clean and validate cookie string"""
    # Remove any non-essential characters and validate format
    lines = cookie_data.strip().split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and '\t' in line:
            parts = line.split('\t')
            if len(parts) >= 7:  # Basic Netscape format check
                cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def get_video_id_from_url(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None