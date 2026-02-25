// ===== INITIALIZATION =====
let socket;
let charts = {};
let monitoringTimer = null;
let monitoringSeconds = 0;
let notifications = [];
let evidenceData = [];

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io({
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: Infinity
    });

    // Connection events
    socket.on('connect', function() {
        console.log('🔌 Connected to server');
        updateConnectionStatus(true);
        showToast('success', 'Connected', 'Real-time connection established');
    });

    socket.on('disconnect', function() {
        console.log('🔌 Disconnected from server');
        updateConnectionStatus(false);
        showToast('error', 'Disconnected', 'Lost connection to server');
    });

    socket.on('video_frame', handleVideoFrame);
    socket.on('stats_update', handleStatsUpdate);
    socket.on('new_alert', handleNewAlert);
}

// ===== UI INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeSidebar();
    initializeCharts();
    loadAllData();
    setupEventListeners();
    
    // Hide loading overlay after initialization
    setTimeout(() => {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }, 1500);
});

// ===== SIDEBAR =====
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const menuToggle = document.getElementById('menuToggle');
    const menuItems = document.querySelectorAll('.menu-item');

    // Toggle sidebar
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Mobile menu toggle
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Menu item click
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            const section = this.dataset.section;
            
            // Update active menu item
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Show corresponding section
            document.querySelectorAll('.content-section').forEach(s => {
                s.classList.remove('active');
            });
            document.getElementById(section).classList.add('active');
            
            // Update page title
            document.getElementById('pageTitle').textContent = 
                this.querySelector('span').textContent;
            
            // Close sidebar on mobile
            if (window.innerWidth <= 992) {
                sidebar.classList.remove('open');
            }
        });
    });
}

