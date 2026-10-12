const API_BASE = 'http://localhost:8000';

let currentFileName = '';
let currentDocumentId = null;
let authToken = localStorage.getItem('token') || null;

// ─── Boot ────────────────────────────────────────────────────────────────────

if (authToken) {
    showApp();
} else {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('appSection').style.display = 'none';
}

document.getElementById('fileInput').addEventListener('change', handleFileSelect);
document.getElementById('questionInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

// ─── Auth ────────────────────────────────────────────────────────────────────

function switchTab(tab) {
    document.getElementById('loginForm').style.display    = tab === 'login'    ? 'flex' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'flex' : 'none';
    document.querySelectorAll('.auth-tab').forEach((btn, i) => {
        btn.classList.toggle('active', (i === 0) === (tab === 'login'));
    });
}

async function login() {
    const email    = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const status   = document.getElementById('loginStatus');

    if (!email || !password) { status.textContent = 'Please fill in all fields.'; status.className = 'status-message error'; return; }

    status.textContent = 'Logging in...'; status.className = 'status-message';

    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);

    try {
        const res  = await fetch(`${API_BASE}/token`, { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        showApp();
    } catch (err) {
        status.textContent = `✗ ${err.message}`; status.className = 'status-message error';
    }
}

async function register() {
    const email    = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const status   = document.getElementById('registerStatus');

    if (!email || !password) { status.textContent = 'Please fill in all fields.'; status.className = 'status-message error'; return; }

    status.textContent = 'Registering...'; status.className = 'status-message';

    try {
        const res  = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');

        status.textContent = '✓ Registered! Please log in.'; status.className = 'status-message success';
        setTimeout(() => switchTab('login'), 1000);
    } catch (err) {
        status.textContent = `✗ ${err.message}`; status.className = 'status-message error';
    }
}

function logout() {
    authToken = null;
    currentDocumentId = null;
    localStorage.removeItem('token');
    document.getElementById('appSection').style.display  = 'none';
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('loginEmail').value    = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('loginStatus').textContent = '';
}

async function showApp() {
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('appSection').style.display  = 'block';

    try {
        const res  = await fetch(`${API_BASE}/me`, { headers: authHeaders() });
        const data = await res.json();
        if (res.ok) document.getElementById('userEmail').textContent = data.user?.email || '';
    } catch (_) {}

    loadDocuments();
    showUploadPanel();
}

function authHeaders(extra = {}) {
    return { 'Authorization': `Bearer ${authToken}`, ...extra };
}

// ─── Documents sidebar ───────────────────────────────────────────────────────

async function loadDocuments() {
    const list = document.getElementById('documentsList');
    list.innerHTML = '<div class="doc-loading">Loading...</div>';

    try {
        const res  = await fetch(`${API_BASE}/documents`, { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to load documents');

        if (!data.documents.length) {
            list.innerHTML = '<div class="doc-empty">No documents yet</div>';
            return;
        }

        list.innerHTML = '';
        data.documents.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'doc-item' + (doc.document_id === currentDocumentId ? ' active' : '');
            item.innerHTML = `
                <span class="doc-item-name" title="${doc.filename}">${doc.filename}</span>
                <div class="doc-item-actions">
                    <button class="btn-icon" title="Chat" onclick="selectDocument('${doc.document_id}','${doc.filename}')">💬</button>
                    <button class="btn-icon btn-danger" title="Delete" onclick="deleteDocument('${doc.document_id}', this)">🗑️</button>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        list.innerHTML = `<div class="doc-empty error">${err.message}</div>`;
    }
}

function selectDocument(documentId, filename) {
    currentDocumentId = documentId;
    currentFileName   = filename;
    showChatSection();
    loadDocuments(); // refresh active state
}

async function deleteDocument(documentId, btn) {
    if (!confirm('Delete this document?')) return;
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/documents/${documentId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Delete failed'); }

        if (currentDocumentId === documentId) {
            currentDocumentId = null;
            showUploadPanel();
        }
        loadDocuments();
    } catch (err) {
        alert(`Error: ${err.message}`);
        btn.disabled = false;
    }
}

// ─── Upload ──────────────────────────────────────────────────────────────────

function showUploadPanel() {
    document.getElementById('uploadSection').style.display = 'flex';
    document.getElementById('chatSection').style.display   = 'none';
}

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

    const progressBar  = document.getElementById('uploadProgress');
    const progressFill = progressBar.querySelector('.progress-fill');
    const statusDiv    = document.getElementById('uploadStatus');

    progressBar.style.display = 'block';
    progressFill.style.width  = '0%';
    progressFill.style.transition = 'none';
    statusDiv.textContent = 'Uploading and indexing...';
    statusDiv.className   = 'status-message';

    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) { progress += Math.random() * 15; if (progress > 90) progress = 90; }
        progressFill.style.width = progress + '%';
    }, 200);

    try {
        const res  = await fetch(`${API_BASE}/upload_pdf`, {
            method: 'POST',
            headers: authHeaders(),
            body: formData,
        });
        const data = await res.json();
        clearInterval(interval);

        if (!res.ok) throw new Error(data.detail || 'Upload failed');

        progressFill.style.transition = 'width 0.3s ease';
        progressFill.style.width      = '100%';
        statusDiv.textContent = `✓ ${data.message} (${data.total_chunks} chunks)`;
        statusDiv.className   = 'status-message success';

        currentDocumentId = data.document_id;
        setTimeout(() => { showChatSection(); loadDocuments(); }, 500);
    } catch (err) {
        clearInterval(interval);
        statusDiv.textContent = `✗ Error: ${err.message}`;
        statusDiv.className   = 'status-message error';
        progressBar.style.display = 'none';
    }
}

function showChatSection(chunkCount) {
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('chatSection').style.display   = 'block';
    document.getElementById('docName').textContent         = currentFileName;
    if (chunkCount !== undefined)
        document.getElementById('chunkCount').textContent = `${chunkCount} chunks`;
    else
        document.getElementById('chunkCount').textContent = '';
    // clear previous messages
    document.getElementById('messages').innerHTML = `
        <div class="welcome-message">
            <h3>👋 Ready to answer your questions!</h3>
            <p>Ask anything about <strong>${currentFileName}</strong></p>
        </div>`;
}

// ─── Query ───────────────────────────────────────────────────────────────────

async function sendQuestion() {
    const input    = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question || !currentDocumentId) return;

    addMessage(question, 'user');
    input.value = '';
    input.style.height = 'auto';

    const loadingId = addLoadingMessage();

    try {
        const res  = await fetch(`${API_BASE}/ask_query`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ question, document_id: currentDocumentId }),
        });
        const data = await res.json();
        removeLoadingMessage(loadingId);

        if (!res.ok) throw new Error(data.detail || 'Query failed');
        addMessage(data.answer, 'bot', data.confidence, data.sources, data.confidence_breakdown, data.latency_breakdown);
    } catch (err) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${err.message}`, 'bot', 0);
    }
}

// ─── Reset ───────────────────────────────────────────────────────────────────

function resetApp() {
    currentDocumentId = null;
    showUploadPanel();
    document.getElementById('messages').innerHTML = `
        <div class="welcome-message">
            <h3>👋 Ready to answer your questions!</h3>
            <p>Ask anything about the uploaded document</p>
        </div>`;
    document.getElementById('fileName').textContent          = '';
    document.getElementById('uploadProgress').style.display  = 'none';
    document.getElementById('uploadStatus').textContent      = '';
    document.getElementById('fileInput').value               = '';
}

// ─── Message rendering (unchanged logic) ─────────────────────────────────────

function addMessage(text, type, confidence = null, sources = null, breakdown = null, latency_breakdown = null) {
    const messagesDiv = document.getElementById('messages');
    const welcomeMsg  = messagesDiv.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    const messageDiv  = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const contentDiv  = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    if (type === 'bot' && confidence !== null) {
        const badge = document.createElement('div');
        badge.className = `confidence-badge ${getConfidenceClass(confidence)}`;
        badge.textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;
        contentDiv.appendChild(badge);

        if (latency_breakdown !== null) {
            const latencyBadge = document.createElement('div');
            latencyBadge.className = 'latency-badge';
            latencyBadge.textContent = `⚡ ${Math.round(latency_breakdown.total_ms)}ms`;
            contentDiv.appendChild(latencyBadge);

            const latencyBreakdownDiv = document.createElement('div');
            latencyBreakdownDiv.className = 'latency-breakdown';

            const latencyHeader = document.createElement('div');
            latencyHeader.className = 'breakdown-header';
            latencyHeader.onclick = function() { this.parentElement.classList.toggle('expanded'); };
            latencyHeader.innerHTML = '⚡ Latency Breakdown <span class="toggle-icon">▼</span>';

            const latencyContent = document.createElement('div');
            latencyContent.className = 'breakdown-content';

            const stages = [
                { key: 'query_rewriting_ms', label: 'Query Rewriting' },
                { key: 'embedding_ms', label: 'Embedding' },
                { key: 'hybrid_retrieval_ms', label: 'Hybrid Retrieval' },
                { key: 'normalisation_ms', label: 'Normalisation' },
                { key: 'calculation_ms', label: 'Score Calculation' },
                { key: 'reranking_ms', label: 'Reranking' },
                { key: 'generation_ms', label: 'LLM Generation' },
            ];

            stages.forEach(stage => {
                const value      = latency_breakdown[stage.key];
                const percentage = (value / latency_breakdown.total_ms * 100).toFixed(1);
                const item       = document.createElement('div');
                item.className   = 'breakdown-item';

                const labelDiv = document.createElement('div');
                labelDiv.className = 'breakdown-label';
                labelDiv.innerHTML = `<span>${stage.label}</span>`;

                const barContainer = document.createElement('div');
                barContainer.className = 'breakdown-bar-container';

                const bar = document.createElement('div');
                bar.className = 'breakdown-bar';
                bar.style.width = `${percentage}%`;
                bar.style.backgroundColor = value < 100 ? '#10b981' : value < 300 ? '#f59e0b' : '#ef4444';

                barContainer.appendChild(bar);

                const valueSpan = document.createElement('span');
                valueSpan.className = 'breakdown-value';
                valueSpan.textContent = `${Math.round(value)}ms (${percentage}%)`;

                item.appendChild(labelDiv);
                item.appendChild(barContainer);
                item.appendChild(valueSpan);
                latencyContent.appendChild(item);
            });

            latencyBreakdownDiv.appendChild(latencyHeader);
            latencyBreakdownDiv.appendChild(latencyContent);
            contentDiv.appendChild(latencyBreakdownDiv);
        }

        if (breakdown) {
            const breakdownDiv = document.createElement('div');
            breakdownDiv.className = 'confidence-breakdown';

            const breakdownHeader = document.createElement('div');
            breakdownHeader.className = 'breakdown-header';
            breakdownHeader.onclick = function() { this.parentElement.classList.toggle('expanded'); };

            breakdownHeader.appendChild(document.createTextNode('📊 Confidence Breakdown '));

            const infoIcon = document.createElement('span');
            infoIcon.className = 'formula-info';
            infoIcon.textContent = 'i';
            infoIcon.title = 'Click to see formula details';
            infoIcon.onclick = (e) => { e.stopPropagation(); toggleFormulaModal(); };
            breakdownHeader.appendChild(infoIcon);

            const toggleIcon = document.createElement('span');
            toggleIcon.className = 'toggle-icon';
            toggleIcon.textContent = '▼';
            breakdownHeader.appendChild(toggleIcon);

            const breakdownContent = document.createElement('div');
            breakdownContent.className = 'breakdown-content';
            breakdownContent.innerHTML = `
                <div class="breakdown-item">
                    <div class="breakdown-label"><span>Mean Relevance</span><span class="breakdown-weight">(50% weight)</span></div>
                    <div class="breakdown-bar-container"><div class="breakdown-bar" style="width:${(breakdown.mean_score*100).toFixed(0)}%"></div></div>
                    <span class="breakdown-value">${(breakdown.mean_score*100).toFixed(0)}%</span>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label"><span>Agreement</span><span class="breakdown-weight">(30% weight)</span></div>
                    <div class="breakdown-bar-container"><div class="breakdown-bar" style="width:${(breakdown.agreement*100).toFixed(0)}%"></div></div>
                    <span class="breakdown-value">${(breakdown.agreement*100).toFixed(0)}%</span>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label"><span>Dominance</span><span class="breakdown-weight">(20% weight)</span></div>
                    <div class="breakdown-bar-container"><div class="breakdown-bar" style="width:${(breakdown.dominance*100).toFixed(0)}%"></div></div>
                    <span class="breakdown-value">${(breakdown.dominance*100).toFixed(0)}%</span>
                </div>
                <div class="breakdown-explanation">${getConfidenceExplanation(breakdown)}</div>
                <div class="breakdown-calculation">
                    <strong>Final Calculation:</strong><br>
                    ${(breakdown.mean_score*100).toFixed(1)}% × 0.5 + ${(breakdown.agreement*100).toFixed(1)}% × 0.3 + ${(breakdown.dominance*100).toFixed(1)}% × 0.2 = <strong>${(confidence*100).toFixed(0)}%</strong>
                </div>`;

            breakdownDiv.appendChild(breakdownHeader);
            breakdownDiv.appendChild(breakdownContent);
            contentDiv.appendChild(breakdownDiv);
        }

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';

            const sourcesHeader = document.createElement('div');
            sourcesHeader.className = 'sources-header';
            sourcesHeader.onclick = () => sourcesDiv.classList.toggle('expanded');
            sourcesHeader.innerHTML = `📚 Sources: ${sources.length} chunks <span class="toggle-icon">▼</span>`;

            const sourcesList = document.createElement('div');
            sourcesList.className = 'sources-list';
            sources.forEach((source, idx) => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `
                    <span class="source-rank">#${idx + 1}</span>
                    <span class="source-id">${source.chunk_id}</span>
                    <span class="source-score">${(source.score * 100).toFixed(1)}%</span>
                    <button class="view-chunk-btn" title="View chunk text">👁️</button>`;

                sourceItem.querySelector('.view-chunk-btn').onclick = (e) => {
                    e.stopPropagation();
                    showChunkModal(source.text, source.chunk_id, source.score);
                };
                sourcesList.appendChild(sourceItem);
            });

            sourcesDiv.appendChild(sourcesHeader);
            sourcesDiv.appendChild(sourcesList);
            contentDiv.appendChild(sourcesDiv);
        }
    }

    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function getConfidenceExplanation(breakdown) {
    const { mean_score: mean, agreement, dominance } = breakdown;
    if (mean < 0.3)                          return '⚠️ Low confidence: Retrieved chunks have weak relevance to the query.';
    if (agreement < 0.5)                     return '⚠️ Low confidence: High disagreement between retrieved chunks.';
    if (dominance < 0.2 && mean < 0.6)      return '⚠️ Moderate confidence: No single chunk clearly dominates.';
    if (mean >= 0.65 && dominance >= 0.3)   return '✅ High confidence: Strong relevance with a clear best match.';
    if (mean >= 0.6)                         return '✅ Good confidence: Multiple relevant chunks support the answer.';
    return 'ℹ️ Moderate confidence: Reasonable relevance but some uncertainty remains.';
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('messages');
    const messageDiv  = document.createElement('div');
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
    const el = document.getElementById(id);
    if (el) el.remove();
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.7) return 'confidence-high';
    if (confidence >= 0.4) return 'confidence-medium';
    return 'confidence-low';
}

// ─── Modals (unchanged) ───────────────────────────────────────────────────────

function toggleFormulaModal() {
    const modal = document.getElementById('formulaModal');
    if (!modal) { createFormulaModal(); return; }
    modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
}

function createFormulaModal() {
    const modal = document.createElement('div');
    modal.id = 'formulaModal';
    modal.className = 'formula-modal';
    modal.innerHTML = `
        <div class="formula-modal-content">
            <div class="formula-modal-header">
                <h3>🧮 Confidence Scoring Formula</h3>
                <span class="formula-close" onclick="toggleFormulaModal()">×</span>
            </div>
            <div class="formula-modal-body">
                <div class="formula-section">
                    <h4>Core Formula</h4>
                    <div class="formula-box">Confidence = 0.5 × Mean Score + 0.3 × Agreement + 0.2 × Dominance</div>
                </div>
                <div class="formula-section">
                    <h4>Component Breakdown</h4>
                    <div class="formula-component">
                        <strong>1. Mean Relevance Score (50% weight)</strong>
                        <p>Average reranking score from cross-encoder model</p>
                        <ul><li>Range: 0.0 (irrelevant) to 1.0 (highly relevant)</li></ul>
                    </div>
                    <div class="formula-component">
                        <strong>2. Agreement (30% weight)</strong>
                        <p>Formula: 1 / (1 + variance)</p>
                        <ul><li>Range: 0.0 (high disagreement) to 1.0 (perfect agreement)</li></ul>
                    </div>
                    <div class="formula-component">
                        <strong>3. Dominance (20% weight)</strong>
                        <p>Formula: Top Score − Second Score</p>
                        <ul><li>Range: 0.0 (no clear winner) to 1.0 (dominant chunk)</li></ul>
                    </div>
                </div>
            </div>
        </div>`;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.addEventListener('click', (e) => { if (e.target === modal) toggleFormulaModal(); });
}

function showChunkModal(text, chunkId, score) {
    const existing = document.getElementById('chunkModal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = 'chunkModal';
    modal.className = 'chunk-modal';
    modal.innerHTML = `
        <div class="chunk-modal-content">
            <div class="chunk-modal-header">
                <h3>📝 Chunk Preview</h3>
                <span class="chunk-modal-close" onclick="closeChunkModal()">×</span>
            </div>
            <div class="chunk-modal-body">
                <div class="chunk-info">
                    <div class="chunk-info-item"><strong>Chunk ID:</strong> ${chunkId}</div>
                    <div class="chunk-info-item"><strong>Relevance Score:</strong> <span class="chunk-score-badge">${(score*100).toFixed(1)}%</span></div>
                </div>
                <div class="chunk-text-container">
                    <div class="chunk-text-label">Chunk Text:</div>
                    <div class="chunk-text">${text}</div>
                </div>
            </div>
        </div>`;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.addEventListener('click', (e) => { if (e.target === modal) closeChunkModal(); });
}

function closeChunkModal() {
    const modal = document.getElementById('chunkModal');
    if (modal) modal.remove();
}
