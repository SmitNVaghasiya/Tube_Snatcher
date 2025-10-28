// history.js - Download history management
document.addEventListener('DOMContentLoaded', function() {
    let currentFilter = 'all';
    let allHistory = [];
    
    // Initialize history page
    initHistoryPage();
    
    // Add filter event listeners
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            setActiveFilter(this.dataset.filter);
        });
    });
    
    function initHistoryPage() {
        loadDownloadHistory();
        updateStats();
    }
    
    async function loadDownloadHistory() {
        try {
            const response = await fetch('http://127.0.0.1:2004/api/v1/history');
            if (response.ok) {
                const data = await response.json();
                allHistory = data.history || [];
                displayHistory(allHistory);
                updateStats();
            }
        } catch (error) {
            console.error('Could not load download history:', error);
            showError('Failed to load download history');
        }
    }
    
    function displayHistory(history) {
        const container = document.getElementById('historyContainer');
        
        if (!history || history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                    </svg>
                    <h3>No downloads yet</h3>
                    <p>Start downloading YouTube videos to see them here</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        // Apply current filter
        const filteredHistory = filterHistory(history, currentFilter);
        
        filteredHistory.forEach(task => {
            const item = createHistoryItem(task);
            container.appendChild(item);
        });
    }
    
    function filterHistory(history, filter) {
        if (filter === 'all') return history;
        return history.filter(task => task.status === filter);
    }
    
    function setActiveFilter(filter) {
        currentFilter = filter;
        
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        // Re-display filtered history
        displayHistory(allHistory);
    }
    
    function createHistoryItem(task) {
        const item = document.createElement('div');
        item.className = 'history-item';
        
        const statusClass = getStatusClass(task.status);
        const statusText = getStatusText(task.status);
        const timeText = formatTime(task.created_at);
        
        item.innerHTML = `
            <div class="history-title">${task.filename || 'Unknown'}</div>
            <div class="history-status ${statusClass}">${statusText}</div>
            <div class="history-time">${timeText}</div>
        `;
        
        // Add click handler for task details
        item.addEventListener('click', () => showTaskDetails(task));
        
        return item;
    }
    
    function getStatusClass(status) {
        switch (status) {
            case 'completed': return 'completed';
            case 'failed': return 'failed';
            case 'downloading': return 'downloading';
            case 'queued': return 'queued';
            default: return 'unknown';
        }
    }
    
    function getStatusText(status) {
        switch (status) {
            case 'completed': return 'Completed';
            case 'failed': return 'Failed';
            case 'downloading': return 'Downloading';
            case 'queued': return 'Queued';
            default: return status;
        }
    }
    
    function formatTime(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString();
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    function showTaskDetails(task) {
        const details = `
Task ID: ${task.id}
Status: ${task.status}
Created: ${new Date(task.created_at).toLocaleString()}
${task.start_time ? `Started: ${new Date(task.start_time).toLocaleString()}` : ''}
${task.completion_time ? `Completed: ${new Date(task.completion_time).toLocaleString()}` : ''}
${task.filename ? `Filename: ${task.filename}` : ''}
${task.error ? `Error: ${task.error}` : ''}
        `;
        
        alert(details);
    }
    
    function updateStats() {
        const totalDownloads = allHistory.length;
        const completedDownloads = allHistory.filter(task => task.status === 'completed').length;
        
        document.getElementById('totalDownloads').textContent = totalDownloads;
        document.getElementById('completedDownloads').textContent = completedDownloads;
    }
    
    function showError(message) {
        const container = document.getElementById('historyContainer');
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <h3>Error</h3>
                <p>${message}</p>
            </div>
        `;
    }
    
    // Auto-refresh history every 30 seconds
    setInterval(loadDownloadHistory, 30000);
});

// Navigation function
function goBack() {
    window.history.back();
}
