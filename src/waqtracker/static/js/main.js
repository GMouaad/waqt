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
    
    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle icon
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }
    
    // Initialize theme immediately to prevent FOUC
    const initialTheme = getPreferredTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);
    
    // Set up theme toggle button when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Update icon after DOM is ready
        applyTheme(initialTheme);
        
        const themeToggle = document.getElementById('theme-toggle');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                applyTheme(newTheme);
            });
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // Only auto-switch if user hasn't manually set a preference that differs from system
                const storedTheme = localStorage.getItem('theme');
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const systemTheme = e.matches ? 'dark' : 'light';
                
                // Auto-switch only if no stored preference or stored preference matches system
                if (!storedTheme || currentTheme === systemTheme) {
                    applyTheme(systemTheme);
                }
            });
        }
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
                        preview.style.marginTop = '0.5rem';
                        preview.style.fontWeight = 'bold';
                        preview.className = 'text-info';
                        endTimeInput.parentElement.appendChild(preview);
                    }
                    preview.textContent = `Duration: ${durationText}`;
                }
            }
        }
        
        startTimeInput.addEventListener('change', updateDurationPreview);
        endTimeInput.addEventListener('change', updateDurationPreview);
    }
});
