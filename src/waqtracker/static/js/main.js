// Theme Management
(function() {
    // Get theme from localStorage or system preference
    function getPreferredTheme() {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            return storedTheme;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }
    
    // Update theme icon
    function updateThemeIcon(theme) {
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }
    
    // Apply theme to document
    function applyTheme(theme, isManual = false) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Only store in localStorage if manually changed by user
        if (isManual) {
            localStorage.setItem('theme', theme);
        }
        
        updateThemeIcon(theme);
    }
    
    // Initialize theme immediately to prevent FOUC
    const initialTheme = getPreferredTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);
    
    // Set up theme toggle button when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Update icon after DOM is ready
        updateThemeIcon(initialTheme);
        
        const themeToggle = document.getElementById('theme-toggle');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                applyTheme(newTheme, true);
            });
        }
        
        // Listen for system theme changes
        const prefersDarkQuery = window.matchMedia('(prefers-color-scheme: dark)');
        prefersDarkQuery.addEventListener('change', function(e) {
            // Only auto-switch if user hasn't manually set a preference
            const hasManualPreference = localStorage.getItem('theme') !== null;
            if (!hasManualPreference) {
                applyTheme(e.matches ? 'dark' : 'light', false);
            }
        });
    });
})();

// Simple JavaScript for time tracker app

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s';
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Calculate duration preview for time entry form
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    if (startTimeInput && endTimeInput) {
        function updateDurationPreview() {
            const startTime = startTimeInput.value;
            const endTime = endTimeInput.value;
            
            if (startTime && endTime) {
                const start = new Date('2000-01-01 ' + startTime);
                const end = new Date('2000-01-01 ' + endTime);
                
                let duration = (end - start) / (1000 * 60 * 60); // hours
                
                if (duration < 0) {
                    duration += 24; // Handle midnight crossing
                }
                
                if (duration > 0) {
                    const hours = Math.floor(duration);
                    const minutes = Math.round((duration - hours) * 60);
                    const durationText = `${hours}h ${minutes}m`;
                    
                    // Create or update preview element
                    let preview = document.getElementById('duration-preview');
                    if (!preview) {
                        preview = document.createElement('div');
                        preview.id = 'duration-preview';
                        preview.className = 'duration-preview';
                        endTimeInput.parentElement.appendChild(preview);
                    }
                    preview.textContent = `Duration: ${durationText}`;
                }
            }
        }
        
        startTimeInput.addEventListener('change', updateDurationPreview);
        endTimeInput.addEventListener('change', updateDurationPreview);
    }

    // Timer Logic
    const timerDisplay = document.getElementById('timer-display');
    if (timerDisplay) {
        const btnStart = document.getElementById('btn-start-timer');
        const btnStop = document.getElementById('btn-stop-timer');
        const btnPause = document.getElementById('btn-pause-timer');
        const btnResume = document.getElementById('btn-resume-timer');
        const statusIndicator = document.getElementById('timer-status-indicator');
        const descriptionDisplay = document.getElementById('timer-description');
        
        let timerInterval;
        let startTime = null;

        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }

        function updateTimer() {
            if (!startTime) return;
            const now = new Date();
            const elapsed = Math.floor((now - startTime) / 1000);
            timerDisplay.textContent = formatTime(elapsed);
        }

        function setTimerActive(active, startTimestamp = null, description = "Work") {
            if (active) {
                // Parse start time "HH:MM:SS" today
                const today = new Date();
                const [hours, minutes, seconds] = startTimestamp.split(':');
                startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), hours, minutes, seconds);
                
                // Adjust for if start time was yesterday (should handle in backend ideally but simple fix here)
                if (startTime > new Date()) {
                    startTime.setDate(startTime.getDate() - 1);
                }

                timerInterval = setInterval(updateTimer, 1000);
                updateTimer(); // Immediate update

                statusIndicator.className = 'status-indicator active';
                descriptionDisplay.textContent = `Tracking: ${description}`;
                
                btnStart.style.display = 'none';
                btnResume.style.display = 'none';
                btnStop.style.display = 'inline-block';
                btnPause.style.display = 'inline-block';
            } else {
                clearInterval(timerInterval);
                statusIndicator.className = 'status-indicator inactive';
                descriptionDisplay.textContent = 'Ready to work';
                timerDisplay.textContent = '00:00:00';
                
                btnStop.style.display = 'none';
                btnPause.style.display = 'none';
                
                // If we just stopped/paused, deciding between Start and Resume is handled by caller
                // Default reset state:
                btnStart.style.display = 'inline-block';
                btnResume.style.display = 'none';
            }
        }

        function checkTimerStatus() {
            fetch('/api/timer/status')
                .then(response => response.json())
                .then(data => {
                    if (data.active) {
                        setTimerActive(true, data.start_time, data.description);
                    } else {
                        setTimerActive(false);
                    }
                })
                .catch(err => console.error('Error checking timer status:', err));
        }

        // Initialize status
        checkTimerStatus();

        btnStart.addEventListener('click', () => {
            fetch('/api/timer/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: 'Work' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimerActive(true, data.start_time, 'Work');
                } else {
                    alert('Failed to start timer: ' + data.message);
                }
            });
        });

        btnStop.addEventListener('click', () => {
            fetch('/api/timer/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimerActive(false);
                    // Reload to update the list of entries
                    window.location.reload();
                } else {
                    alert('Failed to stop timer: ' + data.message);
                }
            });
        });

        btnPause.addEventListener('click', () => {
            fetch('/api/timer/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Stop the visual timer
                    clearInterval(timerInterval);
                    statusIndicator.className = 'status-indicator paused';
                    descriptionDisplay.textContent = 'Timer Paused';
                    
                    btnStop.style.display = 'none';
                    btnPause.style.display = 'none';
                    btnStart.style.display = 'none';
                    btnResume.style.display = 'inline-block'; // Show Resume
                } else {
                    alert('Failed to pause timer: ' + data.message);
                }
            });
        });

        btnResume.addEventListener('click', () => {
             fetch('/api/timer/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: 'Work' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimerActive(true, data.start_time, 'Work');
                } else {
                    alert('Failed to resume timer: ' + data.message);
                }
            });
        });
    }
});