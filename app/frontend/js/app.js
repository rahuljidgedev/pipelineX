/* ========================================
   AI Software Factory — Frontend App
   ======================================== */

// --- State ---
const app = {
    threadId: null,
    projectName: '',
    prdEditing: false,
    pollInterval: null,
    lastActiveNode: null,
    lastLogCount: 0,
    logsMinimized: false
};

const STEP_ORDER = [
    'init', 'ideation_node', 'pm', 'prd_approval', 'dev', 'qa', 'ast_node', 'auditor_node', 'review_node', 'build_approval', 'compliance_node', 'packaging_node', 'deployment_node', 'done'
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

    // A small delay function for the ripple effect when falling
    const delay = ms => new Promise(res => setTimeout(res, ms));

    STEP_ORDER.forEach((step, i) => {
        const el = document.querySelector(`.step-item[data-step="${step}"]`);
        if (!el) return;

        el.classList.remove('completed', 'active');
        if (i < activeIdx) {
            el.classList.add('completed');
        } else if (i === activeIdx) {
            el.classList.add('active');
        }
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
    const logs = state.logs || [];

    // Handle new logs
    if (logs.length > app.lastLogCount) {
        for (let i = app.lastLogCount; i < logs.length; i++) {
            addLogLine(logs[i]);
        }
        app.lastLogCount = logs.length;
    }

    if (status.error) {
        stopPolling();
        document.getElementById('cancel-reason').textContent = 'Backend Crash: ' + status.error.split('\n')[0];
        showScreen('cancelled');
        addLogLine("❌ Pipeline crashed: " + status.error.split('\n')[0]);
        return;
    }

    // Check for agent-level errors (e.g., LLM API failures)
    if (state.error && !isRunning) {
        stopPolling();
        addLogLine("❌ " + state.error);
        document.getElementById('error-message').textContent = state.error;
        showScreen('error');
        return;
    }

    if (status.is_completed) {
        stopPolling();
        updateStepper('done');
        
        // If the user rejected/cancelled, show the cancelled screen instead of complete
        if (state.last_approval === false) {
            document.getElementById('cancel-reason').textContent = 'Pipeline exited at your request.';
            showScreen('cancelled');
            addLogLine("🚫 Pipeline ended by user.");
            return;
        }

        // Update download link with project name
        const downloadBtn = document.getElementById('btn-download');
        if (downloadBtn) {
            downloadBtn.href = `/download-app?name=${encodeURIComponent(app.projectName)}`;
        }
        
        addLogLine("🎉 Pipeline completed successfully!");
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
        // When running, snapshot.next contains the node currently executing.
        // Fall back to active_node if next is empty.
        let node = (next && next.length > 0) ? next[0] : (status.active_node || 'init');
        let activeNode = 'init';

        if (node.includes('pm')) activeNode = 'pm';
        else if (node.includes('ideation')) activeNode = 'ideation_node';
        else if (node.includes('dev')) activeNode = 'dev';
        else if (node.includes('ast')) activeNode = 'ast_node';
        else if (node.includes('audit')) activeNode = 'auditor_node';
        else if (node.includes('qa')) activeNode = 'qa';
        else if (node.includes('review')) activeNode = 'review_node';
        else if (node.includes('compliance')) activeNode = 'compliance_node';
        else if (node.includes('packaging')) activeNode = 'packaging_node';
        else if (node.includes('deployment') || node.includes('marketing')) activeNode = 'deployment_node';
        else if (node.includes('approval')) {
            activeNode = state.review_result ? 'build_approval' : 'prd_approval';
        }
        
        // Fallback logic based on state data
        if (activeNode === 'init') {
            if (state.packaging_result) activeNode = 'deployment_node';
            else if (state.compliance_result) activeNode = 'packaging_node';
            else if (state.review_result) activeNode = 'build_approval'; 
            else if (state.auditor_result) activeNode = 'review_node'; 
            else if (state.ast_result) activeNode = 'auditor_node'; 
            else if (state.test_result === 'pass') activeNode = 'ast_node'; 
            else if (state.test_result === 'fail') activeNode = 'dev'; 
            else if (state.code) activeNode = 'qa'; 
            else if (state.prd) activeNode = 'dev'; 
            else if (state.is_feasible) activeNode = 'pm'; 
            else if (state.idea) activeNode = 'ideation_node'; 
        }
        
        updateStepper(activeNode);
        
        // Show loading screen with context
        const labels = {
            'ideation_node': ['Evaluating Idea...', 'The Quality Gate is checking feasibility'],
            'pm': ['Writing PRD...', 'The PM agent is defining requirements'],
            'dev': ['Coding...', 'The Dev agent is building your web app'],
            'qa': ['Testing...', 'The QA agent is validating the build'],
            'ast_node': ['Static Analysis...', 'The AST checker is analyzing code structure'],
            'auditor_node': ['Auditing...', 'The Auditor agent is checking semantic compliance'],
            'review_node': ['Reviewing...', 'A senior engineer is checking code quality'],
            'compliance_node': ['Compliance...', 'Generating legal and Play Store metadata'],
            'packaging_node': ['Packaging...', 'Zipping source code and app bundles'],
            'deployment_node': ['Launching...', 'Deploying to Play Store & executing Marketing Campaign']
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

    const btnApprove = document.getElementById('btn-build-approve');
    const btnReject = document.getElementById('btn-build-reject');

    if (qaResult === 'fail') {
        btnApprove.innerHTML = '🔄 Restart Process';
        btnApprove.onclick = () => resetApp();
        btnApprove.className = 'btn btn-primary';

        btnReject.innerHTML = '✕ Exit / Give Up';
        btnReject.onclick = () => rejectBuild();
    } else {
        btnApprove.innerHTML = '✓ Approve Build';
        btnApprove.onclick = () => approveBuild();
        btnApprove.className = 'btn btn-success';

        btnReject.innerHTML = '✕ Reject';
        btnReject.onclick = () => rejectBuild();
    }

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
    app.lastLogCount = 0;
    
    document.getElementById('input-name').value = '';
    document.getElementById('input-idea').value = '';
    document.getElementById('header-meta').textContent = '';
    
    // Clear all step logs
    document.querySelectorAll('.step-logs').forEach(el => el.innerHTML = '');
    
    showStepper(false);
    showScreen('start');
}

// --- Log Helpers ---

function addLogLine(text) {
    let containerId = 'logs-init';
    if (app.lastActiveNode) {
        containerId = 'logs-' + app.lastActiveNode;
    }
    const container = document.getElementById(containerId);
    if (!container) return;

    const line = document.createElement('div');
    line.className = 'log-line';
    
    if (text.includes('✅') || text.includes('successfully')) line.style.color = '#34d399';
    else if (text.includes('❌') || text.includes('failed') || text.includes('error')) line.style.color = '#f87171';
    else if (text.includes('Started')) line.style.color = '#60a5fa';

    line.textContent = text;
    container.appendChild(line);
    
    container.scrollTop = container.scrollHeight;
}

function toggleLogs() {
    // Legacy global log toggle is removed
}
