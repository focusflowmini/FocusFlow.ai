from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict
from config import settings
from services.tracker import SessionTracker
from services.agent_logic import focus_agent

import os

app = FastAPI(title=settings.app_name)

SESSION_FILE = "sessions.json"

# Session Registry to support multiple concurrent users
session_registry: Dict[str, SessionTracker] = {}

def save_sessions():
    try:
        data = {sid: tracker.to_dict() for sid, tracker in session_registry.items()}
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving sessions: {e}")

def load_sessions():
    global session_registry
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                session_registry = {sid: SessionTracker.from_dict(tdata) for sid, tdata in data.items()}
                print(f"Loaded {len(session_registry)} sessions from disk.")
        except Exception as e:
            print(f"Error loading sessions: {e}")

# Load sessions on startup
load_sessions()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "FocusFlow Brain is online",
        "status": "healthy",
        "active_sessions": len(session_registry)
    }

@app.post("/session/start")
async def start_session(data: dict):
    goal = data.get("goal", "Focusing on work")
    whitelist = data.get("whitelist", [])
    session_id = str(uuid.uuid4())
    
    tracker = SessionTracker(session_id=session_id, goal=goal, whitelist=whitelist)
    session_registry[session_id] = tracker
    save_sessions()
    
    return {
        "message": "Session initialized",
        "session_id": session_id,
        "goal": goal
    }

@app.post("/session/reset")
async def reset_sessions():
    global session_registry
    session_registry = {}
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    
    # Truncate agent logs as valid JSON array
    if os.path.exists("agent_logs.json"):
        with open("agent_logs.json", "w") as f:
            f.write("[]")
            
    return {"message": "All sessions and logs have been reset"}

@app.websocket("/ws/track/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in session_registry:
        print(f"Connection rejected: Invalid Session ID {session_id}")
        await websocket.close(code=4001, reason="Invalid Session ID")
        return

    tracker = session_registry[session_id]
    await websocket.accept()
    print(f"Session {session_id} connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "tab_update":
                tab_data = message.get("data", {})
                url = tab_data.get("url", "")
                title = tab_data.get("title", "")
                tab_id = tab_data.get("tab_id")
                
                is_focus = (tab_id == tracker.focus_tab_id) if tracker.focus_tab_id else False
                
                # RUN THE AGENTIC WORKFLOW
                agent_result = await focus_agent.run({
                    "goal": tracker.goal,
                    "anchor_title": tracker.focus_tab_title,
                    "current_tab": {"title": title, "url": url},
                    "context_history": tracker.context_window,
                    "is_focus_tab": is_focus,
                    "current_score": tracker.distraction_score
                })
                
                # MODULAR OBSERVATION (RabbitHole Detection & Prevention)
                observation = tracker.logges.observe(
                    category=agent_result.get("category", "UNKNOWN"),
                    relevance=agent_result.get("relevance_score", 0.5),
                    current_score=agent_result.get("current_score", tracker.distraction_score),
                    history=tracker.context_window,
                    llm_drift=agent_result.get("is_drifting", False)  # Pass the LLM drift signal
                )
                
                # Finalize Strategy
                action = observation["strategy"]
                reason = observation["reason"]
                
                # Update tracker state from Agent results
                tracker.distraction_score = agent_result.get("current_score", tracker.distraction_score)
                tracker.add_to_context({"title": title, "url": url})
                
                # RECORD ACTION
                tracker.logges.record_action(action, reason, {
                    "category": agent_result.get("category"),
                    "relevance": agent_result.get("relevance_score"),
                    "rolling_avg": observation["rolling_avg"],
                    "drift_detected": observation["drift_detected"],
                    "tab_id": tab_id
                })
                
                # Send Agentic Action to Extension
                await websocket.send_text(json.dumps({
                    "type": "agent_action",
                    "data": {
                        "action": action,
                        "category": agent_result.get("category", "UNKNOWN"),
                        "reason": f"{agent_result.get('reasoning')} | {reason}",
                        "score": tracker.distraction_score,
                        "drift_detected": observation["drift_detected"],
                        "rolling_avg": observation["rolling_avg"],
                        "tab_id": tab_id
                    }
                }))
                
                # Persist state after update
                save_sessions()
                    
            elif msg_type == "set_focus_tab":
                tab_id = message.get("tab_id")
                tab_title = message.get("title", "Focus Anchor")
                tracker.set_focus_tab(tab_id, tab_title)
                await websocket.send_text(json.dumps({
                    "type": "ack",
                    "message": f"Focus anchor set to '{tab_title}' (ID: {tab_id})"
                }))

            elif msg_type == "feedback":
                feedback_data = message.get("data", {})
                if feedback_data.get("is_productive"):
                    tracker.distraction_score = max(0, tracker.distraction_score - 1.5)
                    save_sessions()
                    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")

# Legacy endpoint handler to catch old extensions
@app.websocket("/ws/track")
async def legacy_websocket(websocket: WebSocket):
    await websocket.accept()
    print("Rejected legacy connection attempt to /ws/track")
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": "Legacy extension detected. Please refresh the extension."
    }))
    await websocket.close(code=4000)
