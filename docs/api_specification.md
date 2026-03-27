# API Specification - FocusFlow

## 1. WebSocket Protocol (Real-time Feedback)

The WebSocket server is available at `ws://<backend-url>/ws/track`.

### 1.1 Client -> Server: Tab Update
Sent whenever the active tab URL/Title changes.

```json
{
  "type": "tab_update",
  "data": {
    "url": "https://www.youtube.com/watch?v=...",
    "title": "Learn FastAPI in 10 Minutes",
    "is_focus_tab": false,
    "timestamp": "2023-10-27T10:00:00Z"
  }
}
```

### 1.2 Client -> Server: User Feedback
Sent when a user overrides a block.

```json
{
  "type": "feedback",
  "data": {
    "url": "https://example.com",
    "is_productive": true,
    "reason": "Researching specific component"
  }
}
```

### 1.3 Server -> Client: Agent Action
Sent when the LangGraph agent decides on an autonomous strategy.

```json
{
  "type": "agent_action",
  "data": {
    "action": "BLOCK | WARN | NOTIFY | ALLOW",
    "category": "SOCIAL_MEDIA | WORK_RELATED | RESEARCH | UNKNOWN",
    "reason": "Agent reasoning logic here...",
    "score_impact": 0.2,
    "current_score": 0.85
  }
}
```

- **BLOCK:** Injects the full blocker overlay.
- **WARN:** Shows a semi-transparent warning at the top of the tab.
- **NOTIFY:** Sends a browser notification (desktop) but doesn't interrupt the tab.
- **ALLOW:** Updates the internal score but takes no visible action.

## 2. REST API (Session Management)

### 2.1 POST /session/start
Initializes a new session with a target focus goal.

**Request Body:**
```json
{
  "goal": "Building a Chrome Extension with FastAPI backend",
  "whitelist": ["stackoverlow.com", "github.com"]
}
```

**Response:**
```json
{
  "session_id": "uuid-v4-string",
  "status": "active",
  "goal": "Building a Chrome Extension..."
}
```

### 2.2 GET /session/status
Retrieves the current distraction score and summary of the session.

**Response:**
```json
{
  "current_score": 0.15,
  "history": [...],
  "top_distractions": [...]
}
```
