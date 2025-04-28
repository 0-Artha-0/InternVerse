/**
 * Main JavaScript file for Virtual Internship Simulator
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize AI Supervisor Chat
    initializeAISupervisor();

    // Task submission form validation
    initializeTaskSubmission();

    // Profile form validation
    initializeProfileValidation();
});

/**
 * Initialize AI Supervisor Chat functionality
 */
function initializeAISupervisor() {
    const chatContainer = document.getElementById('ai-supervisor-chat');
    if (!chatContainer) return;

    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const internshipId = chatContainer.dataset.internshipId || '';
    const taskId = chatContainer.dataset.taskId || '';

    // Add welcome message
    addMessage('Welcome to your virtual internship! I\'m your AI supervisor. How can I help you today?', 'bot');

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot typing-indicator';
        typingIndicator.innerHTML = '<span>Typing</span><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to AI supervisor API
        fetch('/api/supervisor/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                internship_id: internshipId,
                task_id: taskId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            chatMessages.removeChild(typingIndicator);
            
            // Add bot response
            addMessage(data.response, 'bot');
        })
        .catch(error => {
            console.error('Error:', error);
            // Remove typing indicator
            chatMessages.removeChild(typingIndicator);
            
            // Add error message
            addMessage('Sorry, I\'m having trouble processing your request. Please try again later.', 'bot');
        });
    });

    /**
     * Add a message to the chat container
     * @param {string} text - Message text
     * @param {string} sender - Message sender ('user' or 'bot')
     */
    function addMessage(text, sender) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;
        // Use innerHTML instead of textContent to allow styling
        const messageP = document.createElement('p');
        messageP.textContent = text;
        messageP.style.margin = '0';
        
        // Ensure proper text color based on sender
        if (sender === 'user') {
            messageP.style.color = 'white';
        } else {
            messageP.style.color = '#333333';
        }
        
        messageEl.appendChild(messageP);
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Initialize task submission form validation
 */
function initializeTaskSubmission() {
    const taskForm = document.getElementById('task-submission-form');
    if (!taskForm) return;

    taskForm.addEventListener('submit', function(e) {
        const contentField = document.getElementById('content');
        if (contentField.value.trim() === '') {
            e.preventDefault();
            alert('Please provide your submission content.');
            return false;
        }
        
        // Disable submit button to prevent double submission
        const submitButton = taskForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
    });
}

/**
 * Initialize profile form validation
 */
function initializeProfileValidation() {
    const profileForm = document.getElementById('profile-form');
    if (!profileForm) return;

    profileForm.addEventListener('submit', function(e) {
        const fullName = document.getElementById('full_name');
        const major = document.getElementById('major');
        const university = document.getElementById('university');
        
        if (fullName.value.trim() === '') {
            e.preventDefault();
            alert('Please enter your full name.');
            fullName.focus();
            return false;
        }
        
        if (major.value.trim() === '') {
            e.preventDefault();
            alert('Please enter your major.');
            major.focus();
            return false;
        }
        
        if (university.value.trim() === '') {
            e.preventDefault();
            alert('Please enter your university.');
            university.focus();
            return false;
        }
    });
}

/**
 * Progress bar animation
 */
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(progressBar => {
        const value = progressBar.getAttribute('aria-valuenow');
        progressBar.style.width = '0%';
        setTimeout(() => {
            progressBar.style.width = value + '%';
        }, 100);
    });
}

// Animate progress bars when page loads
window.addEventListener('load', animateProgressBars);
