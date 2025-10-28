// Content script that runs on YouTube pages
let downloadButton = null;
let videoInfo = null;
let serverReady = false;
let serverCheckInProgress = false;

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

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'serverReady') {
        serverReady = true;
        console.log('Server is ready!');
        if (downloadButton) {
            setButtonState('Download', false);
        }
    } else if (request.action === 'serverFailed') {
        serverReady = false;
        console.log('Server connection failed');
        if (downloadButton) {
            setButtonState('Connection Failed', true);
            showServerConnectionInstructions();
        }
    }
});

// Function to check if backend server is running
async function checkServerStatus() {
    try {
        const response = await fetch(getApiUrl('STATUS'));
        if (response.ok) {
            const data = await response.json();
            console.log('Server status response:', data);
            return true;
        }
    } catch (error) {
        console.log('Server not responding:', error);
        return false;
    }
    return false;
}

// Function to extract video information from YouTube page
function extractVideoInfo() {
    const videoId = new URLSearchParams(window.location.search).get('v');
    if (!videoId) return null;
    
    const title = document.querySelector('h1.ytd-video-primary-info-renderer')?.textContent?.trim() || 
                  document.querySelector('h1.title')?.textContent?.trim() || 
                  'Unknown Title';
    
    const thumbnail = document.querySelector('meta[property="og:image"]')?.content || 
                     `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
    
    return {
        videoId,
        title,
        thumbnail,
        url: `https://www.youtube.com/watch?v=${videoId}`
    };
}

// Function to create download button
function createDownloadButton() {
    if (downloadButton) return;
    
    // Look for the action bar where we can add our button
    const actionBar = document.querySelector('#actions-inner') || 
                     document.querySelector('#top-level-buttons-computed') ||
                     document.querySelector('#actions');
    
    if (!actionBar) return;
    
    downloadButton = document.createElement('button');
    downloadButton.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <span>Download</span>
    `;
    downloadButton.className = 'yt-spec-button-shape-next yt-spec-button-shape-next--button-text-content yt-spec-button-shape-next--size-m yt-spec-button-shape-next--style-text';
    downloadButton.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        margin-left: 8px;
        background: #2b2b2b;
        color: white;
        border: none;
        border-radius: 18px;
        padding: 10px 16px;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.2s;
    `;
    
    downloadButton.addEventListener('click', handleDownload);
    downloadButton.addEventListener('mouseenter', () => {
        downloadButton.style.background = '#404040';
    });
    downloadButton.addEventListener('mouseleave', () => {
        downloadButton.style.background = '#2b2b2b';
    });
    
    // Add right-click context menu for manual refresh
    downloadButton.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        refreshButtonState();
    });
    
    actionBar.appendChild(downloadButton);
    
    // Check server status when button is created
    checkAndUpdateButtonState();
}

// Function to handle download
async function handleDownload() {
    if (!videoInfo) {
        videoInfo = extractVideoInfo();
        if (!videoInfo) {
            showError('Could not extract video information. Please refresh the page.');
            return;
        }
    }
    
    try {
        setButtonState('Starting...', true);
        
        // Check if server is running
        if (!await checkServerStatus()) {
            setButtonState('Starting Server...', true);
            
            // Request background script to start server
            chrome.runtime.sendMessage({ action: 'startServer' }, async (response) => {
                if (response && response.status === 'starting_server') {
                    // Wait for server to start
                    await waitForServer();
                    
                    if (await checkServerStatus()) {
                        serverReady = true;
                        proceedWithDownload();
                    } else {
                        setButtonState('Connection Failed', true);
                        showServerConnectionInstructions();
                    }
                } else {
                    setButtonState('Connection Failed', true);
                    showServerConnectionInstructions();
                }
            });
            return;
        }
        
        // Server is running, proceed with download
        serverReady = true;
        proceedWithDownload();
        
    } catch (error) {
        console.error('Download failed:', error);
        showError(`Download failed: ${error.message}`);
        setButtonState('Download', false);
    }
}

// Wait for server to start
async function waitForServer() {
    let attempts = 0;
    const maxAttempts = 30; // Wait up to 30 seconds
    
    while (attempts < maxAttempts) {
        if (await checkServerStatus()) {
            return true;
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
        
        // Update button text to show progress
        if (downloadButton) {
            setButtonState(`Starting Server... (${attempts}s)`, true);
        }
    }
    
    return false;
}

// Proceed with download after server is ready
function proceedWithDownload() {
    // Store video info for popup
    chrome.storage.local.set({
        currentVideo: videoInfo
    });
    
    // Open popup for format selection
    chrome.runtime.sendMessage({
        action: 'openPopup'
    });
    
    setButtonState('Download', false);
}

function setButtonState(text, disabled) {
    if (!downloadButton) return;
    
    downloadButton.disabled = disabled;
    downloadButton.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        <span>${text}</span>
    `;
}

// Manual refresh button state
async function refreshButtonState() {
    console.log('Manual refresh of button state requested');
    if (downloadButton) {
        setButtonState('Checking...', true);
        await checkAndUpdateButtonState();
    }
}

function showServerConnectionInstructions() {
    const message = `Unable to connect to the TubeSnatcher backend server.\n\n` +
                   `This could be due to:\n` +
                   `1. The server is not running or temporarily down\n` +
                   `2. Network connectivity issues\n` +
                   `3. Server authentication problems\n\n` +
                   `Please check if your backend server is accessible and try again.`;
    alert(message);
}

function showError(message) {
    console.error('Tube Snatcher Error:', message);
}

// Check and update button state based on server status
async function checkAndUpdateButtonState() {
    if (downloadButton && !serverCheckInProgress) {
        serverCheckInProgress = true;
        
        try {
            if (await checkServerStatus()) {
                serverReady = true;
                setButtonState('Download', false);
                console.log('Server is already running, button set to Download');
            } else {
                serverReady = false;
                setButtonState('Server Starting...', true);
                console.log('Server not running, requesting start...');
                // Request server start
                chrome.runtime.sendMessage({ action: 'startServer' });
            }
        } catch (error) {
            console.error('Error checking server status:', error);
            setButtonState('Server Starting...', true);
        } finally {
            serverCheckInProgress = false;
        }
    }
}

// Function to check if we're on a video page
function isVideoPage() {
    return window.location.pathname === '/watch' && 
           new URLSearchParams(window.location.search).has('v');
}

// Function to remove download button
function removeDownloadButton() {
    if (downloadButton) {
        downloadButton.remove();
        downloadButton = null;
    }
}

// Main function to initialize the extension
function init() {
    // Wait for YouTube to load and attach when on a video
    const checkInterval = setInterval(() => {
        if (!isVideoPage()) { return; }
        if (document.querySelector('#actions-inner') || 
            document.querySelector('#top-level-buttons-computed') ||
            document.querySelector('#actions')) {
            clearInterval(checkInterval);
            createDownloadButton();
        }
    }, 1000);
    
    // Also try to create button when page changes
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            if (isVideoPage()) {
                setTimeout(createDownloadButton, 1000);
            } else {
                removeDownloadButton();
            }
        }
    }).observe(document, {subtree: true, childList: true});
}

// Start the extension
init();
