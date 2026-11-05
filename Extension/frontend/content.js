// Content script that runs on YouTube pages
// This script helps with video information extraction for the popup interface

// Configuration
const CONFIG = {
    BACKEND_URL: 'http://localhost:2004',  // Update this to your deployed URL
    ENDPOINTS: {
        STATUS: '/api/v1/status'
    }
};

function getApiUrl(endpoint) {
    return CONFIG.BACKEND_URL + CONFIG.ENDPOINTS[endpoint];
}

console.log('Tube Snatcher Pro: content script initialized on', location.href);

// Function to extract video information from YouTube page
function extractVideoInfo() {
    const videoId = new URLSearchParams(window.location.search).get('v');
    if (!videoId) return null;
    
    // Try to get video title from multiple possible selectors
    const titleElement = document.querySelector('h1.ytd-video-primary-info-renderer #video-title') ||
                        document.querySelector('h1.ytd-video-primary-info-renderer') ||
                        document.querySelector('#title yt-formatted-string') ||
                        document.querySelector('#video-title');
    
    const title = titleElement?.textContent?.trim() || 'Unknown Title';
    
    // Try to get thumbnail from meta tags
    const thumbnail = document.querySelector('meta[property="og:image"]')?.content || 
                     `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
    
    return {
        videoId,
        title,
        thumbnail,
        url: window.location.href
    };
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoInfo') {
        const videoInfo = extractVideoInfo();
        if (videoInfo) {
            sendResponse({ success: true, videoInfo: videoInfo });
        } else {
            sendResponse({ success: false, error: 'Could not extract video information' });
        }
    }
});

// Monitor for changes to the page that might affect video information
let currentVideoId = null;
let lastUrl = location.href;

// Function to check if we're on a video page
function isVideoPage() {
    return window.location.pathname === '/watch' && 
           new URLSearchParams(window.location.search).has('v');
}

// Monitor URL changes and update stored video info if needed
new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
        lastUrl = url;
        if (isVideoPage()) {
            // Video page changed, update video info in storage
            const videoInfo = extractVideoInfo();
            if (videoInfo) {
                chrome.storage.local.set({ currentVideo: videoInfo });
            }
        }
    }
}).observe(document, { subtree: true, childList: true });

// Initial setup when content script loads
if (isVideoPage()) {
    const videoInfo = extractVideoInfo();
    if (videoInfo) {
        chrome.storage.local.set({ currentVideo: videoInfo });
    }
}
