import groq
from config import settings
import json

class GroqService:
    def __init__(self):
        self.client = groq.Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_relevance(self, goal: str, current_tab_title: str, current_tab_url: str):
        """
        Analyzes the relevance of a web page to a specific user goal.
        Returns a JSON object with relevance score (0-1) and reasoning.
        """
        prompt = f"""
        User Goal: {goal}
        Current Page Title: {current_tab_title}
        Current Page URL: {current_tab_url}

        Your task is to determine if the user is currently focused on their goal or if they are being distracted.
        Consider:
        1. Does the page content (from title/url) directly assist in the goal?
        2. Is it a known productive tool (e.g., StackOverflow, GitHub, Documentation) related to the goal?
        3. Is it a known source of distraction (Social Media, Gaming, Entertainment) that is NOT the goal?

        Return ONLY a JSON object:
        {{
            "relevance_score": float (0.0 for pure distraction, 1.0 for perfect focus),
            "is_distracted": boolean,
            "reasoning": "Short explanation"
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a productivity analysis agent."},
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
