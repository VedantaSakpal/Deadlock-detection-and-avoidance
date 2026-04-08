// script.js
let currentStep = -1;
let isPlaying = false;
let playInterval = null;
let currentWork = [];
let processRows = [];

document.addEventListener('DOMContentLoaded', () => {
    if (!simData) return;
    
    currentWork = [...simData.available];
    initTable();
    updateWorkDisplay();
    
    // Init graph
    if (typeof initGraph === 'function') {
        initGraph(simData);
    }
    renderBankerAdvice();
});

function initTable() {
    const tbody = document.getElementById('process-table-body');
    tbody.innerHTML = '';
    processRows = [];
    
    const needOrReq = simData.mode === 'banker' ? simData.result.need : simData.demand;

    for (let i = 0; i < simData.processes; i++) {
        const tr = document.createElement('tr');
        tr.id = `row-p${i}`;
        
        let html = `<td><strong>P${i}</strong></td>
                    <td id="alloc-p${i}">[${simData.allocation[i].join(', ')}]</td>`;
                    
        if (simData.mode === 'banker') {
            html += `<td>[${simData.demand[i].join(', ')}]</td>
                     <td id="need-p${i}">[${needOrReq[i].join(', ')}]</td>`;
        } else {
            html += `<td id="req-p${i}">[${needOrReq[i].join(', ')}]</td>`;
        }
        
        html += `<td id="status-p${i}"><span class="badge" style="color: var(--text-secondary);">Waiting</span></td>`;
        
        tr.innerHTML = html;
        tbody.appendChild(tr);
        processRows.push(tr);
    }
}

function updateWorkDisplay() {
    document.getElementById('work-array').innerText = `[${currentWork.join(', ')}]`;
}

function updateStepProgress() {
    const progress = document.getElementById('step-progress');
    if (!progress || !simData?.result?.steps) return;
    const total = simData.result.steps.length;
    const percent = total === 0 ? 0 : ((currentStep + 1) / total) * 100;
    progress.style.width = `${percent}%`;
}

function renderBankerAdvice() {
    const panel = document.getElementById('banker-advice-panel');
    const text = document.getElementById('banker-advice-text');
    if (!panel || !text || simData.mode !== 'banker') return;

    if (simData.result?.steps?.some(step => step.action === 'invalid')) {
        const invalidStep = simData.result.steps.find(step => step.action === 'invalid');
        panel.style.display = 'block';
        text.innerText = invalidStep.message + ' ' + (simData.result.suggestion || 'Fix the highlighted input and retry.');
        return;
    }

    if (!simData.result.isSafe) {
        panel.style.display = 'block';
        text.innerText = simData.result.suggestion || 'Banker\'s algorithm avoids unsafe allocations by refusing them. Increase available resources or reduce max demand.';
        return;
    }

    panel.style.display = 'block';
    text.innerText = simData.result.suggestion || 'Banker\'s algorithm can safely allocate this request and avoid deadlock by keeping the system in a safe state.';
}

function addLog(msg, type = 'info') {
    const panel = document.getElementById('log-panel');
    const div = document.createElement('div');
    div.className = `log-entry ${type}`;
    div.innerText = msg;
    panel.appendChild(div);
    panel.scrollTop = panel.scrollHeight;
}

function stepNext() {
    if (currentStep >= simData.result.steps.length - 1) {
        pauseSim();
        return;
    }
    
    currentStep++;
    updateStepProgress();
    document.getElementById('btn-prev').disabled = false;
    const step = simData.result.steps[currentStep];
    
    // Reset active row visual
    processRows.forEach(row => row.classList.remove('status-active'));
    
    let logType = 'info';
    
    if (step.process !== -1) {
        const row = document.getElementById(`row-p${step.process}`);
        const statusTd = document.getElementById(`status-p${step.process}`);
        row.classList.add('status-active');
        
        if (typeof highlightActiveProcess === 'function') {
            highlightActiveProcess(step.process, step.status);
        }
        
        if (step.action === 'check') {
            if (step.status === 'success') {
                logType = 'success';
                row.className = 'status-executed';
                statusTd.innerHTML = '<span style="color: var(--color-green); font-weight: bold;">Executed</span>';
                
                // Update work
                currentWork = step.new_work;
                updateWorkDisplay();
                
                // Update Graph (remove edges for this process)
                if (typeof removeProcessFromGraph === 'function') {
                    removeProcessFromGraph(step.process);
                }
                
            } else if (step.status === 'wait') {
                logType = 'warning';
                row.className = 'status-waiting';
                statusTd.innerHTML = '<span style="color: var(--color-yellow);">Waiting</span>';
            }
        }
    } else {
        // Final state
        if (step.action === 'safe') {
            logType = 'success';
            document.getElementById('export-panel').style.display = 'block';
            document.getElementById('final-result-text').innerText = step.message;
        } else if (step.action === 'deadlock' || step.action === 'unsafe') {
            logType = 'error';
            
            if (step.deadlocked) {
                step.deadlocked.forEach(p => {
                    const row = document.getElementById(`row-p${p}`);
                    row.className = 'status-deadlock';
                    document.getElementById(`status-p${p}`).innerHTML = '<span style="color: var(--color-red); font-weight: bold;">Deadlocked</span>';
                });
                
                // Update Graph to highlight deadlocked nodes
                if(typeof highlightDeadlock === 'function') {
                    highlightDeadlock(step.deadlocked);
                }
                
                // Show recovery panel
                document.getElementById('recovery-panel').style.display = 'block';
            }
        }
        
        document.getElementById('btn-next').disabled = true;
        pauseSim();
    }
    
    addLog(`Step ${currentStep + 1}: ${step.message}`, logType);
}

