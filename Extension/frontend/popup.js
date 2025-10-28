// Popup script for handling user interactions
// Import configuration
const CONFIG = {
    BACKEND_URL: 'http://localhost:2004',  // Update this to your deployed URL
    ENDPOINTS: {
        AUTH_TOKEN: '/api/v1/auth/get-token',
        VERIFY_TOKEN: '/api/v1/auth/verify-token',
        FETCH_DETAILS: '/api/v1/fetch-details-with-cookies',
        DOWNLOAD: '/api/v1/download-with-cookies',
        DOWNLOAD_PLAYLIST: '/api/v1/download-playlist',
        LOCATIONS: '/api/v1/download-locations',
        HISTORY: '/api/v1/history',
        STATUS: '/api/v1/status'
    }
};

function getApiUrl(endpoint) {
    return CONFIG.BACKEND_URL + CONFIG.ENDPOINTS[endpoint];
}

document.addEventListener('DOMContentLoaded', async function() {
    // Get DOM elements
    const status = document.getElementById('status');
    const videoInfo = document.getElementById('videoInfo');
    const thumbnail = document.getElementById('thumbnail');
    const videoTitle = document.getElementById('videoTitle');
    const videoDuration = document.getElementById('videoDuration');
    const playlistInfo = document.getElementById('playlistInfo');
    const playlistTitle = document.getElementById('playlistTitle');
    const playlistCount = document.getElementById('playlistCount');
    const playlistVideos = document.getElementById('playlistVideos');
    const formatSelection = document.getElementById('formatSelection');
    const formatType = document.getElementById('formatType');
    const contentTypeSelector = document.getElementById('contentTypeSelector');
    const videoOnly = document.getElementById('videoOnly');
    const playlistAll = document.getElementById('playlistAll');
    const formats = document.getElementById('formats');
    const downloadLocation = document.getElementById('downloadLocation');
    const downloadSection = document.getElementById('downloadSection');
    const downloadBtn = document.getElementById('downloadBtn');
    const progress = document.getElementById('progress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    const retryBtn = document.getElementById('retryBtn');
    const queueStatus = document.getElementById('queueStatus');
    
    // Download location elements
    const defaultLocation = document.getElementById('defaultLocation');
    const customLocation = document.getElementById('customLocation');
    const customPathInput = document.getElementById('customPathInput');
    const customPath = document.getElementById('customPath');
    const browseBtn = document.getElementById('browseBtn');

    let selectedFormat = null;
    let selectedLocation = 'default';
    let selectedFormatType = 'mp4'; // 'mp4' or 'mp3'
    let selectedContentType = 'video'; // 'video' or 'playlist'
    let currentVideo = null;
    let currentPlaylist = null;
    let downloadTaskId = null;
    let progressInterval = null;
    let authToken = null;

    // Initialize popup
    await init();
    
    // Add new feature: Download location selector
    await loadDownloadLocations();
    
    // Add new feature: History display
    await loadDownloadHistory();

    async function init() {
        // Get current video info from storage
        const result = await chrome.storage.local.get(['currentVideo']);
        if (result.currentVideo) {
            currentVideo = result.currentVideo;
            displayVideoInfo(currentVideo);
            
            // Check if it's a playlist URL
            if (currentVideo.url.includes('list=')) {
                await fetchPlaylistDetails(currentVideo.url);
            } else {
                // Get authentication token first
                await ensureAuthToken();
                
                // Then fetch video formats
                await fetchVideoFormats(currentVideo.url);
            }
            
            showSection(formatSelection);
            showSection(downloadLocation);
            showSection(downloadSection);
            status.textContent = 'Ready to download';
        } else {
            status.textContent = 'No video selected. Go to a YouTube video page and click the Download button.';
        }

        // Add event listeners
        downloadBtn.addEventListener('click', handleDownload);
        retryBtn.addEventListener('click', init);
        
        // Format type selector
        formatType.addEventListener('change', handleFormatTypeChange);
        
        // Content type selector
        videoOnly.addEventListener('change', handleContentTypeChange);
        playlistAll.addEventListener('change', handleContentTypeChange);
        
        // Download location event listeners
        defaultLocation.addEventListener('change', handleLocationChange);
        customLocation.addEventListener('change', handleLocationChange);
        browseBtn.addEventListener('click', handleBrowseClick);
        
        // Load saved location preference
        await loadLocationPreference();
    }

    function displayVideoInfo(video) {
        thumbnail.src = video.thumbnail;
        videoTitle.textContent = video.title;
        videoDuration.textContent = 'Duration: Loading...';
        showSection(videoInfo);
    }

    // Display playlist info
    function displayPlaylistInfo(playlist) {
        playlistTitle.textContent = playlist.title;
        playlistCount.textContent = `${playlist.video_count} videos`;
        
        // Display playlist videos
        playlistVideos.innerHTML = '';
        playlist.videos.forEach((video, index) => {
            const videoElement = document.createElement('div');
            videoElement.className = 'playlist-video-item';
            videoElement.innerHTML = `
                <div class="video-index">${index + 1}.</div>
                <div class="video-title">${video.title}</div>
                <div class="video-duration">${formatDuration(video.duration)}</div>
            `;
            playlistVideos.appendChild(videoElement);
        });
        
        showSection(playlistInfo);
        showSection(contentTypeSelector); // Show content type selector for playlists
    }
    
    function formatDuration(seconds) {
        if (!seconds) return '';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    // Get or create authentication token
    async function ensureAuthToken() {
        const storedToken = await chrome.storage.local.get(['authToken']);
        
        if (storedToken.authToken) {
            authToken = storedToken.authToken;
            // Verify token is still valid
            if (await verifyToken(authToken)) {
                return authToken;
            }
        }
        
        // If no valid token exists, get a new one
        return await getNewToken();
    }

    // Get a new authentication token
    async function getNewToken() {
        try {
            const response = await fetch(getApiUrl('AUTH_TOKEN'), {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get token: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            authToken = data.access_token;
            
            // Store the token
            await chrome.storage.local.set({ authToken: authToken });
            
            return authToken;
        } catch (error) {
            console.error('Error getting auth token:', error);
            throw new Error('Failed to authenticate with backend server');
        }
    }

    // Verify if token is still valid
    async function verifyToken(token) {
        try {
            const response = await fetch(getApiUrl('VERIFY_TOKEN'), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Handle format type changes (mp4/mp3)
    function handleFormatTypeChange() {
        selectedFormatType = formatType.value;
        // For audio, we might want to update the format options
        if (selectedFormatType === 'mp3') {
            // Update format display for audio
            const formatOptions = document.querySelectorAll('.format-option');
            formatOptions.forEach(option => {
                const formatId = option.querySelector('input').value;
                option.querySelector('.format-quality').textContent = 'Audio Only';
                option.querySelector('.format-details').textContent = 'MP3 Format';
            });
        } else {
            // Refresh video formats
            fetchVideoFormats(currentVideo.url);
        }
    }

    // Handle content type changes (video/playlist)
    function handleContentTypeChange() {
        selectedContentType = document.querySelector('input[name="contentType"]:checked').value;
        
        if (selectedContentType === 'playlist') {
            // For playlists, we need to update the UI
            formats.innerHTML = '<p>Playlist will download all videos in selected format</p>';
        } else {
            // For single video, fetch and display formats
            fetchVideoFormats(currentVideo.url);
        }
    }

    // Handle download location changes
    function handleLocationChange() {
        if (defaultLocation.checked) {
            selectedLocation = 'default';
            customPathInput.style.display = 'none';
        } else if (customLocation.checked) {
            selectedLocation = 'custom';
            customPathInput.style.display = 'block';
            customPath.focus();
        }
        
        // Save location preference
        saveLocationPreference();
    }

    // Handle browse button click
    function handleBrowseClick() {
        // Note: Chrome extensions cannot directly open file picker
        // This is a placeholder for future implementation
        customPath.focus();
        customPath.select();
        
        // Show helpful message
        alert('Please enter the full path to your desired download folder.\n\nExample paths:\nWindows: C:\\Videos\\YouTube\nmacOS: /Users/username/Videos/YouTube\nLinux: /home/username/Videos/YouTube');
    }

    // Load saved location preference
    async function loadLocationPreference() {
        const result = await chrome.storage.local.get(['downloadLocation']);
        if (result.downloadLocation) {
            selectedLocation = result.downloadLocation.type;
            if (selectedLocation === 'custom' && result.downloadLocation.path) {
                customPath.value = result.downloadLocation.path;
                customLocation.checked = true;
                customPathInput.style.display = 'block';
            } else {
                defaultLocation.checked = true;
            }
        }
    }

    // Save location preference
    async function saveLocationPreference() {
        const locationData = {
            type: selectedLocation,
            path: selectedLocation === 'custom' ? customPath.value : null
        };
        await chrome.storage.local.set({ downloadLocation: locationData });
    }

    // Extract cookies from browser for the current YouTube session
    async function extractYouTubeCookies() {
        try {
            // Get all YouTube cookies
            const cookies = await chrome.cookies.getAll({
                domain: '.youtube.com'
            });
            
            const wwwCookies = await chrome.cookies.getAll({
                domain: 'www.youtube.com'
            });
            
            // Merge and deduplicate
            const allCookies = [...cookies, ...wwwCookies];
            const uniqueCookies = Array.from(
                new Map(allCookies.map(c => [c.name, c])).values()
            );
            
            if (uniqueCookies.length === 0) {
                throw new Error('No YouTube cookies found. Please ensure you are logged in to YouTube.');
            }
            
            // Convert to Netscape format for yt-dlp
            const cookieString = uniqueCookies.map(cookie => {
                return [
                    cookie.domain.startsWith('.') ? cookie.domain : '.' + cookie.domain,
                    cookie.hostOnly ? 'FALSE' : 'TRUE',
                    cookie.path,
                    cookie.secure ? 'TRUE' : 'FALSE',
                    cookie.expirationDate ? Math.floor(cookie.expirationDate) : '0',
                    cookie.name,
                    cookie.value
                ].join('\t');
            }).join('\n');
            
            return cookieString;
            
        } catch (error) {
            console.error('Error extracting cookies:', error);
            throw new Error('Failed to extract YouTube cookies. Please ensure you are logged in to YouTube.');
        }
    }

    // Fetch video formats using cookies
    async function fetchVideoFormats(url) {
        try {
            status.textContent = 'Fetching video formats...';
            
            // Extract cookies
            const cookies = await extractYouTubeCookies();
            
            // Prepare request data
            const requestData = {
                url: url,
                format_type: selectedFormatType,
                cookies: cookies
            };
            
            const response = await fetch(getApiUrl('FETCH_DETAILS'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Check if it's a playlist
            if (data.type === 'playlist') {
                currentPlaylist = data;
                displayPlaylistInfo(data);
            } else {
                // Display formats
                displayFormats(data.formats || []);
            }
            
            status.textContent = 'Ready to download';
            
        } catch (error) {
            console.error('Failed to fetch formats:', error);
            const errorMsg = error.message.includes('fetch') || error.message.includes('token') ? 
                'Server connection failed. Please check your server is running and accessible.' : 
                error.message;
            status.textContent = 'Failed to fetch video formats';
            showError(errorMsg);
        }
    }

    // Fetch playlist details
    async function fetchPlaylistDetails(url) {
        try {
            status.textContent = 'Fetching playlist details...';
            
            // Extract cookies
            const cookies = await extractYouTubeCookies();
            
            // Prepare request data
            const requestData = {
                url: url,
                format_type: selectedFormatType,
                cookies: cookies
            };
            
            const response = await fetch(getApiUrl('FETCH_DETAILS'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.type === 'playlist') {
                currentPlaylist = data;
                displayPlaylistInfo(data);
                status.textContent = 'Ready to download';
            } else {
                // If it's not a playlist, treat as single video
                currentVideo = data;
                displayVideoInfo(currentVideo);
                displayFormats(data.formats || []);
                status.textContent = 'Ready to download';
            }
            
        } catch (error) {
            console.error('Failed to fetch playlist details:', error);
            const errorMsg = error.message.includes('fetch') || error.message.includes('token') ? 
                'Server connection failed. Please check your server is running and accessible.' : 
                error.message;
            status.textContent = 'Failed to fetch playlist details';
            showError(errorMsg);
        }
    }

    function displayFormats(formatList) {
        formats.innerHTML = '';
        
        if (!formatList || formatList.length === 0) {
            formats.innerHTML = '<p>No formats available</p>';
            return;
        }
        
        // Filter and sort formats by quality
        const suitableFormats = filterAndSortFormats(formatList);
        
        // Display formats
        suitableFormats.forEach((format, index) => {
            const formatOption = createFormatOption(format, index === 0);
            formats.appendChild(formatOption);
        });

        // Set default selected format
        if (suitableFormats.length > 0) {
            selectedFormat = suitableFormats[0].format_id;
            document.querySelector('.format-option').classList.add('selected');
        }
    }

    function filterAndSortFormats(formatList) {
        // Filter formats to show only suitable qualities
        const suitableFormats = formatList.filter(format => {
            if (!format.resolution) return false;
            
            if (selectedFormatType === 'mp3') {
                // For audio, show audio-only formats
                return format.resolution === 'Audio Only';
            }
            
            const height = extractHeight(format.resolution);
            return height >= 360 && height <= 1440;
        });

        // Sort by quality (highest first)
        suitableFormats.sort((a, b) => {
            if (selectedFormatType === 'mp3') {
                // For audio, sort by quality note
                const aQuality = a.format_note.toLowerCase();
                const bQuality = b.format_note.toLowerCase();
                if (aQuality.includes('high') || aQuality.includes('192')) return -1;
                if (bQuality.includes('high') || bQuality.includes('192')) return 1;
                return 0;
            } else {
                const heightA = extractHeight(a.resolution);
                const heightB = extractHeight(b.resolution);
                return heightB - heightA;
            }
        });

        // If no suitable formats found, show all formats
        return suitableFormats.length > 0 ? suitableFormats : formatList;
    }

    function createFormatOption(format, isDefault) {
        const formatOption = document.createElement('div');
        formatOption.className = 'format-option';
        
        // Create quality display
        const qualityText = format.resolution || format.format_id;
        const detailsText = createFormatDetailsText(format);
        
        formatOption.innerHTML = `
            <input type="radio" name="format" value="${format.format_id}" ${isDefault ? 'checked' : ''}>
            <div class="format-info">
                <div class="format-quality">${qualityText}</div>
                <div class="format-details">${detailsText || 'Best available quality'}</div>
            </div>
        `;
        
        formatOption.addEventListener('change', function() {
            selectedFormat = format.format_id;
            // Update selected state
            document.querySelectorAll('.format-option').forEach(opt => opt.classList.remove('selected'));
            formatOption.classList.add('selected');
        });
        
        return formatOption;
    }

    function createFormatDetailsText(format) {
        const parts = [];
        
        if (format.filesize) {
            parts.push(format.filesize);
        }
        if (format.ext) {
            parts.push(format.ext.toUpperCase());
        }
        if (format.format_note && format.format_note !== 'N/A') {
            parts.push(format.format_note);
        }
        
        return parts.join(' • ');
    }

    function extractHeight(resolution) {
        if (!resolution) return 0;
        
        // Try to extract height from various formats
        const heightMatch = resolution.match(/(\d+)x(\d+)/);
        if (heightMatch) {
            return parseInt(heightMatch[2]);
        }
        
        const qualityMatch = resolution.match(/(\d+)p/);
        if (qualityMatch) {
            return parseInt(qualityMatch[1]);
        }
        
        return 0;
    }

    async function handleDownload() {
        if (!currentVideo && !currentPlaylist) {
            showError('No video or playlist selected');
            return;
        }

        // Validate custom path if selected
        if (selectedLocation === 'custom' && (!customPath.value || customPath.value.trim() === '')) {
            showError('Please enter a valid download path');
            customPath.focus();
            return;
        }

        try {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span>Processing...</span>
            `;
            
            showSection(progress);
            hideSection(error);

            // Extract cookies again (in case they've changed)
            const cookies = await extractYouTubeCookies();
            
            if (selectedContentType === 'playlist' && currentPlaylist) {
                // Download entire playlist
                await downloadPlaylist(currentVideo.url, cookies);
            } else {
                // Download single video
                await downloadSingleVideo(currentVideo.url, cookies);
            }
            
        } catch (error) {
            console.error('Download error:', error);
            showError(error.message);
            resetUI();
        }
    }

    // Download single video
    async function downloadSingleVideo(url, cookies) {
        // Prepare download data with cookies
        const downloadData = {
            url: url,
            format_id: selectedFormat || 'best',
            format_type: selectedFormatType,
            cookies: cookies,
            download_location: selectedLocation === 'custom' ? customPath.value.trim() : undefined
        };

        // Send download request to backend with authentication
        const response = await fetch(getApiUrl('DOWNLOAD'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(downloadData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.success) {
            // Show success message and update UI
            status.textContent = `✓ ${result.message}`;
            progressFill.style.width = '100%';
            progressText.textContent = '100% - Completed';
            
            // Optional: Start checking for file download completion
            // The backend will handle the actual file download to user's system
            setTimeout(() => {
                resetUI();
                status.textContent = result.message;
            }, 2000);
        } else {
            throw new Error(result.message || 'Download failed');
        }
    }

    // Download entire playlist
    async function downloadPlaylist(playlistUrl, cookies) {
        // Prepare form data for playlist download
        const formData = new FormData();
        formData.append('playlist_url', playlistUrl);
        formData.append('format_type', selectedFormatType);
        if (selectedLocation !== 'default') {
            formData.append('download_location', customPath.value.trim());
        }
        // Add cookies to form data (in Netscape format)
        formData.append('cookies', cookies);

        // Send playlist download request
        const response = await fetch(getApiUrl('DOWNLOAD_PLAYLIST'), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.success) {
            // Show success message and update UI
            status.textContent = `✓ ${result.message}`;
            progressFill.style.width = '100%';
            progressText.textContent = '100% - Completed';
            
            setTimeout(() => {
                resetUI();
                status.textContent = result.message;
            }, 2000);
        } else {
            // Handle error
            throw new Error(result.message || 'Playlist download failed');
        }
    }

    function updateProgress(percent, text) {
        progressFill.style.width = percent + '%';
        progressText.textContent = text;
    }

    function showSuccess(message) {
        status.textContent = message;
        hideSection(progress);
        hideSection(error);
        resetUI();
    }

    function showError(message) {
        errorMessage.textContent = message;
        showSection(error);
        hideSection(progress);
    }

    function resetUI() {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            Download
        `;
        hideSection(progress);
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        
        if (queueStatus) {
            queueStatus.style.display = 'none';
        }
    }

    function showSection(section) {
        if (section) section.style.display = 'block';
    }

    function hideSection(section) {
        if (section) section.style.display = 'none';
    }
    
    // ===== NEW FEATURES =====
    
    // Download Location Selector
    async function loadDownloadLocations() {
        try {
            const response = await fetch(getApiUrl('LOCATIONS'), {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                createLocationSelector(data.locations);
            }
        } catch (error) {
            console.log('Could not load download locations:', error);
        }
    }
    
    function createLocationSelector(locations) {
        if (!locations || locations.length === 0) return;
        
        // Create a dropdown for location selection
        const locationSelect = document.createElement('select');
        locationSelect.id = 'locationSelector';
        locationSelect.className = 'location-select';
        
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location.path;
            option.textContent = location.name;
            if (location.is_default) option.selected = true;
            locationSelect.appendChild(option);
        });
        
        // Add to download location section
        const locationSection = document.getElementById('downloadLocation');
        if (locationSection) {
            locationSection.appendChild(locationSelect);
        }
    }
    
    // Download History Display
    async function loadDownloadHistory() {
        try {
            const response = await fetch(getApiUrl('HISTORY'), {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                displayHistory(data.history);
            }
        } catch (error) {
            console.log('Could not load download history:', error);
        }
    }
    
    function displayHistory(history) {
        if (!history || history.length === 0) return;
        
        // Create history container if it doesn't exist
        let historyContainer = document.getElementById('historyContainer');
        if (!historyContainer) {
            historyContainer = document.createElement('div');
            historyContainer.id = 'historyContainer';
            historyContainer.className = 'history-container';
            document.body.appendChild(historyContainer);
        }
        
        historyContainer.innerHTML = '';
        
        // Add history header
        const header = document.createElement('h3');
        header.textContent = 'Download History';
        header.className = 'history-header';
        historyContainer.appendChild(header);
        
        // Display history items
        history.forEach(task => {
            const item = createHistoryItem(task);
            historyContainer.appendChild(item);
        });
    }
    
    function createHistoryItem(task) {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div class="history-title">${task.filename || 'Unknown'}</div>
            <div class="history-status ${task.status}">${task.status}</div>
            <div class="history-time">${new Date(task.created_at).toLocaleString()}</div>
        `;
        return item;
    }
    
    // Function to open history page
    function openHistory() {
        chrome.tabs.create({
            url: chrome.runtime.getURL('history.html')
        });
    }
    
    // Make openHistory globally accessible
    window.openHistory = openHistory;
});
