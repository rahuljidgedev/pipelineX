/* ========================================
   AI Software Factory — Frontend App
   ======================================== */

// --- State ---
const app = {
    threadId: null,
    projectName: '',
    prdEditing: false,
    pollInterval: null,
    lastActiveNode: null
};

// --- Pipeline step order (for stepper) ---
const STEP_ORDER = [
    'init', 'pm', 'prd_approval', 'dev', 'qa', 'review_node', 'build_approval', 'done'
];

// =====================
// Screen Management
// =====================

function showScreen(id) {
    // If we are already on this screen, don't flicker
    const screen = document.getElementById('screen-' + id);
    if (screen && screen.classList.contains('active')) return;

    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    if (screen) {
        screen.classList.add('active');
        const card = screen.querySelector('.card');
        if (card) {
            card.classList.remove('fade-in');
            void card.offsetWidth;
            card.classList.add('fade-in');
        }
    }
}

function showStepper(show) {
    document.getElementById('stepper-container').style.display = show ? '' : 'none';
}

// =====================
// Pipeline Stepper
// =====================

function updateStepper(activeStep) {
    if (app.lastActiveNode === activeStep) return;
    app.lastActiveNode = activeStep;

    const activeIdx = STEP_ORDER.indexOf(activeStep);
    if (activeIdx === -1) return;

    STEP_ORDER.forEach((step, i) => {
        const el = document.querySelector(`.step[data-step="${step}"]`);
        if (!el) return;

        el.classList.remove('completed', 'active');
        if (i < activeIdx) {
            el.classList.add('completed');
        } else if (i === activeIdx) {
            el.classList.add('active');
        }
    });

    // Update connecting lines
    document.querySelectorAll('.step-line').forEach(line => {
        const afterStep = line.dataset.after;
        const afterIdx = STEP_ORDER.indexOf(afterStep);
        line.classList.toggle('completed', afterIdx < activeIdx);
    });
}

// =====================
// API Calls
// =====================