function stepPrev() {
    if (currentStep < 0) return;
    
    // The easiest way to reverse state accurately in a browser is to rebuild to currentStep - 1
    const targetStep = currentStep - 1;
    resetSimState(); // Clears everything back to start
    document.getElementById('log-panel').innerHTML = ''; // Specific clear for log
    
    for (let i = 0; i <= targetStep; i++) {
        // We will execute the logic of stepNext silently or very quickly
        // But to keep it simple, calling stepNext iteratively works.
        // Disable log panel temporary appending or just let it rebuild.
        stepNext();
    }
    
    if (targetStep < 0) {
        document.getElementById('btn-prev').disabled = true;
    }
}

function resetSimState() {
    currentStep = -1;
    currentWork = [...simData.available];
    initTable();
    updateWorkDisplay();
    updateStepProgress();
    
    // Hide panels
    document.getElementById('recovery-panel').style.display = 'none';
    document.getElementById('export-panel').style.display = 'none';
    
    document.getElementById('btn-next').disabled = false;
    document.getElementById('btn-prev').disabled = true;
    
    if (typeof initGraph === 'function') {
        initGraph(simData);
    }
}

function resetSim() {
    pauseSim();
    document.getElementById('log-panel').innerHTML = '';
    resetSimState();
    addLog("Simulation reset. Fresh start ready.", "info");

    if (simData.mode === 'banker' && simData.result?.safeSequence?.length) {
        addLog(`Tip: Banker\'s safe sequence is [${simData.result.safeSequence.map(p => 'P' + p).join(', ')}]. Play again to watch it execute.`, 'success');
    } else if (simData.mode === 'detection') {
        addLog('Tip: Watch the Resource Allocation Graph for circular waits and use recovery actions if deadlock appears.', 'warning');
    }
}

function togglePlay() {
    const btn = document.getElementById('btn-play');
    if (isPlaying) {
        pauseSim();
    } else {
        if (currentStep >= simData.result.steps.length - 1) {
            resetSim(); // loop back if at end
        }
        isPlaying = true;
        btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
        btn.classList.replace('btn-primary', 'btn-warning');
        
        const speed = document.getElementById('speed').max - document.getElementById('speed').value + 200; // Invert slider
        
        playInterval = setInterval(() => {
            if (currentStep >= simData.result.steps.length - 1) {
                pauseSim();
            } else {
                stepNext();
            }
        }, speed);
    }
}

function pauseSim() {
    isPlaying = false;
    clearInterval(playInterval);
    const btn = document.getElementById('btn-play');
    btn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
    btn.classList.replace('btn-warning', 'btn-primary');
}

document.getElementById('speed').addEventListener('change', () => {
    if (isPlaying) {
        pauseSim();
        togglePlay();
    }
});

async function recoverTerminate() {
    try {
        const response = await fetch('/recover/terminate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
        const result = await response.json();
        if(response.ok) {
            alert('Recovery successful: ' + result.message);
            window.location.reload();
        } else {
            alert('Recovery failed: ' + (result.error || result.message));
        }
    } catch (error) {
        alert('Error during recovery: ' + error.message);
    }
}

async function recoverPreempt() {
    try {
        const response = await fetch('/recover/preempt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
        const result = await response.json();
        if(response.ok) {
            alert('Recovery successful: ' + result.message);
            window.location.reload();
        } else {
            alert('Recovery failed: ' + (result.error || result.message));
        }
    } catch (error) {
        alert('Error during recovery: ' + error.message);
    }
}

function exportCSV() {
    window.location.href = '/export/csv';
}

function exportPDF() {
    window.location.href = '/export/pdf';
}

function toggleTheme() {
    const body = document.body;
    const btn = document.querySelector('.theme-toggle i');
    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        btn.className = 'fa-solid fa-sun';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        btn.className = 'fa-solid fa-moon';
        localStorage.setItem('theme', 'dark');
    }
}

function loadTheme() {
    const theme = localStorage.getItem('theme') || 'dark';
    const body = document.body;
    const btn = document.querySelector('.theme-toggle i');
    if (theme === 'light') {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        if (btn) btn.className = 'fa-solid fa-sun';
    }
}

// Load theme on page load
document.addEventListener('DOMContentLoaded', loadTheme);
