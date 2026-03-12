document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const goalInput = document.getElementById('goal');
    const setupView = document.getElementById('setup-view');
    const activeView = document.getElementById('active-view');
    const statusBadge = document.getElementById('status');
    const goalDisplay = document.getElementById('current-goal-display');

    // Check for existing session
    chrome.storage.local.get(['sessionActive', 'goal'], (result) => {
        if (result.sessionActive) {
            showActiveView(result.goal);
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

            if (response.ok) {
                chrome.storage.local.set({ sessionActive: true, goal: goal });
                showActiveView(goal);
            }
        } catch (error) {
            alert("Could not connect to Brain. Is the server running?");
        }
    });

    stopBtn.addEventListener('click', () => {
        chrome.storage.local.set({ sessionActive: false, goal: null });
        setupView.style.display = 'block';
        activeView.style.display = 'none';
        statusBadge.textContent = 'Ready';
        statusBadge.style.color = '#22c55e';
    });

    function showActiveView(goal) {
        setupView.style.display = 'none';
        activeView.style.display = 'block';
        goalDisplay.textContent = goal;
        statusBadge.textContent = 'Active';
        statusBadge.style.color = '#a855f7';
    }
});
