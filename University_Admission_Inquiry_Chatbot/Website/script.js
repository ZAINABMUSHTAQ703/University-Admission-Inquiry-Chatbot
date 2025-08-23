// Chat history for display when the chatbot is closed/reopened
let chatHistory = JSON.parse(sessionStorage.getItem('chatHistory')) || [];

// Message history for up/down arrow navigation
let messageHistory = JSON.parse(sessionStorage.getItem('messageHistory')) || [];
let currentHistoryIndex = -1;

function toggleChatbot() {
    const chatbot = document.getElementById('chatbot');
    if (chatbot.style.display === 'flex') {
        closeChatbot();
    } else {
        openChatbot();
    }
}

function openChatbot() {
    const chatbot = document.getElementById('chatbot');
    chatbot.style.display = 'flex';
    // Restore chat history from sessionStorage
    if (chatHistory.length > 0) {
        const messagesDiv = document.getElementById('chatbot-messages');
        messagesDiv.innerHTML = '';
        chatHistory.forEach(msg => {
            addMessage(msg.sender, msg.text, false); // false means don't add to history again
        });
    }
}

function closeChatbot() {
    const chatbot = document.getElementById('chatbot');
    chatbot.style.display = 'none';
    // Save both chat and message history
    saveChatHistory();
    sessionStorage.setItem('messageHistory', JSON.stringify(messageHistory));
}

function saveChatHistory() {
    const messagesDiv = document.getElementById('chatbot-messages');
    const messages = messagesDiv.querySelectorAll('div');
    chatHistory = Array.from(messages).map(msg => ({
        sender: msg.style.alignSelf === 'flex-end' ? 'user' : 'bot',
        text: msg.textContent
    }));
    sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

function showTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'block';
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'none';
}

function sendMessage() {
    const inputField = document.getElementById('chatbot-input-field');
    const message = inputField.value.trim();
    if (message === '') return;

    // Add user message to chat
    addMessage('user', message);
    
    // Store the message in history (only if not empty and different from last message)
    if (messageHistory.length === 0 || message !== messageHistory[messageHistory.length - 1]) {
        messageHistory.push(message);
        sessionStorage.setItem('messageHistory', JSON.stringify(messageHistory));
    }
    
    // Reset history index
    currentHistoryIndex = -1;
    inputField.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to Rasa backend
    fetch('http://localhost:5005/webhooks/rest/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            sender: 'user_' + Date.now(),  // Unique sender ID
            message: message
        }),
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        // Handle Rasa's response
        data.forEach(response => {
            if (response.text) {
                addMessage('bot', response.text);
            }
        });
    })
    .catch(error => {
        hideTypingIndicator();
        addMessage('bot', "Sorry, I'm having trouble connecting to the server. Please try again later.");
        console.error('Error:', error);
    });
}

function addMessage(sender, text, saveToHistory = true) {
    const messagesDiv = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.style.margin = '5px';
    messageDiv.style.padding = '8px';
    messageDiv.style.borderRadius = '5px';
    messageDiv.style.maxWidth = '80%';
    messageDiv.style.wordWrap = 'break-word';
    messageDiv.style.backgroundColor = sender === 'user' ? '#001a33' : '#f1f1f1';
    messageDiv.style.alignSelf = sender === 'user' ? 'flex-end' : 'flex-start';
    
    // Handle both markdown-style and direct URLs with proper encoding
    const withLinks = text.replace(
        /(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s<]+)/g, 
        (match, markdown, text, url, directUrl) => {
            try {
                if (url) {
                    const encodedUrl = encodeURI(url.trim());
                    return `<a href="${encodedUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();">${text || encodedUrl}</a>`;
                } else if (directUrl) {
                    const encodedUrl = encodeURI(directUrl.trim());
                    return `<a href="${encodedUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();">${encodedUrl}</a>`;
                }
                return match;
            } catch (e) {
                console.error('Error processing URL:', e);
                return match;
            }
        }
    );
    
    messageDiv.innerHTML = withLinks;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    if (saveToHistory) {
        chatHistory.push({ sender, text });
    }
}

// Prevent chat window from closing when clicking links
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.closest('#chatbot-messages')) {
        e.stopPropagation();
    }
});

function handleKeyDown(e) {
    const inputField = document.getElementById('chatbot-input-field');
    
    if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (messageHistory.length === 0) return;
        
        if (currentHistoryIndex < messageHistory.length - 1) {
            currentHistoryIndex++;
            inputField.value = messageHistory[messageHistory.length - 1 - currentHistoryIndex];
        }
    } 
    else if (e.key === 'ArrowDown') {
        e.preventDefault();
        
        if (currentHistoryIndex > 0) {
            currentHistoryIndex--;
            inputField.value = messageHistory[messageHistory.length - 1 - currentHistoryIndex];
        } 
        else if (currentHistoryIndex === 0) {
            currentHistoryIndex = -1;
            inputField.value = '';
        }
    }
    else if (e.key === 'Enter') {
        sendMessage();
    }
}

// Clear both histories when page is refreshed
window.addEventListener('beforeunload', function() {
    sessionStorage.removeItem('chatHistory');
    sessionStorage.removeItem('messageHistory');
});

// Initialize event listeners
document.getElementById('chatbot-input-field').addEventListener('keydown', handleKeyDown);