# Video Downloader - Tube Snatcher

Tube Snatcher is a powerful tool that allows users to download audio and videos from YouTube at the highest resolution for free.

![Screenshot 2025-04-27 175035](https://github.com/user-attachments/assets/4183db2c-c86a-4408-8863-7edcf6468b30)


## Features

- Download YouTube videos in the **best available quality**
- Extract audio in **MP3 format**
- Supports multiple resolutions and formats
- Uses **yt-dlp** for efficient downloading
- Works with **proxy servers** and **YouTube cookies** for bypassing restrictions

## How It Works

This project is built using **Python** and **Flask** on the backend. The frontend is a simple web interface where users can:

1. **Enter a YouTube URL**
2. **Select the format** (MP3 or MP4)
3. **Choose resolution** (for MP4 downloads)
4. **Click the download button**

The backend uses **yt-dlp** to fetch video details and download the requested media.

### **Why Proxy or Cookies Are Needed?**

YouTube has strict anti-bot measures, making it difficult to download videos directly from a server. To bypass this:

- **Proxy servers** can be used to change the request origin.
- **YouTube cookies** allow authenticated access to restricted content.

⚠️ **Note:** Due to YouTube's cookie policy, cookies expire quickly, making it difficult to host this on a permanent server.

## Installation & Usage

1. **Clone the Repository**
   ```sh
   git clone https://github.com/your-repo/video-downloader.git
   cd video-downloader
   ```
2. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the Server**
   ```sh
   python app.py
   ```
4. **Access the Web Interface**
   Open `http://127.0.0.1:8000` in your browser.

## Deployment Notes

- Deploying on a server like **Render** or **Vercel** may require handling **proxy settings** or **YouTube cookies**.
- A proxy list can be used for authentication, but success is not always guaranteed.
- If using **cookies.txt**, make sure to extract them in an **incognito browser** to extend their validity.

## Disclaimer

This tool is meant for **educational purposes only**. Downloading copyrighted content without permission is illegal.

## Future Improvements

- Implement **OAuth login** for a more stable authentication method.
- Improve **proxy rotation** for better uptime.
- Explore **PO Tokens** for bypassing YouTube restrictions.

---

Feel free to contribute and suggest improvements! 🚀
