# TubeSnatcher Backend

## Overview
TubeSnatcher Backend is a FastAPI-based server application designed to work with the TubeSnatcher Chrome Extension for downloading YouTube videos securely. The backend provides authentication, cookie handling, and manages downloads with comprehensive tracking.

## Features

### Core Features
- **Secure Cookie Handling**: Extracts and uses YouTube cookies for authenticated downloads
- **JWT Authentication**: Token-based access control for API endpoints
- **MongoDB Integration**: Tracks downloads and unique users for analytics
- **Download Management**: Queue system with progress tracking
- **Format Support**: MP4, MP3, and various quality options
- **Playlist Support**: Full and single video playlist downloads

### Security Features
- **Encrypted Cookie Storage**: YouTube cookies encrypted using Fernet symmetric encryption
- **Token-Based Access Control**: JWT tokens with expiration for secure API access
- **IP Tracking**: Logs all download attempts with source IP
- **Rate Limiting Ready**: Structure in place for rate limiting implementations

### Analytics
- **Download Tracking**: Comprehensive logging of all download attempts
- **User Analytics**: Track unique users and download patterns
- **Success/Failure Logging**: Detailed error reporting and tracking

## Architecture

### API Endpoints
- `/api/v1/auth/get-token` - Generate authentication token for extension
- `/api/v1/auth/verify-token` - Verify authentication token
- `/api/v1/fetch-details-with-cookies` - Get video details with authentication
- `/api/v1/download-with-cookies` - Download video with cookies
- `/api/v1/download-locations` - Get available download locations
- `/api/v1/history` - Download history
- `/api/v1/analytics` - Usage analytics
- `/api/v1/status` - Server health check

### Tech Stack
- **FastAPI**: Modern Python web framework
- **yt-dlp**: YouTube video downloader
- **MongoDB**: Database for analytics and user tracking
- **PyJWT**: JSON Web Token implementation
- **Cryptography**: Cookie encryption

## Environment Variables
- `SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)
- `MONGODB_URL`: MongoDB connection string
- `COOKIE_ENCRYPTION_KEY`: Fernet encryption key for cookies
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 2004)
- `SHUTDOWN_DELAY`: Auto-shutdown delay in seconds

## Deployment

### Render Deployment
1. Set up MongoDB Atlas or other MongoDB service
2. Configure environment variables in Render dashboard
3. Deploy using the provided `render.yaml`

### Docker Deployment
```bash
docker build -t tubesnatcher-backend .
docker run -p 2004:2004 -e MONGODB_URL=your_mongo_url tubesnatcher-backend
```

## Security Considerations
- Environment variables should never be hardcoded
- Use strong, unique JWT and encryption keys
- Regularly rotate security keys
- Monitor analytics for unusual activity
- Use HTTPS in production environments

## Why These Features Were Added
- **Cookie Authentication**: To handle YouTube's authentication requirements safely
- **Token System**: To prevent unauthorized API access and track usage
- **Database**: For analytics and security monitoring
- **Encryption**: To protect user's YouTube credentials
- **Analytics**: To understand usage patterns and detect abuse
- **Format Support**: To provide flexibility in download options
- **Playlist Support**: To extend functionality beyond single videos