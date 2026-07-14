document.addEventListener('DOMContentLoaded', () => {
    // State
    let activePaper = null;
    let papers = [];
    const pollingIntervals = {};

    // DOM Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const papersList = document.getElementById('papersList');
    const noSelectionState = document.getElementById('noSelectionState');
    const activeWorkspace = document.getElementById('activeWorkspace');
    
    // Breakdown Sheet Elements
    const paperTitle = document.getElementById('paperTitle');
    const paperAuthors = document.getElementById('paperAuthors');
    const paperVenue = document.getElementById('paperVenue');
    const paperTldr = document.getElementById('paperTldr');
    const paperMethodology = document.getElementById('paperMethodology');
    const paperContributions = document.getElementById('paperContributions');
    const paperResults = document.getElementById('paperResults');
    const paperLimitations = document.getElementById('paperLimitations');
    const paperKeywords = document.getElementById('paperKeywords');
    const copyCitationBtn = document.getElementById('copyCitationBtn');
    
    // Companion Q&A Elements
    const citationStyle = document.getElementById('citationStyle');
    const chatLog = document.getElementById('chatLog');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const toast = document.getElementById('toast');
    const paperReferences = document.getElementById('paperReferences');
    
    // Custom Delete Confirmation Modal Elements
    const deleteModal = document.getElementById('deleteModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    let deleteTargetId = null;

    cancelDeleteBtn.addEventListener('click', () => {
        deleteModal.classList.remove('show');
        setTimeout(() => { deleteModal.style.display = 'none'; }, 200);
        deleteTargetId = null;
    });

    confirmDeleteBtn.addEventListener('click', () => {
        if (deleteTargetId) {
            performDelete(deleteTargetId);
        }
        deleteModal.classList.remove('show');
        setTimeout(() => { deleteModal.style.display = 'none'; }, 200);
    });

    // Init Lucide
    lucide.createIcons();

    // Fetch initial library list
    fetchPapers();

    // 1. Dropzone Upload Interactions
    dropzone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropzone.addEventListener(type, () => {
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // 2. Upload Action
    async function handleFileUpload(file) {
        if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
            showToast('Only PDF files are supported.', 'error');
            return;
        }

        showToast('Uploading paper to catalog...', 'info');
        dropzone.classList.add('busy');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/papers/upload', {
                method: 'POST',
                body: formData
            });

            dropzone.classList.remove('busy');

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Upload failed');
            }

            const paper = await res.json();
            showToast('Upload successful. Analyzing paper...', 'success');
            
            // Refresh list & select the new paper
            await fetchPapers();
            selectPaper(paper.id);
        } catch (error) {
            dropzone.classList.remove('busy');
            console.error('Upload error:', error);
            showToast(error.message, 'error');
        }
    }

    // 3. Fetch Papers List
    async function fetchPapers() {
        try {
            const res = await fetch('/api/papers/');
            if (!res.ok) throw new Error('Failed to load catalog');
            
            papers = await res.json();
            renderPapersList();
        } catch (error) {
            console.error('Error fetching papers:', error);
            showToast(error.message, 'error');
        }
    }

    // 4. Render Catalog Sidebar List
    function renderPapersList() {
        if (papers.length === 0) {
            papersList.innerHTML = `
                <div class="empty-library">
                    <p>No papers uploaded yet.</p>
                </div>
            `;
            return;
        }

        papersList.innerHTML = papers.map(p => {
            const isActive = activePaper && activePaper.id === p.id ? 'active' : '';
            return `
                <div class="catalog-card ${isActive}" data-id="${p.id}">
                    <h3 class="catalog-card-title">${escapeHTML(p.title || p.filename)}</h3>
                    <div class="catalog-card-meta">
                        <span>${escapeHTML(p.filename)}</span>
                        <span class="badge badge-${p.status}">${p.status}</span>
                    </div>
                    <button class="catalog-card-delete" data-id="${p.id}" title="Delete from catalog">
                        <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
                    </button>
                </div>
            `;
        }).join('');

        lucide.createIcons();

        // Catalog selections
        document.querySelectorAll('.catalog-card').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.catalog-card-delete')) return;
                const id = item.getAttribute('data-id');
                selectPaper(id);
            });
        });

        // Catalog deletion
        document.querySelectorAll('.catalog-card-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                deletePaper(id);
            });
        });

        // Check for processing papers and start polling
        papers.forEach(p => {
            if (p.status === 'processing' && !pollingIntervals[p.id]) {
                startPolling(p.id);
            }
        });
    }

    // 5. Polling for Paper Status
    function startPolling(id) {
        pollingIntervals[id] = setInterval(async () => {
            try {
                const res = await fetch(`/api/papers/${id}`);
                if (!res.ok) {
                    clearInterval(pollingIntervals[id]);
                    delete pollingIntervals[id];
                    return;
                }
                const paper = await res.json();
                
                if (paper.status !== 'processing') {
                    clearInterval(pollingIntervals[id]);
                    delete pollingIntervals[id];
                    
                    // Update state & list
                    const idx = papers.findIndex(p => p.id === id);
                    if (idx !== -1) papers[idx] = paper;
                    
                    renderPapersList();

                    if (activePaper && activePaper.id === id) {
                        selectPaper(id);
                    }
                    
                    if (paper.status === 'ready') {
                        showToast(`Analysis complete: "${paper.title || paper.filename}"`, 'success');
                    } else {
                        showToast(`Analysis failed: ${paper.error_message}`, 'error');
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 1500);
    }

    // 6. Select Paper & Update Breakdown Sheet
    async function selectPaper(id) {
        let paper = papers.find(p => p.id === id);
        if (!paper) return;

        activePaper = paper;
        
        // Highlight active sidebar item
        document.querySelectorAll('.catalog-card').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-id') === id);
        });

        if (paper.status === 'processing') {
            noSelectionState.style.display = 'block';
            activeWorkspace.style.display = 'none';
            noSelectionState.innerHTML = `
                <div class="empty-state" style="text-align: center;">
                    <div class="loader-compass">
                        <div class="compass-needle"></div>
                    </div>
                    <div class="empty-eyebrow">Structured Analysis</div>
                    <h1>Analyzing Article...</h1>
                    <p class="empty-sub" style="margin: 0 auto;">We are currently parsing PDF lines, extracting page structures, and running summary generation. This will take a moment...</p>
                </div>
            `;
            return;
        }

        if (paper.status === 'error') {
            noSelectionState.style.display = 'block';
            activeWorkspace.style.display = 'none';
            noSelectionState.innerHTML = `
                <div class="empty-state">
                    <div class="empty-eyebrow">Analysis Failed</div>
                    <h1 style="color: var(--burgundy-bright);">Extraction Error</h1>
                    <p class="empty-sub">${escapeHTML(paper.error_message)}</p>
                </div>
            `;
            return;
        }

        // Display page layout
        noSelectionState.style.display = 'none';
        activeWorkspace.style.display = 'block';

        // Render header details
        paperTitle.textContent = paper.title || 'Untitled Article';
        paperAuthors.textContent = paper.authors.join(', ') || 'Unknown Authors';
        paperVenue.textContent = (paper.venue || 'Unknown Venue') + (paper.year ? ` (${paper.year})` : '');

        // Render sheet contents
        paperTldr.textContent = paper.tldr || 'No summary generated.';
        paperMethodology.textContent = paper.methodology || 'No methodology data extracted.';

        // Contributions list
        if (paper.contributions && paper.contributions.length > 0) {
            paperContributions.innerHTML = paper.contributions.map(c => `<li>${escapeHTML(c)}</li>`).join('');
        } else {
            paperContributions.innerHTML = `<li>No contributions listed.</li>`;
        }

        paperResults.textContent = paper.results || 'No results data extracted.';
        paperLimitations.textContent = paper.limitations || 'No limitations data extracted.';

        // Keywords tag cards
        if (paper.keywords && paper.keywords.length > 0) {
            paperKeywords.innerHTML = paper.keywords.map(k => `<span class="keyword-tag">${escapeHTML(k)}</span>`).join('');
        } else {
            paperKeywords.innerHTML = `<span class="keyword-tag">None</span>`;
        }

        // References List
        if (paper.references && paper.references.length > 0) {
            paperReferences.innerHTML = paper.references.map(ref => {
                const scholarUrl = `https://scholar.google.com/scholar?q=${encodeURIComponent(ref)}`;
                return `
                    <li>
                        <span>${escapeHTML(ref)}</span>
                        <a href="${scholarUrl}" target="_blank" class="reference-link" title="Look up on Google Scholar">
                            <i data-lucide="external-link" style="width: 12.5px; height: 12.5px; display: inline-block; vertical-align: middle;"></i> Scholar
                        </a>
                    </li>
                `;
            }).join('');
        } else {
            paperReferences.innerHTML = `<li style="list-style: none; margin-left: -20px; color: var(--ink-soft); font-style: italic;">No bibliography references extracted.</li>`;
        }

        lucide.createIcons();

        // Reset Q&A companion list
        chatLog.innerHTML = `
            <div class="qa-block" style="background: transparent; border: none; padding: 0 0 10px 0; border-bottom: 1px solid var(--navy-line);">
                <div class="qa-answer" style="color: var(--text-secondary); font-style: italic; font-size: 13.5px; margin: 0;">
                    Reading companion initialized. Ask any grounding questions to query the text.
                </div>
            </div>
        `;
    }

    // 7. Delete Paper from Catalog
    function deletePaper(id) {
        deleteTargetId = id;
        deleteModal.style.display = 'flex';
        // force reflow
        deleteModal.offsetHeight;
        deleteModal.classList.add('show');
    }

    async function performDelete(id) {
        // Clear polling
        if (pollingIntervals[id]) {
            clearInterval(pollingIntervals[id]);
            delete pollingIntervals[id];
        }

        try {
            const res = await fetch(`/api/papers/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('Failed to delete paper');

            showToast('Paper deleted from catalog.', 'success');
            
            // Reset workspace if active paper was deleted
            if (activePaper && activePaper.id === id) {
                activePaper = null;
                activeWorkspace.style.display = 'none';
                noSelectionState.style.display = 'block';
                noSelectionState.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-eyebrow">Marginal Library</div>
                        <h1>No Paper Selected</h1>
                        <p class="empty-sub">Select an article from your sidebar library, or upload a new PDF to generate a structured academic breakdown and ask grounding questions.</p>
                    </div>
                `;
            }

            fetchPapers();
        } catch (error) {
            console.error('Delete error:', error);
            showToast(error.message, 'error');
        }
    }

    // 8. Copy citation
    copyCitationBtn.addEventListener('click', () => {
        if (!activePaper) return;
        const style = citationStyle.value;
        const fullCitation = activePaper.full_citations ? activePaper.full_citations[style] : '';
        
        if (fullCitation) {
            navigator.clipboard.writeText(fullCitation)
                .then(() => showToast(`Citation copied to clipboard (${style.toUpperCase()})!`, 'success'))
                .catch(err => console.error('Failed to copy', err));
        } else {
            const fallback = `${activePaper.title || 'Untitled'}. (${activePaper.year || 'n.d.'}).`;
            navigator.clipboard.writeText(fallback)
                .then(() => showToast('Citation copied!', 'success'));
        }
    });

    // 9. Q&A Grounded Chat Interaction
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question || !activePaper) return;

        chatInput.value = '';

        // Create unified QA Block
        const qaId = 'qa-' + Date.now();
        const qaBlock = document.createElement('div');
        qaBlock.className = 'qa-block';
        qaBlock.id = qaId;
        qaBlock.innerHTML = `
            <div class="qa-question">Question: ${escapeHTML(question)}</div>
            <div class="qa-answer qa-loading">
                <i data-lucide="loader" class="animate-spin" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 8px; animation: spin 2s linear infinite;"></i>
                Querying index & drafting response...
            </div>
        `;
        
        chatLog.appendChild(qaBlock);
        lucide.createIcons();
        chatLog.scrollTop = chatLog.scrollHeight;

        try {
            const res = await fetch('/api/chat/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    paper_id: activePaper.id,
                    question: question,
                    style: citationStyle.value
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to answer');
            }

            const data = await res.json();
            
            // Format markers in response
            let answerHtml = escapeHTML(data.answer).replace(/\[(\d+)\]/g, (match, marker) => {
                return `<span class="citation-marker" data-marker="${marker}">${match}</span>`;
            });

            // Generate footnotes
            let footnoteHtml = '';
            if (data.citations && data.citations.length > 0) {
                footnoteHtml = `
                    <div class="qa-footnote">
                        <span class="pages">Footnotes & Context Quotes:</span>
                        ${data.citations.map(c => `
                            <div class="qa-footnote-item" data-marker="${c.marker}">
                                <span style="color: var(--brass-bright); font-weight: 700;">[${c.marker}]</span>
                                <span class="citation-quote">"${escapeHTML(c.quote)}"</span>
                                <span>— ${escapeHTML(c.formatted)}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            // Update block content
            qaBlock.innerHTML = `
                <div class="qa-question">Question: ${escapeHTML(question)}</div>
                <div class="qa-answer">${answerHtml}</div>
                ${footnoteHtml}
            `;

            // Scrolling adjustments
            chatLog.scrollTop = chatLog.scrollHeight;

            // Highlight citation link interactions
            const markers = qaBlock.querySelectorAll('.citation-marker');
            const items = qaBlock.querySelectorAll('.qa-footnote-item');

            markers.forEach(m => {
                m.addEventListener('click', () => {
                    const markerId = m.getAttribute('data-marker');
                    const targetItem = qaBlock.querySelector(`.qa-footnote-item[data-marker="${markerId}"]`);
                    if (targetItem) {
                        items.forEach(i => i.classList.remove('highlighted'));
                        targetItem.classList.add('highlighted');
                        targetItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            });

            items.forEach(item => {
                item.addEventListener('click', () => {
                    items.forEach(i => i.classList.remove('highlighted'));
                    item.classList.add('highlighted');
                });
            });

        } catch (error) {
            console.error('Chat error:', error);
            qaBlock.innerHTML = `
                <div class="qa-question">Question: ${escapeHTML(question)}</div>
                <div class="qa-answer qa-error">Error: ${escapeHTML(error.message)}</div>
            `;
        }
    });

    // Alert toast notification
    function showToast(message, type = 'info') {
        toast.textContent = message;
        toast.className = 'toast show';
        
        if (type === 'error') {
            toast.style.borderLeft = '4px solid var(--danger)';
        } else if (type === 'success') {
            toast.style.borderLeft = '4px solid var(--success)';
        } else {
            toast.style.borderLeft = '4px solid var(--brass-bright)';
        }

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    function escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // 10. About Modal Interactions
    const aboutBtn = document.getElementById('aboutBtn');
    const aboutModal = document.getElementById('aboutModal');
    const closeAboutBtn = document.getElementById('closeAboutBtn');

    if (aboutBtn && aboutModal && closeAboutBtn) {
        aboutBtn.addEventListener('click', () => {
            aboutModal.style.display = 'flex';
            aboutModal.offsetHeight; // force reflow
            aboutModal.classList.add('show');
        });

        closeAboutBtn.addEventListener('click', () => {
            aboutModal.classList.remove('show');
            setTimeout(() => { aboutModal.style.display = 'none'; }, 200);
        });

        aboutModal.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                aboutModal.classList.remove('show');
                setTimeout(() => { aboutModal.style.display = 'none'; }, 200);
            }
        });
    }
});