async function apiPost(url) {
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

async function apiPatch(url, body) {
    const res = await fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

// =====================
// Polling Logic
// =====================

function startPolling() {
    if (app.pollInterval) clearInterval(app.pollInterval);
    app.pollInterval = setInterval(async () => {
        try {
            const status = await apiGet(`/status/${app.threadId}`);
            handleStatusUpdate(status);
            
            // Stop polling if completed or waiting for human
            if (status.is_completed || (status.next && status.next.length > 0 && !status.is_running)) {
                // Keep polling a bit longer to be sure, or stop
                if (!status.is_running) {
                    console.log("Stopping poll: waiting for human or done.");
                }
            }
        } catch (err) {
            console.error("Polling error:", err);
        }
    }, 2000);
}

function stopPolling() {
    if (app.pollInterval) {
        clearInterval(app.pollInterval);
        app.pollInterval = null;
    }
}

// =====================
// Flow Actions
// =====================

async function startPipeline() {
    const name = document.getElementById('input-name').value.trim();
    const idea = document.getElementById('input-idea').value.trim();

    if (!idea) {
        alert('Please describe your app idea.');
        return;
    }

    app.projectName = name || 'Untitled Project';
    document.getElementById('header-meta').textContent = app.projectName;

    showStepper(true);
    showLoading('Starting Pipeline...', 'Initializing agents');

    try {
        const data = await apiPost(`/start?idea=${encodeURIComponent(idea)}`);
        app.threadId = data.thread_id;
        startPolling();
    } catch (err) {
        showError(err.message);
    }
}

function handleStatusUpdate(status) {
    const next = status.next || [];
    const state = status.state || {};
    const isRunning = status.is_running;

    if (status.is_completed) {
        stopPolling();
        updateStepper('done');
        
        // Update download link with project name
        const downloadBtn = document.getElementById('btn-download');
        if (downloadBtn) {
            downloadBtn.href = `/download-app?name=${encodeURIComponent(app.projectName)}`;
        }
        
        showScreen('complete');
        return;
    }

    // 1. If waiting for PRD Approval
    if (next.includes('prd_approval') && !isRunning) {
        updateStepper('prd_approval');
        showPrdReview(state.prd || 'No PRD generated.');
        return;
    }

    // 2. If waiting for Build Approval
    if (next.includes('build_approval') && !isRunning) {
        updateStepper('build_approval');
        showBuildApproval(state);
        return;
    }

    // 3. If running, figure out which node is active for the stepper
    if (isRunning) {
        let activeNode = 'init';
        if (state.review_result) activeNode = 'build_approval'; // Almost done
        else if (state.test_result) activeNode = 'review_node'; // QA done, reviewing
        else if (state.code) activeNode = 'qa'; // Code done, testing
        else if (state.prd) activeNode = 'dev'; // PRD done, coding
        else if (state.idea) activeNode = 'pm'; // Idea present, writing PRD
        
        updateStepper(activeNode);
        
        // Show loading screen with context
        const labels = {
            'pm': ['Writing PRD...', 'The PM agent is defining requirements'],
            'dev': ['Coding...', 'The Dev agent is building your web app'],
            'qa': ['Testing...', 'The QA agent is validating the build'],
            'review_node': ['Reviewing...', 'A senior engineer is checking code quality']
        };
        const [title, sub] = labels[activeNode] || ['Processing...', 'The pipeline is running'];
        showLoading(title, sub);
    }
}

// --- PRD Review ---

function showPrdReview(prd) {
    document.getElementById('prd-viewer').innerHTML = marked.parse(prd);
    document.getElementById('prd-editor').value = prd;
    showScreen('prd');
}

function togglePrdEdit() {
    const viewer = document.getElementById('prd-viewer');
    const editor = document.getElementById('prd-editor');
    const btn = document.getElementById('btn-prd-toggle');

    if (app.prdEditing) {
        // Switch to view mode — render MD
        viewer.innerHTML = marked.parse(editor.value);
        viewer.style.display = '';
        editor.style.display = 'none';
        btn.textContent = '✏️ Edit';
    } else {
        // Switch to edit mode — show raw MD
        viewer.style.display = 'none';
        editor.style.display = '';
        btn.textContent = '👁 Preview';
        editor.focus();
    }
    app.prdEditing = !app.prdEditing;
}

async function approvePrd() {
    const editor = document.getElementById('prd-editor');
    const viewer = document.getElementById('prd-viewer');
    const editedPrd = app.prdEditing ? editor.value : viewer.textContent;

    showLoading('Saving & Approving PRD...', 'Starting code generation');
    
    try {
        await apiPatch(`/prd/${app.threadId}`, { prd: editedPrd });
        await apiPost(`/approve/${app.threadId}?approved=true`);
        startPolling();
    } catch (err) {
        showError(err.message);
    }
}

async function rejectApproval() {
    try {
        await apiPost(`/approve/${app.threadId}?approved=false`);
        document.getElementById('cancel-reason').textContent = 'PRD was rejected. Pipeline cancelled.';
        showScreen('cancelled');
        stopPolling();
    } catch (err) {
        showError(err.message);
    }
}

// --- Build Approval ---

function showBuildApproval(state) {
    const qaResult = state.test_result || '—';
    const attempts = state.attempts || 0;
    const review = state.review_result || 'No review available';

    const qaEl = document.getElementById('qa-result');
    qaEl.textContent = qaResult === 'pass' ? '✅ PASS' : qaResult === 'fail' ? '❌ FAIL' : qaResult;
    qaEl.className = 'status-pill ' + (qaResult === 'pass' ? 'pass' : qaResult === 'fail' ? 'fail' : '');

    document.getElementById('build-attempts').textContent = `${attempts} / 3`;
    document.getElementById('review-content').textContent = review;

    showScreen('build');
}

async function approveBuild() {
    showLoading('Finalizing...', 'Wrapping up your project');
    try {
        await apiPost(`/approve/${app.threadId}?approved=true`);
        startPolling();
    } catch (err) {
        showError(err.message);
    }
}

async function rejectBuild() {
    showLoading('Processing...', 'Updating pipeline state');
    try {
        await apiPost(`/approve/${app.threadId}?approved=false`);
        startPolling();
    } catch (err) {
        showError(err.message);
    }
}

// --- Helpers ---

function showLoading(title, subtitle) {
    document.getElementById('loading-title').textContent = title;
    document.getElementById('loading-subtitle').textContent = subtitle;
    showScreen('loading');
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    showScreen('error');
    stopPolling();
}

function resetApp() {
    stopPolling();
    app.threadId = null;
    app.projectName = '';
    app.prdEditing = false;
    app.lastActiveNode = null;
    document.getElementById('input-name').value = '';
    document.getElementById('input-idea').value = '';
    document.getElementById('header-meta').textContent = '';
    showStepper(false);
    showScreen('start');
}
