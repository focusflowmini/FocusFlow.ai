# Technical Requirements - FocusFlow

## 1. Functional Requirements

### 1.1 Web Tracking (The Observer)
- **Active Tab Monitoring:** The extension must detect when the user switches to a new tab or when the URL/Title of the current tab changes.
- **Focus Tab Selection:** Users can mark a specific tab as the "Focus Anchor". Any deviation from this tab increases the distraction penalty.
- **WebSocket Communication:** The extension must maintain a persistent WebSocket connection to the backend to transmit tab data in real-time. Each connection must be identified by a unique `session_id`.
- **Heartbeat:** The extension should send a heartbeat to ensure the connection is active.

### 1.2 Back-end Logic (The Brain)
- **Multi-User Session Registry:** Support multiple concurrent users by managing sessions in a registry rather than a global state.
- **Semantic Classification:** Use the Groq API (LLM) to classify the user's intent based on the URL and Page Title of the active tab.
- **Context Awareness:** Maintain recent tab history (context window) for each session to detect semantic drift more accurately.
- **Distraction Scoring:** Calculate a distraction score based on the semantic distance from the target task, with higher weight applied when away from the "Focus Tab".
- **Override/Whitelist:** Allow users to whitelist specific domains or manually override a block.

### 1.3 Interventions
- **Site Blocking:** When the distraction threshold is exceeded, the backend must trigger an intervention signal.
- **UI Overlay:** The extension must inject a content script to block access to the distracting page and display a "Focus Restored" message.
- **User Feedback:** The blocking overlay should include an option for the user to mark a site as "Actually Productive," which updates the backend's understanding for the session.

## 2. Non-Functional Requirements
- **Performance:** WebSocket communication should have latency < 200ms for responsiveness.
- **Deployment:** The backend must be deployable to Render's free tier.
- **Reliability:** The system must handle WebSocket reconnections gracefully.
- **Privacy:** Data should be processed locally (or via Groq API) and not stored permanently beyond the session duration, unless user opts-in for history tracking.
- **Persistence:** Use a database (e.g., PostgreSQL) to store session meta-data and long-term focus analytics for the user dashboard.
- **Aesthetics:** The extension's popup and blocking UI must follow premium design principles (vibrant colors, clean typography, smooth transitions).
