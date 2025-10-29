# Tube Snatcher Pro - Chrome Extension

A powerful Chrome extension for downloading YouTube videos with automatic Python backend management, high-quality format selection, and intelligent server lifecycle management.

## ✨ Features

### 🚀 **Automatic Server Management**
- **Smart Startup**: Automatically starts Python backend when visiting YouTube
- **Session Tracking**: Keeps server running while YouTube tabs are active
- **Download Protection**: Prevents server shutdown during active downloads
- **Auto-Recovery**: Automatically restarts server if it goes down
- **Resource Efficient**: Only runs when needed, auto-shutdowns when idle

### 📥 **Advanced Download Capabilities**
- **Format Selection**: Choose from 360p to 1440p quality options
- **Smart Filtering**: Automatically filters suitable formats for your screen
- **Queue Management**: Download multiple videos with background processing
- **Progress Tracking**: Real-time download progress monitoring
- **Error Handling**: Comprehensive error handling with user-friendly messages

### 🎯 **User Experience**
- **Seamless Integration**: Download button appears directly on YouTube video pages
- **One-Click Download**: Simple interface with format selection popup
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Modern UI**: Clean, responsive design with smooth animations

## 🔧 Technical Architecture

### **Frontend (Chrome Extension)**
- **Content Script**: Injects download button into YouTube pages
- **Background Script**: Manages server lifecycle and download queue
- **Popup Interface**: Format selection and download management
- **Storage API**: Chrome storage for video information persistence

### **Backend (Python Server)**
- **FastAPI**: Modern, fast web framework for API endpoints
- **yt-dlp**: Latest YouTube downloader with format support
- **Async Processing**: Non-blocking download queue management
- **Auto-Shutdown**: Intelligent server lifecycle management

### **Security Features**
- **CORS Protection**: Restricted to Chrome extensions only
- **Input Validation**: Sanitized user inputs and URL validation
- **Permission Management**: Minimal required permissions for security

## 📋 Requirements

### **System Requirements**
- Python 3.7+ installed and in PATH
- Chrome/Chromium-based browser
- Windows 10+ (for VBS script support), macOS, or Linux

### **Python Dependencies**
```
yt-dlp          # YouTube video downloader
fastapi         # Web framework
uvicorn[standard] # ASGI server
python-multipart # Form data handling
```

## 🚀 Installation

### **1. Install Python Dependencies**
```bash
cd Extension/app
pip install -r requirements.txt
```

### **2. Load Extension in Chrome**
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked" and select the `Extension` folder
4. The extension icon should appear in your toolbar

### **3. First Use**
1. Visit any YouTube video page
2. Click the "Download" button that appears
3. The extension will automatically start the Python backend
4. Select your preferred video format and quality
5. Click "Download" to start the download

## 🔄 Auto-Server Management

### **How It Works**
The extension automatically manages the Python backend server:

1. **Detection**: Monitors YouTube tabs and detects when server is needed
2. **Startup**: Automatically starts server using available startup methods
3. **Maintenance**: Keeps server running while YouTube sessions are active
4. **Shutdown**: Gracefully shuts down when no longer needed

### **Startup Methods (Priority Order)**
1. **VBS Script** (`run_server_silent.vbs`) - Most reliable on Windows
2. **Batch File** (`start_server.bat`) - Alternative Windows method
3. **Python Script** (`start_server.py`) - Cross-platform method

### **Server Lifecycle**
- **Start**: When first YouTube tab is opened
- **Maintain**: While YouTube tabs are active OR downloads are in progress
- **Shutdown**: 30 seconds after last YouTube tab closes AND no active downloads

## 📁 Download Locations

### **Default Location**
Downloads are saved to: `~/Downloads/TubeSnatcher/`

### **Custom Location (Coming Soon)**
- Location picker in popup interface
- Remember user preferences
- Support for multiple download directories

## 🎨 User Interface

### **Download Button**
- Appears on YouTube video pages
- Shows server status (Download, Starting Server, Server Failed)
- Integrates seamlessly with YouTube's design

### **Format Selection Popup**
- Video thumbnail and title display
- Quality options from 360p to 1440p
- File size and format information
- Download progress tracking

### **Status Indicators**
- Server status monitoring
- Download queue position
- Progress bars and completion status
- Error messages with retry options

## 🔍 Troubleshooting

### **Common Issues**

#### **Server Won't Start**
1. Ensure Python is installed and in PATH
2. Check if dependencies are installed: `pip install -r requirements.txt`
3. Try manual startup: double-click `run_server_silent.vbs`
4. Check console for error messages

#### **Download Button Not Appearing**
1. Refresh the YouTube page
2. Check if extension is enabled in `chrome://extensions/`
3. Ensure you're on a video page (URL contains `/watch?v=`)
4. Check browser console for error messages

#### **Downloads Fail**
1. Verify server is running (`http://127.0.0.1:2004/status`)
2. Check internet connection
3. Ensure video is not age-restricted or private
4. Try different quality formats

### **Manual Server Management**
If automatic startup fails:

1. **Windows (Recommended)**:
   ```
   Double-click: Extension\run_server_silent.vbs
   ```

2. **Alternative Methods**:
   ```bash
   # From Extension folder
   python start_server.py
   
   # Or from Extension/app folder
   cd app
   python -m uvicorn main:app --host 127.0.0.1 --port 2004
   ```

## 🚧 Development

### **Project Structure**
```
Extension/
├── app/                    # Python backend
│   ├── main.py           # FastAPI application
│   ├── video_downloader.py # Download logic
│   ├── details_fetcher.py # Video info extraction
│   └── requirements.txt   # Python dependencies
├── popup.html             # Extension popup interface
├── popup.js               # Popup functionality
├── popup.css              # Popup styling
├── content.js             # YouTube page integration
├── background.js          # Server management
├── manifest.json          # Extension configuration
├── start_server.py        # Server launcher
├── run_server_silent.vbs  # Windows VBS launcher
└── start_server.bat       # Windows batch launcher
```

### **Key Components**
- **Background Script**: Manages server lifecycle and download queue
- **Content Script**: Injects download button and handles YouTube integration
- **Popup Interface**: Format selection and download management
- **Python Backend**: Video processing and download execution

## 📈 Recent Improvements

### **v1.0 - Major Overhaul**
- ✅ **Auto-Server Management**: Automatic startup/shutdown based on usage
- ✅ **Smart Session Tracking**: Keeps server running while needed
- ✅ **Enhanced Error Handling**: Better user feedback and error recovery
- ✅ **Code Optimization**: Removed duplicate code and unnecessary complexity
- ✅ **Security Improvements**: CORS protection and input validation
- ✅ **Performance**: Efficient polling and resource management
- ✅ **User Experience**: Seamless integration and modern UI

### **Removed Unnecessary Features**
- ❌ Web app templates and static files
- ❌ Duplicate styling and CSS rules
- ❌ Unused dependencies (jinja2, aiofiles, requests)
- ❌ Complex path resolution logic
- ❌ Streaming response handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **yt-dlp**: For excellent YouTube downloading capabilities
- **FastAPI**: For the modern, fast web framework
- **Chrome Extensions API**: For the powerful browser integration

---

**Note**: This extension requires a Python backend to function. The extension automatically manages the backend server lifecycle for a seamless user experience.
