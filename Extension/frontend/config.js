// config.js - Configuration for TubeSnatcher Extension
// Update this with your deployed backend URL when deploying

const CONFIG = {
    // Backend server URL - update this when deploying to production
    BACKEND_URL: 'http://localhost:2004',  // Change to your actual deployed URL
    
    // API endpoints
    ENDPOINTS: {
        AUTH_TOKEN: '/api/v1/auth/get-token',
        VERIFY_TOKEN: '/api/v1/auth/verify-token',
        FETCH_DETAILS: '/api/v1/fetch-details-with-cookies',
        DOWNLOAD: '/api/v1/download-with-cookies',
        LOCATIONS: '/api/v1/download-locations',
        HISTORY: '/api/v1/history',
        STATUS: '/api/v1/status'
    }
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return CONFIG.BACKEND_URL + CONFIG.ENDPOINTS[endpoint];
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, getApiUrl };
}