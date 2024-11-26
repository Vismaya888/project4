document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('#chat-messages')) {
        loadMessages();
        scrollToBottom();
        
        // Clear notification badge when entering chat
        const messageBadge = document.querySelector('#message-badge');
        if (messageBadge) {
            messageBadge.style.display = 'none';
        }
        
        // Poll for new messages every 3 seconds
        setInterval(loadMessages, 3000);

        // Add event listener for Enter key in message input
        document.querySelector('#message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(e);
            }
        });

        // Update chat list every 10 seconds
        setInterval(updateChatList, 10000);
    }
});

function loadMessages() {
    const username = window.location.pathname.split('/').pop();
    fetch(`/n/messages/${username}`)
        .then(response => response.json())
        .then(messages => {
            const messagesDiv = document.querySelector('#chat-messages');
            let messageHTML = '';
            
            messages.forEach(message => {
                const isCurrentUser = message.sender === currentUser;
                messageHTML += `
                    <div class="message ${isCurrentUser ? 'sent' : 'received'}">
                        <div class="message-content">
                            ${message.content}
                            <div class="message-time grey">${message.timestamp}</div>
                        </div>
                    </div>
                `;
            });
            
            // Only update if messages have changed
            if (messageHTML !== messagesDiv.innerHTML) {
                messagesDiv.innerHTML = messageHTML;
                scrollToBottom();
            }
        })
        .catch(error => console.error('Error loading messages:', error));
}

function sendMessage(event) {
    event.preventDefault();
    const input = document.querySelector('#message-input');
    const content = input.value.trim();
    
    if (content) {
        const username = window.location.pathname.split('/').pop();
        fetch('/n/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                receiver: username,
                content: content
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                input.value = '';
                loadMessages();
            } else {
                console.error('Error sending message:', result.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    return false;
}

function scrollToBottom() {
    const messagesDiv = document.querySelector('#chat-messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Add unread message count update
function updateUnreadCount() {
    const chatUsers = document.querySelectorAll('.chat-user');
    chatUsers.forEach(user => {
        const username = user.dataset.username;
        fetch(`/n/messages/${username}/unread_count`)
            .then(response => response.json())
            .then(data => {
                const badge = user.querySelector('.unread-badge');
                if (data.count > 0) {
                    if (badge) {
                        badge.textContent = data.count;
                    } else {
                        const newBadge = document.createElement('div');
                        newBadge.className = 'unread-badge';
                        newBadge.textContent = data.count;
                        user.appendChild(newBadge);
                    }
                } else if (badge) {
                    badge.remove();
                }
            });
    });
}

// Update unread counts periodically
setInterval(updateUnreadCount, 5000);

// Add this function to update the chat list
function updateChatList() {
    if (!document.querySelector('.chat-users')) return;
    
    fetch('/n/chat')
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newChatUsers = doc.querySelector('.chat-users');
            const currentChatUsers = document.querySelector('.chat-users');
            
            if (newChatUsers && currentChatUsers) {
                currentChatUsers.innerHTML = newChatUsers.innerHTML;
            }
        })
        .catch(error => console.error('Error updating chat list:', error));
}
 