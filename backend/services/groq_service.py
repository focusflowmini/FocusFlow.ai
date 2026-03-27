import groq
from config import settings
import json

class GroqService:
    def __init__(self):
        self.client = groq.Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_relevance(self, goal: str, current_tab_title: str, current_tab_url: str, context: list = None, is_focus_tab: bool = False):
        """
        Analyzes relevance with added context from previous tabs and focus anchor status.
        """
        context_str = "\n".join([f"- {c.get('title')} ({c.get('url')})" for c in (context or [])])
        
        prompt = f"""
        User Goal: {goal}
        
        Recent Browsing Context (last 5 tabs):
        {context_str if context_str else "No prior history for this session."}

        Currently Visiting:
        Title: {current_tab_title}
        URL: {current_tab_url}
        Is this the primary 'Focus Anchor' tab? {'Yes' if is_focus_tab else 'No'}

        Your task is to determine if the user is currently focused on their goal or if they are being distracted.
        
        Special Instructions:
        1. If the current tab is the 'Focus Anchor', the relevance should generally be higher unless the content completely changed.
        2. If the user is on a different tab, look at the recent context to see if they are following a logical research path (e.g., searching for a bug found in the focus tab).
        3. Penalize heavily if the current tab is a known distraction site (Social Media, Entertainment) and NOT the focus tab.

        Return ONLY a JSON object:
        {{
            "relevance_score": float (0.0 to 1.0),
            "is_distracted": boolean,
            "reasoning": "Short explanation considering the context shift"
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior productivity coach analyzing focus patterns."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "relevance_score": 0.5,
                "is_distracted": False,
                "reasoning": "Error in AI analysis. Defaulting to neutral."
            }

groq_service = GroqService()
