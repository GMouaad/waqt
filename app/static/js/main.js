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
                        preview.style.color = '#3498db';
                        preview.style.fontWeight = 'bold';
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
