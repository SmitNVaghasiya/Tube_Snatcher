# Tube Snatcher Pro - Setup Guide

## 🚀 Quick Installation

### Step 1: Install Python Dependencies
```bash
cd "Backend"
python -m venv venv
venv/Scripts/Activate
pip install -r requirements.txt
```

### Step 2: Install Chrome Extension
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select this Extension folder
5. Done! 🎉

## 🎥 How It Works

1. **Go to any YouTube video**
2. **Click the dark download button** (appears automatically)
3. **Make sure the Python backend is running** (`cd backend && python main.py`)
4. **Select your preferred quality** (360p to 1440p)
5. **Download begins automatically** with real progress tracking
6. **Server shuts down** when all downloads complete

## 🔧 Features

- ✅ **Local backend** - start it once with `python main.py`; it keeps running until you stop it
- ✅ **High-quality downloads** - uses yt-dlp for best available quality
- ✅ **Download queue** - handle multiple videos efficiently
- ✅ **Real progress tracking** - see status in browser
- ✅ **Quality filtering** - optimized for 1920x1080 screens

## 📁 Extension Files

- `content.js` - Adds download button and manages server
- `popup.js` - Quality selection and progress tracking
- `popup.html` - User interface
- `run_server_silent.vbs` - Starts the Python server without a console window (Windows)
- `requirements.txt` - Python dependencies

## ⚠️ Troubleshooting

### Extension not working:
- Make sure Python dependencies are installed
- Check if port 2004 is available
- Start the backend manually: `cd backend && python main.py`

### Downloads not starting:
- Check browser console for errors
- Verify Python server is running on port 2004
- Check if yt-dlp is properly installed

## 🎯 Usage

1. **Install extension** (one-time setup)
2. **Browse YouTube** normally
3. **Click download button** on any video
4. **Select quality** and download
5. **Monitor progress** in popup
6. **Server manages itself** - no cleanup needed!

---

**That's it!** The extension now works intelligently with a Python backend that manages itself. 🚀
