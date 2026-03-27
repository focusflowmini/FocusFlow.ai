chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "BLOCK_PAGE") {
        injectBlocker(message.reason);
    } else if (message.type === "SHOW_WARNING") {
        injectWarning(message.reason);
    } else if (message.type === "ADD_HIGHLIGHT") {
        toggleHighlight(true);
    } else if (message.type === "REMOVE_HIGHLIGHT") {
        toggleHighlight(false);
    }
});

function toggleHighlight(enable) {
    let highlight = document.getElementById('focusflow-anchor-highlight');
    if (enable) {
        if (highlight) return;
        highlight = document.createElement('div');
        highlight.id = 'focusflow-anchor-highlight';
        highlight.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            border: 5px solid transparent;
            border-image: linear-gradient(to right, #6366f1, #a855f7) 1;
            box-sizing: border-box;
            pointer-events: none;
            z-index: 2147483646;
            box-shadow: inset 0 0 20px rgba(99, 102, 241, 0.4);
        `;
        document.documentElement.appendChild(highlight);
    } else {
        if (highlight) highlight.remove();
    }
}

function injectWarning(reason) {
    if (document.getElementById('focusflow-warning')) return;

    const warning = document.createElement('div');
    warning.id = 'focusflow-warning';
    warning.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(to right, #6366f1, #a855f7);
        color: white;
        padding: 10px 20px;
        z-index: 2147483647;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        animation: slideDown 0.3s ease-out;
    `;

    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes slideDown {
            from { transform: translateY(-100%); }
            to { transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);

    warning.innerHTML = `
        <span><strong>FocusFlow:</strong> ${reason}</span>
        <button id="ff-warning-close" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-left: 20px;">Got it</button>
    `;

    document.documentElement.appendChild(warning);

    document.getElementById('ff-warning-close').onclick = () => warning.remove();
    setTimeout(() => { if (warning) warning.remove(); }, 10000);
}

function injectBlocker(reason) {
    if (document.getElementById('focusflow-blocker')) return;

    const blocker = document.createElement('div');
    blocker.id = 'focusflow-blocker';
    blocker.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(10, 10, 12, 0.98);
        backdrop-filter: blur(10px);
        z-index: 2147483647;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        font-family: 'Inter', sans-serif;
        text-align: center;
        padding: 40px;
    `;

    blocker.innerHTML = `
        <div style="background: linear-gradient(135deg, #6366f1, #a855f7); width: 64px; height: 64px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 32px; margin-bottom: 24px;">F</div>
        <h1 style="font-size: 36px; margin-bottom: 12px; letter-spacing: -1px;">Focus Restored</h1>
        <p style="color: #94a3b8; font-size: 18px; max-width: 500px; line-height: 1.6; margin-bottom: 32px;">
            It looks like you've drifted off track. <br>
            <span style="color: #ef4444; font-weight: 600;">Reason:</span> ${reason}
        </p>
        <div style="display: flex; gap: 16px;">
            <button id="ff-back-btn" style="background: #17171a; border: 1px solid #26262a; color: white; padding: 14px 28px; border-radius: 12px; cursor: pointer; font-weight: 600;">I'll go back</button>
            <button id="ff-ignore-btn" style="background: linear-gradient(to right, #6366f1, #a855f7); border: none; color: white; padding: 14px 28px; border-radius: 12px; cursor: pointer; font-weight: 600;">Actually productive</button>
        </div>
    `;

    document.documentElement.appendChild(blocker);

    document.getElementById('ff-back-btn').onclick = () => {
        window.history.back();
        if (window.history.length <= 1) {
            window.close();
        }
    };

    document.getElementById('ff-ignore-btn').onclick = () => {
        blocker.remove();
        // Notify background script to update whitelist/model
        chrome.runtime.sendMessage({ type: "IGNORE_BLOCK", url: window.location.href });
    };
}
