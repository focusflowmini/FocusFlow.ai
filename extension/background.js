let socket = null;
let sessionId = null;

function connectWebSocket() {
    chrome.storage.local.get(['session_id'], (result) => {
        sessionId = result.session_id;
        if (!sessionId) return;

        socket = new WebSocket(`ws://localhost:8000/ws/track/${sessionId}`);

        socket.onopen = () => {
            console.log("Connected to Brain with Session:", sessionId);
        };

        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === "agent_action") {
                handleAgentAction(message.data);
            }
        };

        socket.onclose = () => {
            console.log("WebSocket disconnected. Retrying in 5s...");
            setTimeout(connectWebSocket, 5000);
        };
    });
}

function handleAgentAction(data) {
    const targetTabId = Number(data.tab_id);
    if (!targetTabId) {
        console.error("No valid tab_id in agent action:", data);
        return;
    }

    console.log(`Executing Agent Action: ${data.action} on Tab: ${targetTabId}`);

    switch (data.action) {
        case "BLOCK":
            chrome.tabs.sendMessage(targetTabId, { 
                type: "BLOCK_PAGE", 
                reason: data.reason,
                category: data.category 
            }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error(`BLOCK failed for tab ${targetTabId}:`, chrome.runtime.lastError.message);
                } else {
                    console.log(`BLOCK message delivered to tab ${targetTabId}`);
                }
            });
            break;
        case "WARN":
            chrome.tabs.sendMessage(targetTabId, { 
                type: "SHOW_WARNING", 
                reason: data.reason 
            }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error(`WARN failed for tab ${targetTabId}:`, chrome.runtime.lastError.message);
                } else {
                    console.log(`WARN message delivered to tab ${targetTabId}`);
                }
            });
            break;
        case "NOTIFY":
            chrome.notifications.create({
                type: "basic",
                iconUrl: "icons/icon48.png",
                title: "FocusFlow Warning",
                message: data.reason,
                priority: 2
            });
            break;
        case "ALLOW":
            console.log(`Agent allowed tab ${targetTabId}:`, data.reason);
            break;
    }
}

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active) {
        sendTabUpdate(tab);
    }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        sendTabUpdate(tab);
    });
});

function sendTabUpdate(tab) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    const data = {
        type: "tab_update",
        data: {
            url: tab.url,
            title: tab.title,
            tab_id: tab.id,
            timestamp: new Date().toISOString()
        }
    };
    socket.send(JSON.stringify(data));
}

function startSession(goal) {
    if (socket) socket.close();
    connectWebSocket();
    // Optionally send goal to backend if needed
}

function stopSession() {
    if (socket) socket.close();
    socket = null;
    if (anchorTabId) {
        chrome.tabs.sendMessage(anchorTabId, { type: "REMOVE_HIGHLIGHT" }).catch(() => {});
        anchorTabId = null;
    }
}

// Initial connection attempt
connectWebSocket();

// Handle messages from popup or content scripts
let anchorTabId = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "START_SESSION") {
        startSession(message.goal);
    } else if (message.type === "STOP_SESSION") {
        stopSession();
    } else if (message.type === "SET_FOCUS_TAB") {
        // Remove highlight from old anchor
        if (anchorTabId) {
            chrome.tabs.sendMessage(anchorTabId, { type: "REMOVE_HIGHLIGHT" }).catch(() => {});
        }
        anchorTabId = message.tab_id;
        // Add highlight to new anchor
        chrome.tabs.sendMessage(anchorTabId, { type: "ADD_HIGHLIGHT" }).catch(() => {});
        
        // Forward to backend
        if (socket && socket.readyState === WebSocket.OPEN) {
            chrome.tabs.get(anchorTabId, (tab) => {
                socket.send(JSON.stringify({ 
                    type: "set_focus_tab", 
                    tab_id: anchorTabId,
                    title: tab.title 
                }));
            });
        }
    } else if (message.type === "IGNORE_BLOCK") {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "feedback", data: { url: message.url, is_productive: true } }));
        }
    }
});
