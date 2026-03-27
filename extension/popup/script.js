document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const goalInput = document.getElementById('goal');
    const setupView = document.getElementById('setup-view');
    const activeView = document.getElementById('active-view');
    const statusBadge = document.getElementById('status');
    const goalDisplay = document.getElementById('current-goal-display');

    const focusBtn = document.getElementById('focus-btn');
    const focusDisplay = document.getElementById('focus-tab-display');
    const resetBtn = document.getElementById('reset-btn');

    // Check for existing session
    chrome.storage.local.get(['sessionActive', 'goal', 'session_id', 'focusTabTitle'], (result) => {
        if (result.sessionActive) {
            showActiveView(result.goal, result.focusTabTitle);
        }
    });

    startBtn.addEventListener('click', async () => {
        const goal = goalInput.value.trim();
        if (!goal) return alert("Please enter a goal!");

        try {
            const response = await fetch('http://localhost:8000/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal })
            });

            const data = await response.json();
            if (response.ok && data.session_id) {
                chrome.storage.local.set({ 
                    sessionActive: true, 
                    goal: goal, 
                    session_id: data.session_id 
                });
                showActiveView(goal);
                // Notify background to reconnect with new session ID
                chrome.runtime.sendMessage({ type: "START_SESSION", session_id: data.session_id });
            }
        } catch (error) {
            alert("Could not connect to Brain. Is the server running?");
        }
    });

    focusBtn.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const tab = tabs[0];
            if (tab) {
                chrome.storage.local.set({ focusTabId: tab.id, focusTabTitle: tab.title });
                focusDisplay.textContent = tab.title;
                chrome.runtime.sendMessage({ type: "SET_FOCUS_TAB", tab_id: tab.id });
                focusBtn.textContent = "Focus Updated!";
                setTimeout(() => focusBtn.textContent = "Set Current as Focus Tab", 2000);
            }
        });
    });

    stopBtn.addEventListener('click', () => {
        chrome.storage.local.set({ sessionActive: false, goal: null, session_id: null, focusTabId: null, focusTabTitle: null });
        setupView.style.display = 'block';
        activeView.style.display = 'none';
        statusBadge.textContent = 'Ready';
        statusBadge.style.color = '#22c55e';
        chrome.runtime.sendMessage({ type: "STOP_SESSION" });
    });

    resetBtn.addEventListener('click', async () => {
        if (!confirm("Are you sure? This will clear all session history and logs on the server.")) return;

        try {
            const response = await fetch('http://localhost:8000/session/reset', {
                method: 'POST'
            });

            if (response.ok) {
                chrome.storage.local.set({ 
                    sessionActive: false, 
                    goal: null, 
                    session_id: null, 
                    focusTabId: null, 
                    focusTabTitle: null 
                });
                setupView.style.display = 'block';
                activeView.style.display = 'none';
                statusBadge.textContent = 'Ready';
                statusBadge.style.color = '#22c55e';
                chrome.runtime.sendMessage({ type: "STOP_SESSION" });
                alert("Server reset successfully. Fresh session ready.");
            }
        } catch (error) {
            alert("Could not connect to Brain for reset.");
        }
    });

    function showActiveView(goal, focusTitle) {
        setupView.style.display = 'none';
        activeView.style.display = 'block';
        goalDisplay.textContent = goal;
        focusDisplay.textContent = focusTitle || "Not Set";
        statusBadge.textContent = 'Active';
        statusBadge.style.color = '#a855f7';
    }
});
