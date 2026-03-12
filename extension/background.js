let socket = null;
let currentSession = null;

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:8000/ws/track");

    socket.onopen = () => {
        console.log("WebSocket connected to FocusFlow Brain");
    };

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "intervention") {
            handleIntervention(message.data);
        }
    };

    socket.onclose = () => {
        console.log("WebSocket disconnected. Retrying in 5s...");
        setTimeout(connectWebSocket, 5000);
    };
}

function handleIntervention(data) {
    if (data.action === "block") {
        // Find current tab and send message to content script
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { type: "BLOCK_PAGE", reason: data.reason });
            }
        });
    }
}

// Monitor tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.active) {
        sendTabUpdate(tab);
    }
});

// Monitor tab activation (switching tabs)
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
            timestamp: new Date().toISOString()
        }
    };
    socket.send(JSON.stringify(data));
}

// Initial connection
connectWebSocket();

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "IGNORE_BLOCK") {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "feedback",
                data: {
                    url: message.url,
                    is_productive: true
                }
            }));
        }
    }
});
