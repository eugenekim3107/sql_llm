document.getElementById('chat-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const userInput = document.getElementById('user-input').value;
    addMessage('user', userInput);
    document.getElementById('user-input').value = '';
    document.getElementById('user-input').disabled = true;

    const loadingMessage = addLoadingMessage();

    fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        removeMessage(loadingMessage);
        addMessage('bot', data.output_message);
        document.getElementById('user-input').disabled = false;
        document.getElementById('user-input').focus();
    })
    .catch(error => {
        console.error('Error:', error);
        removeMessage(loadingMessage);
        addMessage('bot', 'Sorry, something went wrong.');
        document.getElementById('user-input').disabled = false;
        document.getElementById('user-input').focus();
    });
});

function addMessage(sender, message) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    if (sender === 'bot') {
        const preElement = document.createElement('pre');
        preElement.textContent = message;
        messageElement.appendChild(preElement);
    } else {
        messageElement.textContent = message;
    }

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    return messageElement;
}

function addLoadingMessage() {
    const chatBox = document.getElementById('chat-box');
    const loadingElement = document.createElement('div');
    loadingElement.classList.add('message', 'loading');
    loadingElement.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
    chatBox.appendChild(loadingElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    return loadingElement;
}

function removeMessage(messageElement) {
    const chatBox = document.getElementById('chat-box');
    chatBox.removeChild(messageElement);
}
