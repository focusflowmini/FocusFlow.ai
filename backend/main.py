from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from config import settings
from services.groq_service import groq_service
from services.tracker import SessionTracker

app = FastAPI(title=settings.app_name)

# Global session state (Prototype supports single active session)
current_tracker: SessionTracker = None

# Enable CORS for Chrome Extension
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
        "session_active": current_tracker is not None
    }

@app.post("/session/start")
async def start_session(data: dict):
    global current_tracker
    goal = data.get("goal", "Focusing on work")
    whitelist = data.get("whitelist", [])
    current_tracker = SessionTracker(goal=goal, whitelist=whitelist)
    return {"message": "Session started", "goal": goal}

@app.websocket("/ws/track")
async def websocket_endpoint(websocket: WebSocket):
    global current_tracker
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "tab_update":
                if not current_tracker:
                    continue
                
                tab_data = message.get("data", {})
                url = tab_data.get("url", "")
                title = tab_data.get("title", "")
                
                # Analyze relevance with Groq
                analysis = await groq_service.analyze_relevance(
                    goal=current_tracker.goal,
                    current_tab_title=title,
                    current_tab_url=url
                )
                
                # Update tracker and check for intervention
                should_block = current_tracker.update_score(analysis)
                
                if should_block:
                    await websocket.send_text(json.dumps({
                        "type": "intervention",
                        "data": {
                            "action": "block",
                            "reason": analysis.get("reasoning", "Semantic drift detected."),
                            "score": current_tracker.distraction_score
                        }
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": {
                            "score": current_tracker.distraction_score,
                            "analysis": analysis
                        }
                    }))
                    
            elif message.get("type") == "feedback":
                # Handle user override/feedback
                if current_tracker:
                    feedback_data = message.get("data", {})
                    if feedback_data.get("is_productive"):
                        # Adjust score or whitelist
                        current_tracker.distraction_score = max(0, current_tracker.distraction_score - 1.0)
                        
    except WebSocketDisconnect:
        print("Extension disconnected")
