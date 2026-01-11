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
        function parseTimeInput(input) {
            const val = input.value;
            if (!val) return null;
            
            if (input.type === 'time') {
                // "HH:MM" format
                const [h, m] = val.split(':').map(Number);
                if (isNaN(h) || isNaN(m)) return null;
                return h * 60 + m;
            } else {
                // Text input, likely 12h format "HH:MM AM/PM"
                // Try robust parsing
                const match = val.match(/^(\d{1,2}):(\d{2})\s*([AaPp][Mm])?$/i);
                if (match) {
                    let h = parseInt(match[1]);
                    const m = parseInt(match[2]);
                    const period = match[3] ? match[3].toUpperCase() : null;
                    
                    if (period) {
                        if (period === 'PM' && h < 12) h += 12;
                        if (period === 'AM' && h === 12) h = 0;
                    }
                    return h * 60 + m;
                }
                // Fallback basic parse
                const [h, m] = val.split(':').map(Number);
                if (!isNaN(h) && !isNaN(m)) return h * 60 + m;
                return null;
            }
        }

        function updateDurationPreview() {
            const startMinutes = parseTimeInput(startTimeInput);
            const endMinutes = parseTimeInput(endTimeInput);
            
            if (startMinutes !== null && endMinutes !== null) {
                let diff = endMinutes - startMinutes;
                
                if (diff < 0) {
                    diff += 24 * 60; // Handle midnight crossing
                }
                
                // Calculate pause deduction
                let pauseMinutes = 0;
                const pauseModeInput = document.querySelector('input[name="pause_mode"]:checked');
                if (pauseModeInput) {
                    const mode = pauseModeInput.value;
                    if (mode === 'default') {
                        // Get default pause from data attribute
                        const defaultPauseAttr = pauseModeInput.getAttribute('data-default-pause');
                        if (defaultPauseAttr) {
                            pauseMinutes = parseInt(defaultPauseAttr);
                        }
                    } else if (mode === 'custom') {
                        const customInput = document.getElementById('custom_pause_minutes');
                        if (customInput && customInput.value) {
                            pauseMinutes = parseInt(customInput.value);
                        }
                    }
                }
                
                // Apply pause
                const netMinutes = Math.max(0, diff - pauseMinutes);
                
                const hours = Math.floor(netMinutes / 60);
                const minutes = netMinutes % 60;
                
                let durationText = `${hours}h ${minutes}m`;
                if (pauseMinutes > 0) {
                    durationText += ` (incl. ${pauseMinutes}m pause)`;
                }
                
                // Create or update preview element
                let preview = document.getElementById('duration-preview');
                if (!preview) {
                    preview = document.createElement('div');
                    preview.id = 'duration-preview';
                    preview.className = 'duration-preview text-muted';
                    preview.style.marginTop = '0.25rem';
                    preview.style.fontSize = '0.85rem';
                    preview.style.fontWeight = '500';
                    preview.style.color = 'var(--primary-color)';
                    
                    // Append directly under the end time input
                    endTimeInput.parentElement.appendChild(preview);
                }
                preview.textContent = `Duration: ${durationText}`;
            } else {
                const preview = document.getElementById('duration-preview');
                if (preview) preview.textContent = '';
            }
        }
        
        startTimeInput.addEventListener('input', updateDurationPreview);
        endTimeInput.addEventListener('input', updateDurationPreview);
        
        // Listen for pause changes
        const pauseRadios = document.querySelectorAll('input[name="pause_mode"]');
        pauseRadios.forEach(radio => radio.addEventListener('change', updateDurationPreview));
        
        const customPauseInput = document.getElementById('custom_pause_minutes');
        if (customPauseInput) {
            customPauseInput.addEventListener('input', updateDurationPreview);
            // Listen for custom event triggered by toggle function
            customPauseInput.addEventListener('change', updateDurationPreview);
        }
        
        // Initial calc
        setTimeout(updateDurationPreview, 100);
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
        let elapsedSeconds = 0;
        let lastTickTime = null;
        let alertDismissed = false;
        let alertBanner = null;

        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }

        function updateTimer() {
            const now = Date.now();
            if (lastTickTime) {
                elapsedSeconds += (now - lastTickTime) / 1000;
            }
            lastTickTime = now;
            timerDisplay.textContent = formatTime(elapsedSeconds);
        }

        function setTimerState(state, elapsed = 0, description = "Work") {
            clearInterval(timerInterval);
            elapsedSeconds = elapsed;
            timerDisplay.textContent = formatTime(elapsedSeconds);

            if (state === 'running') {
                lastTickTime = Date.now();
                timerInterval = setInterval(updateTimer, 1000);
                
                statusIndicator.className = 'status-indicator active';
                descriptionDisplay.textContent = `Tracking: ${description}`;
                
                btnStart.style.display = 'none';
                btnResume.style.display = 'none';
                btnStop.style.display = 'inline-block';
                btnPause.style.display = 'inline-block';
            } else if (state === 'paused') {
                statusIndicator.className = 'status-indicator paused';
                descriptionDisplay.textContent = `Paused: ${description}`;
                
                btnStart.style.display = 'none';
                btnPause.style.display = 'none';
                btnStop.style.display = 'inline-block'; // Allow stopping while paused
                btnResume.style.display = 'inline-block';
            } else {
                // Stopped/Inactive
                statusIndicator.className = 'status-indicator inactive';
                descriptionDisplay.textContent = 'Ready to work';
                timerDisplay.textContent = '00:00:00';
                
                btnStop.style.display = 'none';
                btnPause.style.display = 'none';
                btnResume.style.display = 'none';
                btnStart.style.display = 'inline-block';
            }
        }

        function checkTimerStatus() {
            fetch('/api/timer/status')
                .then(response => response.json())
                .then(data => {
                    if (data.active) {
                        if (data.is_paused) {
                            setTimerState('paused', data.elapsed_seconds, data.description);
                        } else {
                            setTimerState('running', data.elapsed_seconds, data.description);
                        }
                    } else {
                        setTimerState('stopped');
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
                    // Start from 0
                    setTimerState('running', 0, 'Work');
                    // Reset alert dismissal for new session
                    alertDismissed = false;
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
                    setTimerState('stopped');
                    // Reset alert dismissal when timer stops
                    alertDismissed = false;
                    // Reload to update the list of entries
                    window.location.reload();
                } else {
                    alert('Failed to stop timer: ' + data.message);
                }
            });
        });

        btnPause.addEventListener('click', () => {
            fetch('/api/timer/pause', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Just switch state, keep current elapsed
                    setTimerState('paused', elapsedSeconds, descriptionDisplay.textContent.replace('Tracking: ', ''));
                } else {
                    alert('Failed to pause timer: ' + data.message);
                }
            });
        });

        btnResume.addEventListener('click', () => {
             fetch('/api/timer/resume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Resume from current elapsed
                    setTimerState('running', elapsedSeconds, descriptionDisplay.textContent.replace('Paused: ', ''));
                } else {
                    alert('Failed to resume timer: ' + data.message);
                }
            });
        });

        // Session Alert Logic
        function checkSessionAlert() {
            // Don't check if user dismissed the alert
            if (alertDismissed) {
                return;
            }

            fetch('/api/timer/session-alert-check')
                .then(response => response.json())
                .then(data => {
                    if (data.alert && data.enabled) {
                        showSessionAlert(data);
                    } else {
                        hideSessionAlert();
                    }
                })
                .catch(err => console.error('Error checking session alert:', err));
        }

        function showSessionAlert(data) {
            // Don't create duplicate banners
            if (alertBanner) {
                return;
            }

            const timerPanel = document.querySelector('.timer-control-panel');
            if (!timerPanel) {
                return;
            }

            alertBanner = document.createElement('div');
            alertBanner.className = 'session-alert-banner';
            alertBanner.innerHTML = `
                <div class="session-alert-content">
                    <div class="session-alert-icon">⚠️</div>
                    <div class="session-alert-text">
                        <div class="session-alert-title">Long Work Session Alert</div>
                        <div class="session-alert-message">
                            You've been working for ${data.current_hours.toFixed(1)} hours. 
                            Maximum recommended session is ${data.max_hours} hours. 
                            Consider taking a break!
                        </div>
                    </div>
                </div>
                <button class="session-alert-dismiss" id="dismiss-session-alert">Dismiss</button>
            `;

            timerPanel.parentNode.insertBefore(alertBanner, timerPanel);

            document.getElementById('dismiss-session-alert').addEventListener('click', () => {
                alertDismissed = true;
                hideSessionAlert();
            });
        }

        function hideSessionAlert() {
            if (alertBanner) {
                alertBanner.remove();
                alertBanner = null;
            }
        }

        // Check for session alert every 60 seconds
        checkSessionAlert();
        setInterval(checkSessionAlert, 60000);
    }
    
    // Calendar interactivity
    const calendarDays = document.querySelectorAll('.calendar-day:not(.empty)');
    const tooltip = document.getElementById('calendar-tooltip');
    
    if (calendarDays.length > 0 && tooltip) {
        let currentTooltipDay = null;
        
        calendarDays.forEach(day => {
            day.addEventListener('click', async function(e) {
                e.stopPropagation();
                
                const date = this.dataset.date;
                if (!date) return;
                
                // If clicking the same day, hide tooltip
                if (currentTooltipDay === date && tooltip.style.display !== 'none') {
                    hideTooltip();
                    return;
                }
                
                currentTooltipDay = date;
                
                try {
                    const response = await fetch(`/api/calendar/day/${date}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        showTooltip(this, data);
                    }
                } catch (error) {
                    console.error('Error fetching day details:', error);
                }
            });
        });
        
        function showTooltip(dayElement, data) {
            const rect = dayElement.getBoundingClientRect();
            const tooltipDate = document.getElementById('tooltip-date');
            const tooltipBody = document.getElementById('tooltip-body');
            const tooltipAddEntry = document.getElementById('tooltip-add-entry');
            
            // Format date nicely - parse the date in a timezone-safe manner
            // We deliberately avoid using `new Date(data.date)` because parsing
            // bare 'YYYY-MM-DD' strings is implementation-dependent and often
            // treated as UTC, which can cause off-by-one-day errors depending
            // on the user's timezone. Constructing the Date from (year, month - 1, day)
            // ensures consistent local calendar dates.
            const [year, month, day] = data.date.split('-').map(num => parseInt(num, 10));
            const dateObj = new Date(year, month - 1, day);
            const formattedDate = dateObj.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            tooltipDate.textContent = formattedDate;
            
            // Build tooltip body
            let bodyHTML = '';
            
            if (data.has_leave) {
                const leaveIcon = data.leave.leave_type === 'vacation' ? '🏖️' : '🤒';
                const leaveLabel = data.leave.leave_type === 'vacation' ? 'Vacation' : 'Sick Leave';
                const leaveIconAria = data.leave.leave_type === 'vacation' ? 'Vacation day' : 'Sick leave';
                bodyHTML += `<div class="tooltip-entry"><strong><span role="img" aria-label="${leaveIconAria}">${leaveIcon}</span> ${leaveLabel}</strong>`;
                if (data.leave.description) {
                    bodyHTML += `<br>${data.leave.description}`;
                }
                bodyHTML += '</div>';
            }
            
            if (data.has_entry) {
                bodyHTML += `<div><strong>Work Entries (${data.entry_count}):</strong></div>`;
                data.entries.forEach(entry => {
                    bodyHTML += `
                        <div class="tooltip-entry">
                            <div>${entry.start_time} - ${entry.end_time}</div>
                            <div><strong>${entry.duration_hours}h</strong> - ${entry.description}</div>
                        </div>
                    `;
                });
                bodyHTML += `<div style="margin-top: 0.5rem;"><strong>Total: ${data.total_hours}h</strong></div>`;
            } else if (!data.has_leave) {
                bodyHTML += '<div style="color: var(--text-secondary);"><span role="img" aria-label="Warning">⚠️</span> No entry for this day</div>';
            }
            
            tooltipBody.innerHTML = bodyHTML;
            
            // Update add entry link
            tooltipAddEntry.href = `/time-entry?date=${data.date}`;
            
            // Position tooltip
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            tooltip.style.display = 'block';
            
            // Get tooltip dimensions after making it visible
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Calculate position (try to center below the day)
            let left = rect.left + scrollLeft + (rect.width / 2) - (tooltipRect.width / 2);
            let top = rect.bottom + scrollTop + 10;
            
            // Keep tooltip within viewport horizontally
            if (left < 10) left = 10;
            if (left + tooltipRect.width > window.innerWidth - 10) {
                left = window.innerWidth - tooltipRect.width - 10;
            }
            
            // If tooltip goes below viewport, show above the day instead
            if (top + tooltipRect.height > scrollTop + window.innerHeight) {
                top = rect.top + scrollTop - tooltipRect.height - 10;
            }
            
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
        }
        
        function hideTooltip() {
            tooltip.style.display = 'none';
            currentTooltipDay = null;
        }
        
        // Hide tooltip when clicking outside
        document.addEventListener('click', function(e) {
            if (!tooltip.contains(e.target) && !e.target.closest('.calendar-day')) {
                hideTooltip();
            }
        });
        
        // Hide tooltip on scroll
        window.addEventListener('scroll', hideTooltip);
    }
});