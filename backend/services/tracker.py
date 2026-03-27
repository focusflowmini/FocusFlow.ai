from typing import Dict, Any, List
from services.logges import Logges

class SessionTracker:
    def __init__(self, session_id: str, goal: str, whitelist: list = None):
        self.session_id = session_id
        self.goal = goal
        self.whitelist = whitelist or []
        self.distraction_score = 0.0
        self.history = []
        self.context_window = [] # List of recent tab titles/URLs
        self.max_context = 5
        self.focus_tab_id = None # The "Anchor" tab
        self.focus_tab_title = "" # Title of the Anchor tab
        self.threshold = 2.0  # Increased threshold for more stability
        self.decay_rate = 0.05
        self.logges = Logges(session_id)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "whitelist": self.whitelist,
            "distraction_score": self.distraction_score,
            "history": self.history,
            "context_window": self.context_window,
            "focus_tab_id": self.focus_tab_id,
            "focus_tab_title": self.focus_tab_title,
            "logges": self.logges.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        obj = cls(data["session_id"], data["goal"], data["whitelist"])
        obj.distraction_score = data.get("distraction_score", 0.0)
        obj.history = data.get("history", [])
        obj.context_window = data.get("context_window", [])
        obj.focus_tab_id = data.get("focus_tab_id")
        obj.focus_tab_title = data.get("focus_tab_title", "")
        if "logges" in data:
            obj.logges = Logges.from_dict(data["logges"])
        return obj

    def update_score(self, relevance_result: dict, tab_id: int = None):
        score = relevance_result.get("relevance_score", 0.5)
        is_focus = (tab_id == self.focus_tab_id) if self.focus_tab_id else True
        
        # Base impact
        impact = (0.5 - score) * 2 # Maps 1.0 -> -1.0, 0.0 -> 1.0
        
        # Multiplier if deviating from Focus Tab
        if self.focus_tab_id and not is_focus and impact > 0:
            impact *= 1.5 # 50% more penalty for deviating from the anchor
            
        self.distraction_score = max(0, self.distraction_score + impact)
        
        # Update context window
        # (Actually handled by the caller to keep tracker pure, but we'll store a summary)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "impact": impact,
            "current_score": self.distraction_score,
            "reasoning": relevance_result.get("reasoning", ""),
            "is_on_focus_tab": is_focus
        }
        self.history.append(log_entry)
        
        return self.distraction_score > self.threshold

    def set_focus_tab(self, tab_id: int, title: str = ""):
        self.focus_tab_id = tab_id
        if title:
            self.focus_tab_title = title

    def add_to_context(self, tab_info: dict):
        self.context_window.append(tab_info)
        if len(self.context_window) > self.max_context:
            self.context_window.pop(0)

    def get_status(self):
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "current_score": self.distraction_score,
            "focus_tab_active": self.focus_tab_id is not None,
            "history_count": len(self.history)
        }
