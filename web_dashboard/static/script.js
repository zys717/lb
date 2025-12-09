const API_BASE = '/api';
const DEMO_SCENARIO_ID = 'S022';

// State
let scenarioData = null;
let reportData = null;

// DOM Elements
const tcListEl = document.getElementById('tcList');
const missionPanelEl = document.getElementById('missionPanel');
const reasoningPanelEl = document.getElementById('reasoningPanel');
const decisionPanelEl = document.getElementById('decisionPanel');
const headerTitleEl = document.getElementById('headerTitle');

// Init
document.addEventListener('DOMContentLoaded', async () => {
    await loadDemoData();
});

async function loadDemoData() {
    try {
        // Fetch S022 specifically
        const [sRes, rRes] = await Promise.all([
            fetch(`${API_BASE}/scenario/${DEMO_SCENARIO_ID}`),
            fetch(`${API_BASE}/report/${DEMO_SCENARIO_ID}`)
        ]);
        
        if (!sRes.ok || !rRes.ok) throw new Error("Failed to load demo data");
        
        scenarioData = await sRes.json();
        reportData = await rRes.json();
        
        try {
            renderSidebar();
        } catch (e) {
            console.error("Sidebar render failed", e);
        }
        
        // Auto-select first TC
        if (scenarioData.test_cases && scenarioData.test_cases.length > 0) {
            try {
                selectTestCase(scenarioData.test_cases[0].id);
            } catch (e) {
                console.error("Auto-select failed", e);
            }
        }
        
    } catch (err) {
        console.error(err);
        tcListEl.innerHTML = '<div class="error">Failed to load demo scenario S022. Ensure backend is running.</div>';
    }
}

function renderSidebar() {
    tcListEl.innerHTML = '';
    
    scenarioData.test_cases.forEach(tc => {
        const item = document.createElement('div');
        item.className = 'tc-item';
        item.dataset.id = tc.id;
        
        // Clean up ID for display (e.g., "TC1_EmergencyVsNoise" -> "TC1")
        const shortId = tc.id.split('_')[0];
        const title = tc.description || tc.name;
        
        item.innerHTML = `
            <div class="tc-item-header">
                <span class="tc-id-badge">${shortId}</span>
                <span class="tc-title">${title}</span>
            </div>
        `;
        
        item.onclick = () => selectTestCase(tc.id);
        tcListEl.appendChild(item);
    });
}

