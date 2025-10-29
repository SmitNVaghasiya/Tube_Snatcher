// Test Content Script for Tube Snatcher
// This script injects a test button into YouTube pages

console.log('🧪 Tube Snatcher Test Content Script loaded');

let testButton = null;

// Function to create and inject the test button
function createTestButton() {
    if (testButton) return; // Button already exists
    
    // Look for the action bar where we can add our button
    const actionBar = document.querySelector('#actions-inner') || 
                     document.querySelector('#top-level-buttons-computed') ||
                     document.querySelector('#actions');
    
    if (!actionBar) {
        console.log('Action bar not found, retrying in 1 second...');
        setTimeout(createTestButton, 1000);
        return;
    }
    
    // Create the test button
    testButton = document.createElement('button');
    testButton.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>Test Button</span>
    `;
    
    // Style the button to match YouTube's design
    testButton.className = 'yt-spec-button-shape-next yt-spec-button-shape-next--button-text-content yt-spec-button-shape-next--size-m yt-spec-button-shape-next--style-text';
    testButton.style.cssText = `
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
    
    // Add hover effect
    testButton.addEventListener('mouseenter', () => {
        testButton.style.background = '#404040';
    });
    
    testButton.addEventListener('mouseleave', () => {
        testButton.style.background = '#2b2b2b';
    });
    
    // Add click handler
    testButton.addEventListener('click', handleTestClick);
    
    // Insert the button into the action bar
    actionBar.appendChild(testButton);
    
    console.log('✅ Test button injected successfully');
}

// Function to handle test button click
async function handleTestClick() {
    if (!testButton) return;

    const originalText = testButton.innerHTML;

    try {
        // Disable button and show loading state
        testButton.disabled = true;
        testButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="animate-spin">
                <path d="M12 4V2A10 10 0 002 12h2a8 8 0 018-8z"/>
            </svg>
            <span>Starting...</span>
        `;

        // 1. Tell the background script to start the server
        console.log('🚀 Requesting server start...');
        await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({ action: 'startServer' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('Error sending startServer message:', chrome.runtime.lastError.message);
                    return reject(new Error(chrome.runtime.lastError.message));
                }
                console.log('✅ Server start request sent.');
                resolve();
            });
        });

        // 2. Wait for the server to initialize
        testButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 6v6l4 2"/>
            </svg>
            <span>Testing...</span>
        `;
        console.log('⏳ Waiting for server to initialize (3 seconds)...');
        await new Promise(resolve => setTimeout(resolve, 3000));

        // 3. Call the API endpoint through the background script
        console.log('🌐 Making API request through background script...');
        const result = await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({ action: 'testAPI' }, (response) => {
                if (chrome.runtime.lastError) {
                    return reject(new Error(chrome.runtime.lastError.message));
                }
                if (response && response.success) {
                    resolve(response.data);
                } else {
                    reject(new Error(response?.error || 'API request failed'));
                }
            });
        });

        console.log('✅ API Response:', result);

        // Show success state
        testButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>Success!</span>
        `;
        testButton.style.background = '#28a745';

    } catch (error) {
        console.error('❌ API Test Failed:', error);

        // Show error state
        testButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
            <span>Failed!</span>
        `;
        testButton.style.background = '#dc3545';
        showErrorDetails(error);

    } finally {
        // Reset button after a delay
        setTimeout(() => {
            testButton.innerHTML = originalText;
            testButton.style.background = '#2b2b2b';
            testButton.disabled = false;
            hideErrorDetails();
        }, 5000);
    }
}

// Function to check if we're on a YouTube video page
function isYouTubeVideoPage() {
    return window.location.hostname.includes('youtube.com') && 
           window.location.pathname === '/watch' &&
           window.location.search.includes('v=');
}

// Function to initialize the test button
function initTestButton() {
    if (isYouTubeVideoPage()) {
        console.log('🎥 YouTube video page detected, creating test button...');
        createTestButton();
    } else {
        console.log('❌ Not a YouTube video page');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTestButton);
} else {
    initTestButton();
}

// Also listen for navigation changes (YouTube is a SPA)
let currentUrl = window.location.href;
const observer = new MutationObserver(() => {
    if (window.location.href !== currentUrl) {
        currentUrl = window.location.href;
        console.log('🔄 URL changed, reinitializing...');
        
        // Remove existing button
        if (testButton) {
            testButton.remove();
            testButton = null;
        }
        
        // Wait a bit for YouTube to finish loading, then create new button
        setTimeout(initTestButton, 1000);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Function to show error details below the button
function showErrorDetails(error) {
    // Remove existing error display
    hideErrorDetails();
    
    // Create error container
    const errorContainer = document.createElement('div');
    errorContainer.id = 'test-error-display';
    errorContainer.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: #dc3545;
        color: white;
        padding: 15px;
        border-radius: 8px;
        max-width: 400px;
        z-index: 10000;
        font-family: Arial, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 2px solid #c82333;
    `;
    
    // Create error content
    errorContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <strong>❌ API Test Failed</strong>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
        </div>
        <div style="margin-bottom: 8px;">
            <strong>Error:</strong> ${error.message}
        </div>
        <div style="margin-bottom: 8px;">
            <strong>Type:</strong> ${error.name || 'Unknown'}
        </div>
        ${error.stack ? `<div style="margin-bottom: 8px;">
            <strong>Stack:</strong> 
            <pre style="background: rgba(0,0,0,0.2); padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; margin: 5px 0;">${error.stack}</pre>
        </div>` : ''}
        <div style="font-size: 12px; opacity: 0.8;">
            This error display will auto-hide in 5 seconds
        </div>
    `;
    
    // Add to page
    document.body.appendChild(errorContainer);
}

// Function to hide error details
function hideErrorDetails() {
    const existingError = document.getElementById('test-error-display');
    if (existingError) {
        existingError.remove();
    }
}

// Debug function - you can call this from browser console
window.testTubeSnatcherAPI = async function() {
    console.log('🧪 Manual API test started...');
    try {
        const response = await fetch('http://127.0.0.1:2004/api/v1/status');
        const data = await response.json();
        console.log('✅ Manual test successful:', data);
        return data;
    } catch (error) {
        console.error('❌ Manual test failed:', error);
        return error;
    }
};

// Debug function - test basic connectivity
window.testTubeSnatcherConnectivity = async function() {
    console.log('🔍 Testing basic connectivity...');
    try {
        const response = await fetch('http://127.0.0.1:2004/');
        console.log('✅ Connectivity test successful:', response.status, response.statusText);
        return response.status;
    } catch (error) {
        console.error('❌ Connectivity test failed:', error);
        return error;
    }
};

console.log('🧪 Test Content Script initialization complete');
console.log('💡 Debug functions available:');
console.log('   - testTubeSnatcherAPI() - Test the status API');
console.log('   - testTubeSnatcherConnectivity() - Test basic connectivity');
