const API_BASE = 'http://localhost:8000';

let currentFileName = '';

document.getElementById('fileInput').addEventListener('change', handleFileSelect);
document.getElementById('questionInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentFileName = file.name;
        document.getElementById('fileName').textContent = `Selected: ${file.name}`;
        uploadPDF(file);
    }
}

async function uploadPDF(file) {
    const formData = new FormData();
    formData.append('file', file);

    const progressBar = document.getElementById('uploadProgress');
    const progressFill = progressBar.querySelector('.progress-fill');
    const statusDiv = document.getElementById('uploadStatus');
    
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    progressFill.style.transition = 'none';
    statusDiv.textContent = 'Uploading and indexing...';
    statusDiv.className = 'status-message';

    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }
    }, 200);

    try {
        const response = await fetch(`${API_BASE}/upload_pdf`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        clearInterval(progressInterval);

        if (response.ok) {
            progressFill.style.transition = 'width 0.3s ease';
            progressFill.style.width = '100%';
            
            statusDiv.textContent = `✓ ${data.message} (${data.total_chunks} chunks)`;
            statusDiv.className = 'status-message success';
            
            setTimeout(() => {
                showChatSection(data.total_chunks);
            }, 500);
        } else {
            throw new Error(data.detail || 'Upload failed');
        }
    } catch (error) {
        clearInterval(progressInterval);
        statusDiv.textContent = `✗ Error: ${error.message}`;
        statusDiv.className = 'status-message error';
        progressBar.style.display = 'none';
    }
}

function showChatSection(chunkCount) {
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('chatSection').style.display = 'block';
    document.getElementById('docName').textContent = currentFileName;
    document.getElementById('chunkCount').textContent = `${chunkCount} chunks`;
}

async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question) return;

    addMessage(question, 'user');
    input.value = '';
    input.style.height = 'auto';

    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/ask_query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        removeLoadingMessage(loadingId);

        if (response.ok) {
            addMessage(data.answer, 'bot', data.confidence, data.sources);
        } else {
            throw new Error(data.detail || 'Query failed');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'bot', 0);
    }
}

function addMessage(text, type, confidence = null, sources = null) {
    const messagesDiv = document.getElementById('messages');
    const welcomeMsg = messagesDiv.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    if (type === 'bot' && confidence !== null) {
        const badge = document.createElement('div');
        badge.className = `confidence-badge ${getConfidenceClass(confidence)}`;
        badge.textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;
        contentDiv.appendChild(badge);

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';
            sourcesDiv.textContent = `📚 Sources: ${sources.length} chunks`;
            contentDiv.appendChild(sourcesDiv);
        }
    }

    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = 'loading-message';

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message-content loading';
    loadingDiv.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';

    messageDiv.appendChild(loadingDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return 'loading-message';
}

function removeLoadingMessage(id) {
    const loadingMsg = document.getElementById(id);
    if (loadingMsg) loadingMsg.remove();
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.7) return 'confidence-high';
    if (confidence >= 0.4) return 'confidence-medium';
    return 'confidence-low';
}

function resetApp() {
    document.getElementById('chatSection').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'flex';
    document.getElementById('messages').innerHTML = `
        <div class="welcome-message">
            <h3>👋 Ready to answer your questions!</h3>
            <p>Ask anything about the uploaded document</p>
        </div>
    `;
    document.getElementById('fileName').textContent = '';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('uploadStatus').textContent = '';
    document.getElementById('fileInput').value = '';
}
