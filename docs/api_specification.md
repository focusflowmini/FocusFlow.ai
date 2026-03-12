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

### 1.3 Server -> Client: Intervention
Sent when the distraction score exceeds the threshold.

```json
{
  "type": "intervention",
  "data": {
    "action": "block",
    "reason": "Semantic drift detected. Current focus: 'Researching FastAPI', but visiting 'Gaming Content'.",
    "score": 0.85
  }
}
```

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
  "status": "active"
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
