# TubeSnatcher Extension Frontend

## Overview
TubeSnatcher Extension is a Chrome extension that provides secure YouTube video downloads through an authenticated backend service. The extension automatically extracts YouTube cookies, manages authentication tokens, and handles video downloading through a secure online backend.

## Features

### Core Features
- **Automatic Cookie Extraction**: Extracts YouTube authentication cookies automatically
- **JWT Authentication**: Secure token-based communication with backend
- **Format Selection**: Choose from various video/audio formats and qualities
- **Playlist Support**: Download entire playlists or individual videos
- **Audio Downloads**: Extract MP3 audio from videos
- **Download Location**: Choose custom download locations (default: Downloads folder)
- **Progress Tracking**: Real-time download progress monitoring
- **Analytics Integration**: Tracks usage patterns and download history

### Security Features
- **Token Management**: Automatic JWT token handling and refresh
- **Secure Cookie Transmission**: Encrypted cookie transfer to backend
- **Origin Verification**: Ensures communication only with authorized backend
- **Local Storage Protection**: Secure storage of authentication tokens

### User Interface Features
- **Modern UI**: Clean, intuitive popup interface
- **Format Preview**: Shows available formats with quality indicators
- **Progress Visualization**: Visual progress bars and percentage tracking
- **Error Handling**: Clear error messages and troubleshooting guidance
- **Responsive Design**: Works on various screen sizes

## Architecture

### Main Components
- **content.js**: Injects download button on YouTube pages
- **popup.js**: Handles user interface and download selection
- **background.js**: Manages server connectivity and download queue
- **config.js**: Centralized API configuration
- **popup.html/css**: User interface components

### Tech Stack
- **Chrome Extension APIs**: For browser integration
- **YouTube Cookie Access**: chrome.cookies API for authentication
- **JWT Authentication**: Secure token-based access
- **Fetch API**: For backend communication

## Configuration

### Backend URL Configuration
Update the `BACKEND_URL` in `config.js` to point to your deployed backend:
```javascript
const CONFIG = {
    BACKEND_URL: 'https://your-deployment-url.onrender.com',  // Update this!
    // ... other config
};
```

### Manifest Permissions
- `activeTab`: Access to current tab information
- `storage`: Persistent token and settings storage
- `tabs`: Tab management capabilities
- `cookies`: Access to YouTube authentication cookies
- Host permissions for YouTube and backend domains

## Security Considerations
- Never share authentication tokens
- Use HTTPS backend connections only
- Regularly rotate backend security keys
- Monitor for unauthorized access attempts
- Keep extension updated with latest security patches

## Usage Workflow
1. Navigate to YouTube video
2. Click "Download" button (appears automatically)
3. Extension connects to backend and gets authentication token
4. Automatic extraction of YouTube cookies
5. Shows available formats and quality options
6. Select desired format and download location
7. Backend processes download and returns to user
8. Download appears in selected location

## Why These Features Were Added
- **Cookie Extraction**: YouTube requires authentication for many videos
- **JWT Tokens**: Prevent unauthorized API access and track usage
- **Format Selection**: Provide flexibility in download options
- **Playlist Support**: Extend functionality beyond single videos
- **Progress Tracking**: Provide user feedback during downloads
- **Security**: Protect user credentials and prevent abuse
- **Analytics**: Understand usage patterns and improve service
- **Custom Locations**: Give users control over download destinations
- **Audio Extraction**: Provide MP3 download option for audio content