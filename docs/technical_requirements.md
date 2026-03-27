# Technical Requirements - FocusFlow (Agentic AI)

## 1. Functional Requirements

### 1.1 Web Tracking (The Observer)
- **Active Tab Monitoring:** The extension must detect when the user switches to a new tab or when the URL/Title of the current tab changes.
- **Focus Tab Selection:** Users can mark a specific tab as the "Focus Anchor". Any deviation from this tab increases the distraction penalty.
- **WebSocket Communication:** The extension must maintain a persistent WebSocket connection to the backend to transmit tab data in real-time. Each connection must be identified by a unique `session_id`.
- **Heartbeat:** The extension should send a heartbeat to ensure the connection is active.

### 1.2 Agentic Brain (LangGraph)
- **Multi-User Session Registry:** Support multiple concurrent users by managing sessions in a registry.
- **Autonomous Decision Loop:** Implement a LangGraph-based agent that orchestrates tab evaluation and action selection.
- **Semantic Classification:** Categorize intent (e.g., `CORE_WORK`, `SUPPORTING_RESEARCH`, `SOFT_DISTRACTION`, `HARD_DISTRACTION`).
- **Context Awareness:** Maintain recent tab history (context window) for each session to detect semantic drift.
- **Dynamic Policy:** The agent decides whether to block, warn, or simply log based on the classification and session status.
- **Override/Whitelist:** Allow users to whitelist specific domains or manually override a block.

### 1.3 Autonomous Interventions
- **Action Selection:** The agent automatically chooses from a set of interventions: `BLOCK`, `WARNING`, `NOTIFY`, `ALLOW`.
- **Injection Logic:** The extension must handle multiple message types from the backend to deliver the correct UI intervention.
- **Adaptive Learning:** The agent should attempt to "reason" why a site is allowed or blocked based on the focus goal and previous history.
- **User Feedback:** The blocking overlay should include an option for the user to mark a site as "Actually Productive," which updates the agent's memory.

## 2. Non-Functional Requirements
- **Performance:** WebSocket communication should have latency < 200ms for responsiveness.
- **Deployment:** The backend must be deployable to Render's free tier.
- **Reliability:** The system must handle WebSocket reconnections gracefully.
- **Privacy:** Data should be processed locally (or via Groq API) and not stored permanently beyond the session duration, unless user opts-in for history tracking.
- **Persistence:** Use a database (e.g., PostgreSQL) to store session meta-data and long-term focus analytics for the user dashboard.
- **Aesthetics:** The extension's popup and blocking UI must follow premium design principles (vibrant colors, clean typography, smooth transitions).