// ===== CHARTS INITIALIZATION =====
function initializeCharts() {
    // Cleanliness Trend Chart
    const ctx1 = document.getElementById('cleanlinessChart')?.getContext('2d');
    if (ctx1) {
        charts.cleanliness = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Cleanliness Score',
                    data: [95, 92, 96, 94, 91, 97, 98],
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            display: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Detection Distribution Chart
    const ctx2 = document.getElementById('detectionChart')?.getContext('2d');
    if (ctx2) {
        charts.detection = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['Garbage', 'People', 'Vehicles', 'Animals'],
                datasets: [{
                    data: [30, 45, 15, 10],
                    backgroundColor: [
                        '#ef4444',
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Timeline Chart
    const ctx3 = document.getElementById('timelineChart')?.getContext('2d');
    if (ctx3) {
        charts.timeline = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'Detections',
                    data: [5, 2, 15, 25, 30, 18],
                    backgroundColor: '#4f46e5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Garbage Types Chart
    const ctx4 = document.getElementById('garbageTypesChart')?.getContext('2d');
    if (ctx4) {
        charts.garbageTypes = new Chart(ctx4, {
            type: 'pie',
            data: {
                labels: ['Plastic', 'Paper', 'Glass', 'Metal', 'Organic'],
                datasets: [{
                    data: [45, 25, 15, 10, 5],
                    backgroundColor: [
                        '#ef4444',
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Peak Hours Chart
    const ctx5 = document.getElementById('peakHoursChart')?.getContext('2d');
    if (ctx5) {
        charts.peakHours = new Chart(ctx5, {
            type: 'line',
            data: {
                labels: ['12am', '3am', '6am', '9am', '12pm', '3pm', '6pm', '9pm'],
                datasets: [{
                    label: 'Activity Level',
                    data: [10, 5, 20, 45, 55, 60, 48, 30],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// ===== SOCKET EVENT HANDLERS =====
function handleVideoFrame(data) {
    const videoFeed = document.getElementById('videoFeed');
    const noFeedMessage = document.getElementById('noFeedMessage');
    
    if (videoFeed) {
        videoFeed.src = 'data:image/jpeg;base64,' + data.frame;
        noFeedMessage.style.display = 'none';
    }
}

function handleStatsUpdate(stats) {
    // Update dashboard stats
    updateElement('dashboardCleanlinessScore', stats.cleanliness_score + '%');
    updateElement('dashboardGarbageCount', stats.garbage_count);
    updateElement('dashboardPeopleCount', stats.persons_count);
    updateElement('dashboardIncidentsCount', stats.total_incidents);
    
    // Update monitoring feed stats
    updateElement('feedGarbageCount', stats.garbage_count);
    updateElement('feedPeopleCount', stats.persons_count);
    updateElement('feedCleanliness', stats.cleanliness_score + '%');
    
    // Update detection rates
    const garbageRate = calculateDetectionRate(stats.garbage_count, stats.total_detections);
    const peopleRate = calculateDetectionRate(stats.persons_count, stats.total_detections);
    
    updateElement('garbageRateBar', { style: { width: garbageRate + '%' } });
    updateElement('garbageRateValue', garbageRate + '%');
    updateElement('peopleRateBar', { style: { width: peopleRate + '%' } });
    updateElement('peopleRateValue', peopleRate + '%');
    
    // Update recording indicator
    const recordingIndicator = document.getElementById('recordingIndicator');
    if (recordingIndicator) {
        recordingIndicator.style.display = stats.is_recording ? 'flex' : 'none';
    }
    
    // Update status badge
    const statusBadge = document.querySelector('.status-badge');
    if (statusBadge) {
        if (stats.is_recording) {
            statusBadge.textContent = 'Monitoring';
            statusBadge.classList.add('active');
        } else {
            statusBadge.textContent = 'Stopped';
            statusBadge.classList.remove('active');
        }
    }
}

function handleNewAlert(alert) {
    console.log('New alert:', alert);
    addAlertToList(alert);
    addNotification(alert);
    showToast('warning', '⚠️ Alert Detected', `${alert.object} detected with ${alert.confidence}% confidence`);
    
    // Update charts with new data
    updateChartsWithAlert(alert);
}

// ===== ALERTS MANAGEMENT =====
function addAlertToList(alert) {
    const alertsList = document.getElementById('alertsList');
    const liveAlertCount = document.getElementById('liveAlertCount');
    
    if (!alertsList) return;
    
    // Remove "no alerts" message
    const noAlerts = alertsList.querySelector('.no-alerts');
    if (noAlerts) noAlerts.remove();
    
    // Determine severity based on confidence
    let severity = 'medium';
    if (alert.confidence >= 90) severity = 'high';
    else if (alert.confidence <= 70) severity = 'low';
    
    // Create alert item
    const alertItem = document.createElement('div');
    alertItem.className = `alert-item ${severity}`;
    alertItem.innerHTML = `
        <div class="alert-header">
            <span class="alert-title">
                <i class="fas fa-exclamation-triangle"></i> ${alert.object.toUpperCase()}
            </span>
            <span class="alert-time">${alert.timestamp}</span>
        </div>
        <div class="alert-message">${alert.description || 'Illegal dumping detected'}</div>
        <div class="alert-confidence">Confidence: ${alert.confidence}%</div>
    `;
    
    // Add to top of list
    alertsList.insertBefore(alertItem, alertsList.firstChild);
    
    // Update count
    const currentCount = alertsList.children.length;
    if (liveAlertCount) liveAlertCount.textContent = currentCount;
    
    // Limit to 20 alerts
    while (alertsList.children.length > 20) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

// ===== NOTIFICATIONS =====
function addNotification(alert) {
    const notificationList = document.getElementById('notificationList');
    const notificationCount = document.getElementById('notificationCount');
    
    if (!notificationList) return;
    
    const notificationItem = document.createElement('div');
    notificationItem.className = 'notification-item unread';
    notificationItem.innerHTML = `
        <div class="notification-content">
            <strong>${alert.object} Detected</strong>
            <p>${alert.timestamp}</p>
        </div>
    `;
    
    notificationList.insertBefore(notificationItem, notificationList.firstChild);
    
    // Update count
    notifications.push(alert);
    if (notificationCount) {
        notificationCount.textContent = notifications.length;
    }
    
    // Limit to 50 notifications
    while (notificationList.children.length > 50) {
        notificationList.removeChild(notificationList.lastChild);
    }
}

function markAllAsRead() {
    document.querySelectorAll('.notification-item').forEach(item => {
        item.classList.remove('unread');
    });
    notifications = [];
    updateElement('notificationCount', '0');
}

// ===== TOAST NOTIFICATIONS =====
function showToast(type, title, message) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'check-circle',
        error: 'times-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// ===== MONITORING CONTROLS =====
function startMonitoring() {
    fetch('/api/start_monitoring', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                updateConnectionStatus(true, 'Monitoring');
                showToast('success', '✅ Started', 'Monitoring system activated');
                
                // Start timer
                startMonitoringTimer();
            } else {
                showToast('error', '❌ Error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', '❌ Error', 'Failed to start monitoring');
        });
}

function stopMonitoring() {
    fetch('/api/stop_monitoring', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                updateConnectionStatus(false);
                showToast('success', '⏹️ Stopped', 'Monitoring stopped. Report generated.');
                
                // Stop timer
                stopMonitoringTimer();
                
                // Reload data
                setTimeout(() => {
                    loadAllData();
                }, 1000);
            } else {
                showToast('error', '❌ Error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', '❌ Error', 'Failed to stop monitoring');
        });
}

// ===== MONITORING TIMER =====
function startMonitoringTimer() {
    monitoringSeconds = 0;
    updateTimerDisplay();
    
    monitoringTimer = setInterval(() => {
        monitoringSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function stopMonitoringTimer() {
    if (monitoringTimer) {
        clearInterval(monitoringTimer);
        monitoringTimer = null;
    }
}

function updateTimerDisplay() {
    const hours = Math.floor(monitoringSeconds / 3600);
    const minutes = Math.floor((monitoringSeconds % 3600) / 60);
    const seconds = monitoringSeconds % 60;
    
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    updateElement('recordingTime', `<i class="far fa-clock"></i> ${timeString}`);
}

// ===== CONNECTION STATUS =====
function updateConnectionStatus(isConnected, status = null) {
    const statusIndicator = document.getElementById('statusIndicator');
    const sidebarStatus = document.getElementById('sidebarStatus');
    
    if (statusIndicator) {
        statusIndicator.textContent = isConnected ? (status || 'Online') : 'Offline';
        statusIndicator.className = `status-badge ${isConnected ? 'active' : ''}`;
    }
    
    if (sidebarStatus) {
        sidebarStatus.className = `status-indicator ${isConnected ? 'online' : 'offline'}`;
    }
}

// ===== DATA LOADING =====
function loadAllData() {
    loadEvidence();
    loadReports();
    loadAlertFiles();
    loadDumpingLog();
    loadHistory();
}

function loadEvidence() {
    fetch('/api/evidence')
        .then(response => response.json())
        .then(files => {
            evidenceData = files;
            displayEvidence(files);
        })
        .catch(error => {
            console.error('Error loading evidence:', error);
            showToast('error', 'Error', 'Failed to load evidence');
        });
}

function displayEvidence(files) {
    const gallery = document.getElementById('evidenceGallery');
    if (!gallery) return;
    
    if (files.length === 0) {
        gallery.innerHTML = `
            <div class="no-data">
                <i class="fas fa-folder-open"></i>
                <p>No evidence files yet</p>
            </div>
        `;
        return;
    }
    
    gallery.innerHTML = '';
    
    files.forEach(file => {
        const item = createEvidenceItem(file);
        gallery.appendChild(item);
    });
}

function createEvidenceItem(file) {
    const item = document.createElement('div');
    item.className = 'evidence-item';
    
    const typeIcon = file.type === 'video' ? 'video' : 'camera';
    const timestamp = new Date(file.timestamp).toLocaleString();
    
    item.innerHTML = `
        <div class="evidence-preview" onclick="viewEvidence('${file.filename}', '${file.type}')">
            ${file.type === 'image' ? 
                `<img src="/evidence/${file.filename}" alt="${file.filename}">` :
                `<div style="background: #000; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-play-circle" style="font-size: 3rem; color: white;"></i>
                </div>`
            }
            <span class="evidence-type-badge">
                <i class="fas fa-${typeIcon}"></i> ${file.type}
            </span>
        </div>
        <div class="evidence-details">
            <h4>${file.filename}</h4>
            <p><i class="far fa-clock"></i> ${timestamp}</p>
            <p><i class="fas fa-weight-hanging"></i> ${(file.size / 1024).toFixed(2)} KB</p>
        </div>
        <div class="evidence-actions">
            <button class="btn-icon" onclick="viewEvidence('${file.filename}', '${file.type}')" title="View">
                <i class="fas fa-eye"></i>
            </button>
            <a href="/evidence/${file.filename}" download class="btn-icon" title="Download">
                <i class="fas fa-download"></i>
            </a>
            <button class="btn-icon" onclick="shareEvidence('${file.filename}')" title="Share">
                <i class="fas fa-share-alt"></i>
            </button>
        </div>
    `;
    
    return item;
}

function loadReports() {
    fetch('/api/reports')
        .then(response => response.json())
        .then(reports => {
            displayReports(reports);
        })
        .catch(error => {
            console.error('Error loading reports:', error);
        });
}

function displayReports(reports) {
    const reportsList = document.getElementById('reportsList');
    if (!reportsList) return;
    
    if (reports.length === 0) {
        reportsList.innerHTML = `
            <div class="no-data">
                <i class="fas fa-file-alt"></i>
                <p>No reports yet</p>
            </div>
        `;
        return;
    }
    
    reportsList.innerHTML = '';
    
    reports.forEach(report => {
        const item = document.createElement('div');
        item.className = 'report-item';
        item.innerHTML = `
            <div class="report-header">
                <div class="report-icon">
                    <i class="fas fa-file-pdf"></i>
                </div>
                <div class="report-info">
                    <h3>${report.filename}</h3>
                    <p>Generated: ${new Date(report.timestamp).toLocaleString()}</p>
                </div>
            </div>
            <div class="report-meta">
                <span><i class="fas fa-weight-hanging"></i> ${(report.size / 1024).toFixed(2)} KB</span>
                <span><i class="fas fa-chart-line"></i> ${report.entries || 0} entries</span>
            </div>
            <div class="report-actions">
                <button class="btn btn-primary" onclick="viewReport('${report.filename}')">
                    <i class="fas fa-eye"></i> View
                </button>
                <a href="/reports/${report.filename}" download class="btn btn-success">
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        `;
        reportsList.appendChild(item);
    });
}

function loadAlertFiles() {
    fetch('/api/alert_files')
        .then(response => response.json())
        .then(alerts => {
            displayAlertFiles(alerts);
        })
        .catch(error => {
            console.error('Error loading alert files:', error);
        });
}

function displayAlertFiles(alerts) {
    // Implementation for alert files display
}

function loadDumpingLog() {
    fetch('/api/dumping_log')
        .then(response => response.json())
        .then(data => {
            displayDumpingLog(data);
        })
        .catch(error => {
            console.error('Error loading log:', error);
        });
}

function displayDumpingLog(data) {
    const logContent = document.getElementById('dumpingLog');
    if (!logContent) return;
    
    if (data.content) {
        logContent.innerHTML = `<pre class="log-pre">${data.content}</pre>`;
    }
}

function loadHistory() {
    fetch('/api/cleanliness_history')
        .then(response => response.json())
        .then(data => {
            displayHistory(data);
        })
        .catch(error => {
            console.error('Error loading history:', error);
        });
}

function displayHistory(data) {
    const historyContent = document.getElementById('historyContent');
    if (!historyContent) return;
    
    if (!data.sessions || data.sessions.length === 0) {
        historyContent.innerHTML = '<div class="no-data">No historical data yet</div>';
        return;
    }
    
    // Update charts with historical data if available
    if (data.sessions.length > 0) {
        updateChartsWithHistory(data.sessions);
    }
}

// ===== EVIDENCE VIEWING =====
function viewEvidence(filename, type) {
    const modal = document.getElementById('contentModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const modalImageContainer = document.getElementById('modalImageContainer');
    
    modalTitle.textContent = type === 'image' ? '📸 Evidence Image' : '🎬 Evidence Video';
    
    if (type === 'image') {
        modalContent.style.display = 'none';
        modalImageContainer.style.display = 'block';
        modalImageContainer.innerHTML = `
            <img src="/evidence/${filename}" alt="${filename}" style="width: 100%;">
            <div style="text-align: center; margin-top: 15px;">
                <a href="/evidence/${filename}" download class="btn btn-success">
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        `;
    } else {
        modalContent.style.display = 'none';
        modalImageContainer.style.display = 'block';
        modalImageContainer.innerHTML = `
            <video controls style="width: 100%;">
                <source src="/evidence/${filename}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/evidence/${filename}" download class="btn btn-success">
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        `;
    }
    
    modal.style.display = 'block';
}

function viewReport(filename) {
    fetch(`/api/report/${filename}`)
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                showModal('Report: ' + filename, data.content);
            }
        })
        .catch(error => {
            console.error('Error viewing report:', error);
        });
}

function viewAlert(filename) {
    fetch(`/api/alert/${filename}`)
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                showModal('Alert: ' + filename, data.content);
            }
        })
        .catch(error => {
            console.error('Error viewing alert:', error);
        });
}

// ===== MODAL =====
function showModal(title, content) {
    const modal = document.getElementById('contentModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const modalImageContainer = document.getElementById('modalImageContainer');
    
    modalTitle.textContent = title;
    modalContent.textContent = content;
    modalContent.style.display = 'block';
    modalImageContainer.style.display = 'none';
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('contentModal').style.display = 'none';
}

// ===== UTILITY FUNCTIONS =====
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        if (typeof value === 'object') {
            Object.assign(element, value);
        } else {
            element.textContent = value;
        }
    }
}

function calculateDetectionRate(count, total) {
    if (!total) return 0;
    return Math.round((count / total) * 100);
}

function updateChartsWithAlert(alert) {
    // Update charts with new alert data
    if (charts.timeline) {
        // Add new data point to timeline
        const currentData = charts.timeline.data.datasets[0].data;
        currentData.push(1);
        if (currentData.length > 24) currentData.shift();
        charts.timeline.update();
    }
}

function updateChartsWithHistory(sessions) {
    // Update charts with historical data
    if (charts.cleanliness && sessions.length > 0) {
        const scores = sessions.map(s => s.average_cleanliness_score).reverse();
        charts.cleanliness.data.datasets[0].data = scores;
        charts.cleanliness.update();
    }
}

// ===== SETTINGS =====
function saveSettings() {
    const settings = {
        confidenceThreshold: document.getElementById('confidenceThreshold')?.value,
        alertSensitivity: document.getElementById('alertSensitivity')?.value,
        emailAlerts: document.getElementById('emailAlerts')?.checked,
        smsAlerts: document.getElementById('smsAlerts')?.checked,
        autoDeleteDays: document.getElementById('autoDeleteDays')?.value,
        compressionQuality: document.getElementById('compressionQuality')?.value
    };
    
    fetch('/api/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('success', '✅ Settings Saved', 'Configuration updated successfully');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showToast('error', '❌ Error', 'Failed to save settings');
    });
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Notification badge click
    document.getElementById('notificationBadge')?.addEventListener('click', function() {
        document.getElementById('notificationPanel').classList.toggle('open');
    });

    // Click outside to close notification panel
    document.addEventListener('click', function(event) {
        const panel = document.getElementById('notificationPanel');
        const badge = document.getElementById('notificationBadge');
        
        if (!panel.contains(event.target) && !badge.contains(event.target)) {
            panel.classList.remove('open');
        }
    });

    // Evidence filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.dataset.filter;
            filterEvidence(filter);
        });
    });

    // Evidence search
    document.getElementById('evidenceSearch')?.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        searchEvidence(searchTerm);
    });

    // Settings change listeners
    document.getElementById('confidenceThreshold')?.addEventListener('input', function(e) {
        document.getElementById('confidenceValue').textContent = e.target.value + '%';
    });

    document.getElementById('compressionQuality')?.addEventListener('input', function(e) {
        document.getElementById('compressionValue').textContent = e.target.value + '%';
    });

    // Save settings button
    document.querySelector('#settings .btn-primary')?.addEventListener('click', saveSettings);
}

// ===== EVIDENCE FILTERING =====
function filterEvidence(filter) {
    if (filter === 'all') {
        displayEvidence(evidenceData);
    } else {
        const filtered = evidenceData.filter(item => item.type === filter);
        displayEvidence(filtered);
    }
}

function searchEvidence(term) {
    if (!term) {
        displayEvidence(evidenceData);
        return;
    }
    
    const filtered = evidenceData.filter(item => 
        item.filename.toLowerCase().includes(term) ||
        item.timestamp.toLowerCase().includes(term)
    );
    displayEvidence(filtered);
}

// ===== SHARE FUNCTIONALITY =====
function shareEvidence(filename) {
    // Implement sharing functionality (email, download link, etc.)
    showToast('info', 'Share', 'Sharing feature coming soon');
}

function downloadAllEvidence() {
    showToast('info', 'Download', 'Preparing archive for download...');
    // Implement download all functionality
}

function generateReport() {
    showToast('info', 'Report', 'Generating custom report...');
    // Implement custom report generation
}

function refreshAnalytics() {
    showToast('info', 'Refresh', 'Updating analytics data...');
    // Implement analytics refresh
}

// ===== WINDOW EVENT HANDLERS =====
window.onclick = function(event) {
    const modal = document.getElementById('contentModal');
    if (event.target === modal) {
        closeModal();
    }
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
        document.getElementById('notificationPanel').classList.remove('open');
    }
});

// Export functions for HTML onclick handlers

// ===== EMAIL SETTINGS =====
function loadEmailSettings() {
    fetch('/api/settings/email')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.recipient) {
                document.getElementById('recipientEmail').value = data.recipient;
            }
        })
        .catch(error => {
            console.error('Error loading email settings:', error);
        });
}

function saveEmailSettings() {
    const recipient = document.getElementById('recipientEmail').value.trim();
    
    if (!recipient) {
        showToast('error', 'Error', 'Please enter a recipient email');
        return;
    }
    
    if (!recipient.includes('@')) {
        showToast('error', 'Error', 'Please enter a valid email address');
        return;
    }
    
    fetch('/api/settings/email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ recipient: recipient })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('success', '✅ Saved', data.message);
            } else {
                showToast('error', '❌ Error', data.message);
            }
        })
        .catch(error => {
            console.error('Error saving email settings:', error);
            showToast('error', '❌ Error', 'Failed to save recipient email');
        });
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Load email settings when settings section is opened
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            if (this.dataset.section === 'settings') {
                loadEmailSettings();
            }
        });
    });
    
    // Other event listeners can be added here
}

// Export functions to window
window.startMonitoring = startMonitoring;
window.stopMonitoring = stopMonitoring;
window.loadEvidence = loadEvidence;
window.loadReports = loadReports;
window.loadAlertFiles = loadAlertFiles;
window.loadDumpingLog = loadDumpingLog;
window.loadHistory = loadHistory;
window.viewEvidence = viewEvidence;
window.viewReport = viewReport;
window.viewAlert = viewAlert;
window.closeModal = closeModal;
window.markAllAsRead = markAllAsRead;
window.shareEvidence = shareEvidence;
window.downloadAllEvidence = downloadAllEvidence;
window.generateReport = generateReport;
window.refreshAnalytics = refreshAnalytics;
window.saveSettings = saveSettings;
window.saveEmailSettings = saveEmailSettings;