function selectTestCase(tcId) {
    // Highlight
    document.querySelectorAll('.tc-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.querySelector(`.tc-item[data-id="${tcId}"]`);
    if (activeItem) activeItem.classList.add('active');
    
    // Find Data
    // Note: scenarioData uses 'id' or 'case_id'
    const tcDef = scenarioData.test_cases.find(t => t.id === tcId || t.case_id === tcId);
    const tcResult = reportData.results.find(r => r.test_case_id === tcId);
    
    if (!tcDef) return;

    // Update Header
    headerTitleEl.innerText = tcDef.description || tcDef.name;
    
    // Render Panels
    renderMission(tcDef);
    renderReasoning(tcResult);
    renderDecision(tcResult, tcDef);
}

function renderMission(tc) {
    const m = tc.mission_details || {};
    
    // Icons mapping
    const typeIcons = {
        'emergency_medical': '<i class="fa-solid fa-truck-medical"></i>',
        'law_enforcement': '<i class="fa-solid fa-user-shield"></i>',
        'commercial_public_service': '<i class="fa-solid fa-box-open"></i>',
        'media_coverage': '<i class="fa-solid fa-camera"></i>'
    };
    
    const icon = typeIcons[m.mission_type] || '<i class="fa-solid fa-paper-plane"></i>';
    const urgencyClass = (m.urgency_level === 'CRITICAL') ? 'urgency-critical' : 
                         (m.urgency_level === 'HIGH') ? 'urgency-high' : 'urgency-normal';

    let html = `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon">${icon}</div>
                <div class="mission-type">
                    <div class="label">MISSION TYPE</div>
                    <div class="value">${(m.mission_type || 'General').replace(/_/g, ' ').toUpperCase()}</div>
                </div>
                <div class="mission-urgency ${urgencyClass}">
                    ${m.urgency_level || 'NORMAL'}
                </div>
            </div>
            
            <div class="mission-grid">
                <div class="m-item">
                    <i class="fa-regular fa-clock"></i>
                    <span>${m.time || 'N/A'}</span>
                </div>
                <div class="m-item">
                    <i class="fa-solid fa-location-dot"></i>
                    <span>${m.location_type || 'Unknown Location'}</span>
                </div>
                <div class="m-item full-width">
                    <i class="fa-solid fa-box"></i>
                    <span>Payload: ${m.payload || 'None'}</span>
                </div>
                ${m.patient_condition ? `
                <div class="m-item full-width highlight-red">
                    <i class="fa-solid fa-heart-pulse"></i>
                    <span>${m.patient_condition}</span>
                </div>` : ''}
            </div>
        </div>
    `;

    // Conflicts Visualization
    if (tc.rule_conflicts && tc.rule_conflicts.length > 0) {
        html += `<div class="conflict-section">
            <h5><i class="fa-solid fa-triangle-exclamation"></i> DETECTED CONFLICTS</h5>`;
            
        tc.rule_conflicts.forEach(c => {
            // Handle different structures of conflict objects
            const ruleA = c.rule_a || (c.rules ? c.rules[0] : '?');
            const ruleB = c.rule_b || (c.rules ? c.rules[c.rules.length-1] : '?');
            
            html += `
                <div class="conflict-card">
                    <div class="conflict-header">
                        <span class="rule-tag">${ruleA}</span>
                        <span class="vs">VS</span>
                        <span class="rule-tag">${ruleB}</span>
                    </div>
                    <div class="conflict-desc">${c.conflict_nature}</div>
                </div>
            `;
        });
        html += `</div>`;
    }
    
    // Triggered Rules
    if (tc.triggered_rules) {
        html += `<div class="rules-section">
            <h5>TRIGGERED RULES</h5>
            <div class="tags">`;
        const rules = Array.isArray(tc.triggered_rules) ? tc.triggered_rules : [tc.triggered_rules];
        rules.forEach(r => {
            html += `<span class="tag">${r}</span>`;
        });
        html += `</div></div>`;
    }

    missionPanelEl.innerHTML = html;
}

function renderReasoning(result) {
    if (!result) {
        reasoningPanelEl.innerHTML = '<div class="placeholder-text">No reasoning available.</div>';
        return;
    }

    let steps = [];
    
    // 1. Try to get structured steps from various locations
    // Priority: llm_parsed.reasoning_steps (RAG format) > llm_parsed.analysis.reasoning_steps > llm_result.analysis.reasoning_steps (Validation format)
    let rawSteps = null;
    
    if (result.llm_parsed) {
        if (Array.isArray(result.llm_parsed.reasoning_steps)) {
            rawSteps = result.llm_parsed.reasoning_steps;
        } else if (result.llm_parsed.analysis && Array.isArray(result.llm_parsed.analysis.reasoning_steps)) {
            rawSteps = result.llm_parsed.analysis.reasoning_steps;
        }
    }
    
    if (!rawSteps && result.llm_result && result.llm_result.analysis && Array.isArray(result.llm_result.analysis.reasoning_steps)) {
        rawSteps = result.llm_result.analysis.reasoning_steps;
    }

    if (rawSteps) {
        steps = rawSteps.map(s => {
            // Format: "Step 1: Content..."
            const match = s.match(/^(Step \d+):(.*)/);
            if (match) {
                return { label: match[1], content: match[2].trim() };
            }
            return { label: "Step", content: s };
        });
    }

    // 2. If no structured steps, try parsing the raw reasoning string
    if (steps.length === 0) {
        let reasoning = "";
        if (result.llm_parsed && typeof result.llm_parsed.reasoning === 'string') {
            reasoning = result.llm_parsed.reasoning;
        } else if (result.llm_result && typeof result.llm_result.reasoning === 'string') {
            reasoning = result.llm_result.reasoning;
        }
        
        if (reasoning) {
            const parts = reasoning.split(/(Step \d+:)/g).filter(p => p.trim().length > 0);
            // If we successfully split into Step X + Content pairs
            if (parts.length >= 2 && parts[0].startsWith('Step')) {
                for (let i = 0; i < parts.length; i += 2) {
                    if (parts[i+1]) {
                        steps.push({
                            label: parts[i].replace(':', ''),
                            content: parts[i+1].trim()
                        });
                    }
                }
            } else {
                // Fallback: treat whole string as one block
                steps.push({ label: "Analysis", content: reasoning });
            }
        }
    }

    if (steps.length === 0) {
        reasoningPanelEl.innerHTML = '<div class="placeholder-text">No reasoning steps found.</div>';
        return;
    }
    
    let html = '<div class="timeline">';
    steps.forEach(step => {
        html += `
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <div class="step-title">${step.label}</div>
                    <div class="step-text">${step.content}</div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    reasoningPanelEl.innerHTML = html;
}

function renderDecision(result, tcDef) {
    if (!result) {
        decisionPanelEl.innerHTML = 'No result';
        return;
    }

    let llmDecision = "UNKNOWN";
    if (result.llm_parsed && result.llm_parsed.decision) llmDecision = String(result.llm_parsed.decision);
    else if (result.llm_result && result.llm_result.decision) llmDecision = String(result.llm_result.decision);

    // Ground Truth
    let gtDecision = "UNKNOWN";
    let gtReason = "";
    
    // Prefer GT from Report (it's paired)
    if (result.ground_truth && result.ground_truth.decision) {
        gtDecision = String(result.ground_truth.decision);
    } else if (tcDef.expected_decision) {
        gtDecision = String(tcDef.expected_decision);
        gtReason = tcDef.expected_reason;
    }

    const normLlm = llmDecision.toUpperCase().trim();
    const normGt = gtDecision.toUpperCase().trim();
    
    // Loose matching
    const isMatch = normLlm === normGt || 
                   (normLlm.includes(normGt) && normGt !== "UNKNOWN") ||
                   (normGt.includes(normLlm) && normLlm !== "UNKNOWN");

    const statusColor = isMatch ? '#2ecc71' : '#e74c3c';
    const statusIcon = isMatch ? '<i class="fa-solid fa-circle-check"></i>' : '<i class="fa-solid fa-circle-xmark"></i>';

    let html = `
        <div class="verdict-container">
            <div class="verdict-main ${normLlm.includes('APPROVE') || normLlm.includes('CHOOSE') ? 'approve' : 'reject'}">
                <div class="verdict-label">MODEL DECISION</div>
                <div class="verdict-value">${llmDecision}</div>
            </div>
            
            <div class="gt-comparison">
                <div class="gt-row">
                    <span class="gt-label">Ground Truth:</span>
                    <span class="gt-value">${gtDecision}</span>
                </div>
                <div class="match-badge" style="color:${statusColor}; border-color:${statusColor}">
                    ${statusIcon} ${isMatch ? 'CORRECT' : 'INCORRECT'}
                </div>
            </div>
        </div>
    `;

    if (gtReason || (tcDef && tcDef.expected_reason)) {
        const reason = gtReason || tcDef.expected_reason;
        html += `
            <div class="gt-reason-box">
                <div class="gt-reason-title"><i class="fa-solid fa-book"></i> Expected Reasoning</div>
                <div class="gt-reason-text">${reason}</div>
            </div>
        `;
    }

    decisionPanelEl.innerHTML = html;
}
