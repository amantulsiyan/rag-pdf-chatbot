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
            addMessage(data.answer, 'bot', data.confidence, data.sources, data.confidence_breakdown, data.latency_breakdown);
        } else {
            throw new Error(data.detail || 'Query failed');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'bot', 0);
    }
}

function addMessage(text, type, confidence = null, sources = null, breakdown = null, latency_breakdown = null) {
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

        // Add latency badge and breakdown
        if (latency_breakdown !== null) {
            const latencyBadge = document.createElement('div');
            latencyBadge.className = 'latency-badge';
            latencyBadge.textContent = `⚡ ${Math.round(latency_breakdown.total_ms)}ms`;
            contentDiv.appendChild(latencyBadge);

            // Add latency breakdown
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
                { key: 'generation_ms', label: 'LLM Generation' }
            ];

            stages.forEach(stage => {
                const value = latency_breakdown[stage.key];
                const percentage = (value / latency_breakdown.total_ms * 100).toFixed(1);
                
                const item = document.createElement('div');
                item.className = 'breakdown-item';
                
                const labelDiv = document.createElement('div');
                labelDiv.className = 'breakdown-label';
                labelDiv.innerHTML = `<span>${stage.label}</span>`;
                
                const barContainer = document.createElement('div');
                barContainer.className = 'breakdown-bar-container';
                
                const bar = document.createElement('div');
                bar.className = 'breakdown-bar';
                bar.style.width = `${percentage}%`;
                
                // Color code by speed: green (<100ms), yellow (100-300ms), red (>300ms)
                if (value < 100) {
                    bar.style.backgroundColor = '#10b981';
                } else if (value < 300) {
                    bar.style.backgroundColor = '#f59e0b';
                } else {
                    bar.style.backgroundColor = '#ef4444';
                }
                
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

        // Add confidence breakdown
        if (breakdown) {
            const breakdownDiv = document.createElement('div');
            breakdownDiv.className = 'confidence-breakdown';
            
            const breakdownHeader = document.createElement('div');
            breakdownHeader.className = 'breakdown-header';
            breakdownHeader.onclick = function() { this.parentElement.classList.toggle('expanded'); };
            
            const headerText = document.createTextNode('📊 Confidence Breakdown ');
            breakdownHeader.appendChild(headerText);
            
            const infoIcon = document.createElement('span');
            infoIcon.className = 'formula-info';
            infoIcon.textContent = 'i';
            infoIcon.title = 'Click to see formula details';
            infoIcon.onclick = function(e) { 
                e.stopPropagation(); 
                toggleFormulaModal(); 
            };
            breakdownHeader.appendChild(infoIcon);
            
            const toggleIcon = document.createElement('span');
            toggleIcon.className = 'toggle-icon';
            toggleIcon.textContent = '▼';
            breakdownHeader.appendChild(toggleIcon);
            
            const breakdownContent = document.createElement('div');
            breakdownContent.className = 'breakdown-content';
            breakdownContent.innerHTML = `
                    <div class="breakdown-item">
                        <div class="breakdown-label">
                            <span>Mean Relevance</span>
                            <span class="breakdown-weight">(50% weight)</span>
                        </div>
                        <div class="breakdown-bar-container">
                            <div class="breakdown-bar" style="width: ${(breakdown.mean_score * 100).toFixed(0)}%"></div>
                        </div>
                        <span class="breakdown-value">${(breakdown.mean_score * 100).toFixed(0)}%</span>
                    </div>
                    <div class="breakdown-item">
                        <div class="breakdown-label">
                            <span>Agreement</span>
                            <span class="breakdown-weight">(30% weight)</span>
                        </div>
                        <div class="breakdown-bar-container">
                            <div class="breakdown-bar" style="width: ${(breakdown.agreement * 100).toFixed(0)}%"></div>
                        </div>
                        <span class="breakdown-value">${(breakdown.agreement * 100).toFixed(0)}%</span>
                    </div>
                    <div class="breakdown-item">
                        <div class="breakdown-label">
                            <span>Dominance</span>
                            <span class="breakdown-weight">(20% weight)</span>
                        </div>
                        <div class="breakdown-bar-container">
                            <div class="breakdown-bar" style="width: ${(breakdown.dominance * 100).toFixed(0)}%"></div>
                        </div>
                        <span class="breakdown-value">${(breakdown.dominance * 100).toFixed(0)}%</span>
                    </div>
                    <div class="breakdown-explanation">
                        ${getConfidenceExplanation(breakdown)}
                    </div>
                    <div class="breakdown-calculation">
                        <strong>Final Calculation:</strong><br>
                        ${(breakdown.mean_score * 100).toFixed(1)}% × 0.5 + 
                        ${(breakdown.agreement * 100).toFixed(1)}% × 0.3 + 
                        ${(breakdown.dominance * 100).toFixed(1)}% × 0.2 = 
                        <strong>${(confidence * 100).toFixed(0)}%</strong>
                    </div>
            `;
            
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
                    <button class="view-chunk-btn" title="View chunk text">👁️</button>
                `;
                
                // Add click handler for view button
                const viewBtn = sourceItem.querySelector('.view-chunk-btn');
                viewBtn.onclick = (e) => {
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
    const mean = breakdown.mean_score;
    const agreement = breakdown.agreement;
    const dominance = breakdown.dominance;
    
    if (mean < 0.3) {
        return "⚠️ Low confidence: Retrieved chunks have weak relevance to the query.";
    } else if (agreement < 0.5) {
        return "⚠️ Low confidence: High disagreement between retrieved chunks (conflicting information).";
    } else if (dominance < 0.2 && mean < 0.6) {
        return "⚠️ Moderate confidence: No single chunk clearly dominates, evidence is distributed.";
    } else if (mean >= 0.65 && dominance >= 0.3) {
        return "✅ High confidence: Strong relevance with a clear best match.";
    } else if (mean >= 0.6) {
        return "✅ Good confidence: Multiple relevant chunks support the answer.";
    } else {
        return "ℹ️ Moderate confidence: Reasonable relevance but some uncertainty remains.";
    }
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

function toggleFormulaModal() {
    const modal = document.getElementById('formulaModal');
    if (!modal) {
        createFormulaModal();
    } else {
        modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
    }
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
                    <div class="formula-box">
                        Confidence = 0.5 × Mean Score + 0.3 × Agreement + 0.2 × Dominance
                    </div>
                </div>

                <div class="formula-section">
                    <h4>Component Breakdown</h4>
                    
                    <div class="formula-component">
                        <strong>1. Mean Relevance Score (50% weight)</strong>
                        <p>Average reranking score from cross-encoder model (ms-marco-MiniLM-L-6-v2)</p>
                        <ul>
                            <li>Measures: How relevant are retrieved chunks to the query?</li>
                            <li>Range: 0.0 (irrelevant) to 1.0 (highly relevant)</li>
                            <li>Low value means: Weak retrieval, chunks don't match query well</li>
                        </ul>
                    </div>

                    <div class="formula-component">
                        <strong>2. Agreement (30% weight)</strong>
                        <p>Formula: 1 / (1 + variance)</p>
                        <ul>
                            <li>Measures: Do all chunks agree (similar scores)?</li>
                            <li>Range: 0.0 (high disagreement) to 1.0 (perfect agreement)</li>
                            <li>Low value means: Conflicting evidence, inconsistent chunk quality</li>
                        </ul>
                    </div>

                    <div class="formula-component">
                        <strong>3. Dominance (20% weight)</strong>
                        <p>Formula: Top Score - Second Score</p>
                        <ul>
                            <li>Measures: Is there a clear "best" chunk?</li>
                            <li>Range: 0.0 (no clear winner) to 1.0 (dominant chunk)</li>
                            <li>Low value means: Evidence is distributed, no single authoritative source</li>
                        </ul>
                    </div>
                </div>

                <div class="formula-section">
                    <h4>Why This Design?</h4>
                    <ul>
                        <li><strong>Retrieval-based:</strong> Confidence comes from reranker scores, NOT LLM self-assessment</li>
                        <li><strong>Honest uncertainty:</strong> Low scores trigger "I don't know" responses</li>
                        <li><strong>Explainable:</strong> Each component reveals WHY confidence is high/low</li>
                        <li><strong>Hallucination control:</strong> Prevents fluent but incorrect answers</li>
                    </ul>
                </div>

                <div class="formula-section">
                    <h4>Example Scenarios</h4>
                    <div class="formula-example">
                        <strong>High Confidence (75%):</strong> Mean=0.8, Agreement=0.9, Dominance=0.5<br>
                        → Strong retrieval + chunks agree + clear best match
                    </div>
                    <div class="formula-example">
                        <strong>Low Confidence (32%):</strong> Mean=0.25, Agreement=0.85, Dominance=0.1<br>
                        → Weak retrieval despite agreement, no dominant chunk
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) toggleFormulaModal();
    });
}

function showChunkModal(text, chunkId, score) {
    // Remove existing chunk modal if any
    const existingModal = document.getElementById('chunkModal');
    if (existingModal) existingModal.remove();
    
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
                    <div class="chunk-info-item">
                        <strong>Chunk ID:</strong> ${chunkId}
                    </div>
                    <div class="chunk-info-item">
                        <strong>Relevance Score:</strong> 
                        <span class="chunk-score-badge">${(score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                <div class="chunk-text-container">
                    <div class="chunk-text-label">Chunk Text:</div>
                    <div class="chunk-text">${text}</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeChunkModal();
    });
}

function closeChunkModal() {
    const modal = document.getElementById('chunkModal');
    if (modal) modal.remove();
}
