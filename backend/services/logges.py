import datetime
import json
import os
from typing import List, Dict, Any

class RabbitHoleDetection:
    """Analyzes history to detect deep semantic drift using rolling averages."""
    @staticmethod
    def analyze_drift(history: List[Dict[str, str]], relevance_scores: List[float], llm_drift: bool = False) -> Dict[str, Any]:
        # Always calculate rolling avg if there is at least one score
        rolling_avg = sum(relevance_scores[-5:]) / len(relevance_scores[-5:]) if relevance_scores else 0.5
        is_trending_down = len(relevance_scores) >= 2 and relevance_scores[-1] < relevance_scores[-2]

        if len(relevance_scores) < 3:
            return {
                "is_rabbithole": False, 
                "rolling_avg": round(rolling_avg, 2),
                "is_trending_down": is_trending_down,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        # Calculate rolling average of last 5 scores
        recent_scores = relevance_scores[-5:]
        rolling_avg = sum(recent_scores) / len(recent_scores)
        
        # Trend detection: Are scores generally decreasing?
        is_trending_down = len(recent_scores) >= 2 and recent_scores[-1] < recent_scores[-2]
        
        # Rabbit Hole is detected if:
        # 1. Rolling average is very low (< 0.3)
        # 2. LLM explicitly flagged drifting and rolling average is mediocre (< 0.6)
        is_rabbithole = (rolling_avg < 0.3) or (llm_drift and rolling_avg < 0.6)
        
        return {
            "is_rabbithole": is_rabbithole,
            "rolling_avg": round(rolling_avg, 2),
            "is_trending_down": is_trending_down,
            "timestamp": datetime.datetime.now().isoformat()
        }

class Prevention:
    """Proactive logic for warnings based on scores, drift, and category."""
    @staticmethod
    def recommend_strategy(current_score: float, category: str, drift_info: Dict[str, Any]) -> str:
        is_rabbithole = drift_info["is_rabbithole"]
        avg = drift_info["rolling_avg"]
        
        if is_rabbithole:
            if avg < 0.2: return "BLOCK" # Deep rabbit hole
            return "WARN"
        
        if category == "HARD_DISTRACTION":
            return "BLOCK"
            
        if current_score > 1.8:
            return "BLOCK"
        elif current_score > 1.2 or (category == "SOFT_DISTRACTION" and avg < 0.5):
            return "WARN"
        elif avg < 0.7 or category == "NEUTRAL":
            return "NOTIFY"
        
        return "ALLOW"

class Action:
    """Logs the execution of agentic interventions."""
    @staticmethod
    def log_event(session_id: str, action_type: str, reason: str, details: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": session_id,
            "action": action_type,
            "reason": reason,
            "details": details
        }
        
        # Log to console
        print(f"[AGENT_ACTION] {json.dumps(log_entry, indent=2)}")
        
        # Persist to file (as a proper JSON array)
        try:
            logs = []
            if os.path.exists("agent_logs.json"):
                try:
                    with open("agent_logs.json", "r") as f:
                        content = f.read().strip()
                        if content:
                            logs = json.loads(content)
                except Exception:
                    logs = [] # Fallback if corrupted
            
            logs.append(log_entry)
            with open("agent_logs.json", "w") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"FAILED TO WRITE LOG: {e}")
            
        return log_entry

# Modular Observer Aggregator
class Logges:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.detector = RabbitHoleDetection()
        self.preventer = Prevention()
        self.actor = Action()
        self.relevance_history = []

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "relevance_history": self.relevance_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        obj = cls(data["session_id"])
        obj.relevance_history = data.get("relevance_history", [])
        return obj

    def observe(self, category: str, relevance: float, current_score: float, history: List[Dict[str, str]], llm_drift: bool = False):
        self.relevance_history.append(relevance)
        
        drift = self.detector.analyze_drift(history, self.relevance_history, llm_drift)
        strategy = self.preventer.recommend_strategy(current_score, category, drift)
        
        return {
            "strategy": strategy,
            "drift_detected": drift["is_rabbithole"],
            "rolling_avg": drift["rolling_avg"],
            "reason": f"Drift: {drift['is_rabbithole']}, Category: {category}, Avg: {drift['rolling_avg']}"
        }

    def record_action(self, action_type: str, reason: str, details: Dict[str, Any]):
        return self.actor.log_event(self.session_id, action_type, reason, details)
