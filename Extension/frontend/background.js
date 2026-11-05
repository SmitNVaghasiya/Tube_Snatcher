// Background service worker for handling server management and downloads
let serverStatus = false;
let youtubeTabs = new Set();
let downloadQueue = [];

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

// Add API testing functionality
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'testAPI') {
        testAPI().then(result => {
            sendResponse({ success: true, data: result });
        }).catch(error => {
            sendResponse({ success: false, error: error.message });
        });
        return true; // Keep message channel open for async response
    }
});

// Function to test API from background script
async function testAPI() {
    try {
        console.log('🧪 Background script testing API...');
        const response = await fetch(getApiUrl('STATUS'));
        const data = await response.json();
        console.log('✅ Background API test successful:', data);
        return data;
    } catch (error) {
        console.error('❌ Background API test failed:', error);
        throw error;
    }
}

// Track YouTube tabs and server status
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        if (tab.url.includes('youtube.com') || tab.url.includes('youtu.be')) {
            youtubeTabs.add(tabId);
            checkServerStatus();
        }
    }
});

chrome.tabs.onRemoved.addListener((tabId) => {
    youtubeTabs.delete(tabId);
});

// Check server status for online backend
async function checkServerStatus() {
    try {
        console.log('Checking server status at:', getApiUrl('STATUS'));
        const response = await fetch(getApiUrl('STATUS'));
        if (response.ok) {
            const data = await response.json();
            console.log('Online server is accessible:', data);
            serverStatus = true;
            
            // Notify all YouTube tabs that server is ready
            notifyTabsServerReady();
            return true;
        } else {
            console.log('Server responded with status:', response.status);
        }
    } catch (error) {
        console.log('Online server not responding:', error);
        serverStatus = false;
        notifyTabsServerFailed();
        return false;
    }
    return false;
}

// Notify tabs that server is ready
function notifyTabsServerReady() {
    console.log('Notifying tabs that online server is ready...');
    youtubeTabs.forEach(tabId => {
        chrome.tabs.sendMessage(tabId, { action: 'serverReady' }).catch(() => {
            // Tab might not be ready to receive messages, ignore error
        });
    });
}

// Notify tabs that server connection failed
function notifyTabsServerFailed() {
    console.log('Notifying tabs that server connection failed...');
    youtubeTabs.forEach(tabId => {
        chrome.tabs.sendMessage(tabId, { action: 'serverFailed' }).catch(() => {
            // Tab might not be ready to receive messages, ignore error
        });
    });
}

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'openPopup') {
        // Open the popup for format selection
        chrome.action.openPopup();
    } else if (request.action === 'checkServerStatus') {
        // Check current server status
        sendResponse({status: serverStatus});
    } else if (request.action === 'getCurrentVideoInfo') {
        // Get current active YouTube tab's video info
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            const currentTab = tabs[0];
            if (currentTab && currentTab.url && (currentTab.url.includes('youtube.com/watch') || currentTab.url.includes('youtu.be'))) {
                const videoId = getVideoIdFromUrl(currentTab.url);
                if (videoId) {
                    const videoInfo = {
                        url: currentTab.url,
                        videoId: videoId,
                        title: currentTab.title || 'Unknown Title'
                    };
                    sendResponse({success: true, videoInfo: videoInfo});
                } else {
                    sendResponse({success: false, error: 'No valid YouTube video URL found'});
                }
            } else {
                sendResponse({success: false, error: 'Not on a YouTube video page'});
            }
        });
        return true; // Keep message channel open for async response
    } else if (request.action === 'addToDownloadQueue') {
        // Add download to queue
        downloadQueue.push(request.taskId);
        sendResponse({status: 'added_to_queue'});
    } else if (request.action === 'removeFromDownloadQueue') {
        // Remove download from queue
        const index = downloadQueue.indexOf(request.taskId);
        if (index > -1) {
            downloadQueue.splice(index, 1);
        }
        sendResponse({status: 'removed_from_queue'});
    }
});

// Helper function to extract video ID from YouTube URL
function getVideoIdFromUrl(url) {
    const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('Tube Snatcher Pro extension installed');
    console.log('Extension will connect to online backend server');
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
    console.log('Tube Snatcher Pro extension started');
    console.log('Checking for existing YouTube tabs...');
    
    // Check existing tabs for YouTube
    chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
            if (tab.url && (tab.url.includes('youtube.com') || tab.url.includes('youtu.be'))) {
                youtubeTabs.add(tab.id);
            }
        });
        
        if (youtubeTabs.size > 0) {
            checkServerStatus();
        }
    });
});

// Periodic server status check
setInterval(async () => {
    if (youtubeTabs.size > 0) {
        try {
            console.log('Periodic server status check...');
            const response = await fetch(getApiUrl('STATUS'));
            if (response.ok) {
                if (!serverStatus) {
                    console.log('Online server detected as accessible during periodic check');
                    serverStatus = true;
                    notifyTabsServerReady();
                }
            } else {
                if (serverStatus) {
                    console.log('Online server no longer accessible during periodic check, status:', response.status);
                    serverStatus = false;
                    notifyTabsServerFailed();
                }
            }
        } catch (error) {
            if (serverStatus) {
                console.log('Online server connection failed during periodic check:', error.message);
                serverStatus = false;
                notifyTabsServerFailed();
            }
        }
    }
}, 15000); // Check every 15 seconds for faster response
