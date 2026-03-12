# Architecture Design - FocusFlow

## 1. System Overview
FocusFlow follows a client-server architecture where the Chrome Extension acts as the **Observer** and the FastAPI backend acts as the **Brain**.

```mermaid
graph TD
    A[Chrome Browser] --> B[Chrome Extension - The Observer]
    B -->|WebSocket| C[FastAPI Server - The Brain]
    C -->|API Call| D[Groq LLM Engine]
    C -->|State| E[In-Memory Session Store]
    B -->|Content Script| F[Web Page Blocker]
    F -->|Feedback| B
```

## 2. Component Breakdown

### 2.1 The Observer (Frontend)
- **Background Script:** Uses `chrome.tabs.onUpdated` and `chrome.tabs.onActivated` to monitor user activity.
- **WebSocket Client:** Manages the persistent connection to the Brain. Handles auto-reconnects.
- **Content Scripts:** Injected into tabs to enforce "blocks." It uses a premium CSS overlay to obscure distracting content.
- **Popup UI:** Built with Vanilla HTML/CSS/JS. High-performance, low latency, and follows the "FocusFlow" premium aesthetic.

### 2.2 The Brain (Backend)
- **FastAPI Core:** Provides the WebSocket server and REST endpoints for session initialization.
- **LLM Service (Groq):** A dedicated service that crafts prompts for the Groq API to determine semantic relevance.
- **State Machine:** A logic layer that tracks the user's progress through a "Path." It uses a scoring algorithm to decide when a "rabbit hole" has been entered.
- **Session Manager:** Tracks metadata for the current session (e.g., target task, whitelist, distraction history).

## 3. Technology Stack
- **Frontend:** HTML5, CSS3, ES6 JavaScript, Chrome Extensions API (Manifest V3).
- **Backend:** Python 3.10+, FastAPI, `websockets`, `uvicorn`.
- **AI:** Groq Cloud API (Llama-3-70b or similar).
- **Hosting:** Render (Free Tier).

## 4. Security & Privacy
- **Encryption:** WebSocket connections should use `wss://` in production.
- **Local-First:** While the brain runs on Render, the user's browsing history is ephemeral and cleared at the end of each session.
- **Minimal Extraction:** Only URL and Title are sent to the brain; no full DOM content is transmitted in the MVP.
