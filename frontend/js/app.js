document.addEventListener('DOMContentLoaded', () => {
    // DOM Element References
    const urlInput = document.getElementById('url-input');
    const clearBtn = document.getElementById('clear-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const analyzeSpinner = document.getElementById('analyze-spinner');
    const btnText = analyzeBtn.querySelector('.btn-text');
    
    const loadingCard = document.getElementById('loading-card');
    const errorCard = document.getElementById('error-card');
    const errorTitle = document.getElementById('error-title');
    const errorMessage = document.getElementById('error-message');
    const errorDetails = document.getElementById('error-details');

    const resultsCard = document.getElementById('results-card');
    const mediaTitle = document.getElementById('media-title');
    const domainBadge = document.getElementById('domain-badge');
    const strategyBadge = document.getElementById('strategy-badge');
    const durationBadge = document.getElementById('duration-badge');
    const formatCount = document.getElementById('format-count');

    const thumbPlaceholder = document.getElementById('thumb-placeholder');
    const mediaThumb = document.getElementById('media-thumb');

    const previewBtn = document.getElementById('preview-btn');
    const playerDrawer = document.getElementById('player-drawer');
    const closePlayerBtn = document.getElementById('close-player-btn');
    const previewVideo = document.getElementById('preview-video');

    const filterTabs = document.getElementById('filter-tabs');
    const formatsGrid = document.getElementById('formats-grid');

    const cntAll = document.getElementById('cnt-all');
    const cntVa = document.getElementById('cnt-va');
    const cntVo = document.getElementById('cnt-vo');
    const cntAo = document.getElementById('cnt-ao');
    const cntManifest = document.getElementById('cnt-manifest');

    let currentFormats = [];
    let currentActiveFilter = 'all';

    // Input Handlers
    urlInput.addEventListener('input', () => {
        clearBtn.style.display = urlInput.value.length > 0 ? 'block' : 'none';
    });

    clearBtn.addEventListener('click', () => {
        urlInput.value = '';
        clearBtn.style.display = 'none';
        urlInput.focus();
    });

    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeURL();
        }
    });

    analyzeBtn.addEventListener('click', analyzeURL);

    async function analyzeURL() {
        const url = urlInput.value.trim();
        if (!url) return;

        // Reset UI State
        hideError();
        resultsCard.style.display = 'none';
        playerDrawer.style.display = 'none';
        previewVideo.pause();
        loadingCard.style.display = 'block';

        analyzeBtn.disabled = true;
        btnText.textContent = 'Extracting...';
        analyzeSpinner.style.display = 'block';

        try {
            const data = await window.VidLinkAPI.analyzeURL(url);
            renderResults(data);
        } catch (err) {
            showError("Extraction Failed", err.message);
        } finally {
            loadingCard.style.display = 'none';
            analyzeBtn.disabled = false;
            btnText.textContent = 'Analyze Media';
            analyzeSpinner.style.display = 'none';
        }
    }

    function renderResults(data) {
        if (!data.success) {
            showError("No Public Media Discovered", data.error || "Extraction failed.");
            return;
        }

        currentFormats = data.formats || [];

        // Meta Rendering
        mediaTitle.textContent = data.title || "Extracted Media Resource";
        domainBadge.textContent = data.source_domain || "Web Resource";
        strategyBadge.textContent = data.extractor_used || "Multi-Layer Engine";
        formatCount.textContent = currentFormats.length;

        if (data.duration) {
            durationBadge.textContent = formatDuration(data.duration);
            durationBadge.style.display = 'inline-block';
        } else {
            durationBadge.style.display = 'none';
        }

        // Thumbnail Handling
        if (data.thumbnail) {
            mediaThumb.src = data.thumbnail;
            mediaThumb.style.display = 'block';
            thumbPlaceholder.style.display = 'none';
        } else {
            mediaThumb.style.display = 'none';
            thumbPlaceholder.style.display = 'flex';
        }

        // Preview Player Setup (if playable video direct format exists)
        const playableFormat = currentFormats.find(f => f.has_video && f.download_type === 'direct');
        if (playableFormat) {
            previewBtn.style.display = 'flex';
            previewBtn.onclick = () => {
                previewVideo.src = playableFormat.url;
                playerDrawer.style.display = 'block';
                previewVideo.play();
            };
        } else {
            previewBtn.style.display = 'none';
        }

        // Calculate Tab Counts
        cntAll.textContent = currentFormats.length;
        cntVa.textContent = currentFormats.filter(f => f.stream_type === 'video_audio').length;
        cntVo.textContent = currentFormats.filter(f => f.stream_type === 'video_only').length;
        cntAo.textContent = currentFormats.filter(f => f.stream_type === 'audio_only').length;
        cntManifest.textContent = currentFormats.filter(f => ['hls', 'dash'].includes(f.download_type)).length;

        // Render Format Cards
        renderFormatGrid();
        resultsCard.style.display = 'block';
    }

    // Filter Buttons Listener
    filterTabs.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;

        filterTabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        currentActiveFilter = btn.dataset.filter;
        renderFormatGrid();
    });

    function renderFormatGrid() {
        formatsGrid.innerHTML = '';

        const filtered = currentFormats.filter(fmt => {
            if (currentActiveFilter === 'all') return true;
            if (currentActiveFilter === 'manifest') return ['hls', 'dash'].includes(fmt.download_type);
            return fmt.stream_type === currentActiveFilter;
        });

        if (filtered.length === 0) {
            formatsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">
                    No formats discovered for selected filter.
                </div>
            `;
            return;
        }

        filtered.forEach((fmt) => {
            const card = document.createElement('div');
            card.className = 'format-card';

            const downloadQuery = new URLSearchParams({
                url: fmt.url,
                filename: `${mediaTitle.textContent.replace(/[^a-zA-Z0-9_\-]/g, '_')}_${fmt.quality}.${fmt.ext}`,
                download_type: fmt.download_type,
                headers: JSON.stringify(fmt.http_headers || {})
            }).toString();

            card.innerHTML = `
                <div class="format-top">
                    <div class="format-quality">
                        <span>${fmt.quality || fmt.resolution}</span>
                        <span class="ext-tag">${fmt.ext}</span>
                    </div>
                    <span class="badge badge-stream badge-${fmt.stream_type === 'video_audio' ? 'va' : (fmt.stream_type === 'video_only' ? 'vo' : 'ao')}">
                        ${fmt.badge}
                    </span>
                </div>
                <div class="format-details">
                    <div class="detail-item">
                        <span class="detail-label">Resolution</span>
                        <span>${fmt.resolution}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Est. Size</span>
                        <span>${fmt.filesize_formatted}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Video Codec</span>
                        <span>${fmt.vcodec}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Audio Codec</span>
                        <span>${fmt.acodec}</span>
                    </div>
                </div>
                <a href="/api/download?${downloadQuery}" class="download-link" target="_blank" download>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Download Format
                </a>
            `;
            formatsGrid.appendChild(card);
        });
    }

    closePlayerBtn.addEventListener('click', () => {
        playerDrawer.style.display = 'none';
        previewVideo.pause();
    });

    function showError(title, msg) {
        errorTitle.textContent = title;
        errorMessage.textContent = msg;
        errorCard.style.display = 'block';
    }

    function hideError() {
        errorCard.style.display = 'none';
    }

    function formatDuration(seconds) {
        if (!seconds) return '';
        const sec = Math.floor(seconds % 60);
        const min = Math.floor((seconds / 60) % 60);
        const hrs = Math.floor(seconds / 3600);
        const pad = (n) => n.toString().padStart(2, '0');
        return hrs > 0 ? `${hrs}:${pad(min)}:${pad(sec)}` : `${min}:${pad(sec)}`;
    }
});
