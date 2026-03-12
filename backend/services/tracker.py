from datetime import datetime

class SessionTracker:
    def __init__(self, goal: str, whitelist: list = None):
        self.goal = goal
        self.whitelist = whitelist or []
        self.distraction_score = 0.0
        self.history = []
        self.threshold = 1.5  # Cumulative score threshold for intervention
        self.decay_rate = 0.1 # Score decays over time for neutral/productive sites

    def update_score(self, relevance_result: dict):
        score = relevance_result.get("relevance_score", 0.5)
        
        # Invert relevance for distraction scoring
        # If relevance is 1.0 (productive), we decrease distraction score
        # If relevance is 0.0 (distraction), we increase distraction score
        impact = (0.5 - score) * 2 # Maps 1.0 -> -1.0, 0.0 -> 1.0
        
        self.distraction_score = max(0, self.distraction_score + impact)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "impact": impact,
            "current_score": self.distraction_score,
            "reasoning": relevance_result.get("reasoning", "")
        }
        self.history.append(log_entry)
        
        return self.distraction_score > self.threshold

    def add_to_whitelist(self, url: str):
        self.whitelist.append(url)

    def get_status(self):
        return {
            "goal": self.goal,
            "current_score": self.distraction_score,
            "history_count": len(self.history)
        }
