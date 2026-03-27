import json
import dspy
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from config import settings

# --- DSPy Signatures ---

class IntentionClassify(dspy.Signature):
    """Classify user browser activity based on their productivity goal and focus anchor."""
    goal = dspy.InputField(desc="The user's productivity goal")
    anchor_title = dspy.InputField(desc="Title of the primary Focus Anchor tab")
    tab_title = dspy.InputField(desc="Title of the current browser tab")
    tab_url = dspy.InputField(desc="URL of the current browser tab")
    
    category = dspy.OutputField(desc="One of: CORE_WORK, SUPPORTING_RESEARCH, NEUTRAL, SOFT_DISTRACTION, HARD_DISTRACTION")
    reasoning = dspy.OutputField(desc="How this tab relates to the Goal OR the Focus Anchor")

class RelevanceAudit(dspy.Signature):
    """Audit the relevance of the current tab relative to the Focus Anchor."""
    goal = dspy.InputField(desc="The user's productivity goal")
    anchor_title = dspy.InputField(desc="Title of the primary Focus Anchor tab")
    category = dspy.InputField(desc="Intent category of the tab")
    tab_title = dspy.InputField(desc="Current tab title")
    history = dspy.InputField(desc="Recent browsing history")
    
    relevance = dspy.OutputField(desc="Float from 0.0 to 1.0 (1.0 = Highly relevant to Goal/Anchor)")
    is_drifting = dspy.OutputField(desc="Boolean indicating if user is entering a rabbit hole")
    reasoning = dspy.OutputField(desc="Strategic explanation")

# --- Agentic Logic ---

class AgentState(TypedDict):
    goal: str
    anchor_title: str
    current_tab: Dict[str, str]
    context_history: List[Dict[str, str]]
    is_focus_tab: bool
    current_score: float
    category: str
    relevance_score: float
    decision: str
    reasoning: str
    is_drifting: bool

class FocusFlowAgent:
    def __init__(self):
        # Configure DSPy with Groq
        self.lm = dspy.LM(
            f"groq/{settings.groq_model}", 
            api_key=settings.groq_api_key,
            cache=False
        )
        dspy.settings.configure(lm=self.lm)
        
        # Define DSPy Modules
        self.classifier = dspy.Predict(IntentionClassify)
        self.auditor = dspy.Predict(RelevanceAudit)
        
        self.workflow = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("classify", self._classify_node)
        graph.add_node("evaluate", self._evaluation_node)
        graph.add_node("decide", self._decision_node)
        graph.set_entry_point("classify")
        graph.add_edge("classify", "evaluate")
        graph.add_edge("evaluate", "decide")
        graph.add_edge("decide", END)
        return graph.compile()

    async def _classify_node(self, state: AgentState) -> Dict:
        """Uses DSPy to classify tab intent."""
        result = self.classifier(
            goal=state['goal'],
            anchor_title=state['anchor_title'],
            tab_title=state['current_tab']['title'],
            tab_url=state['current_tab']['url']
        )
        return {
            "category": result.category,
            "reasoning": result.reasoning
        }

    async def _evaluation_node(self, state: AgentState) -> Dict:
        """Uses DSPy to audit relevance and detect drift."""
        history_str = "\n".join([f"- {c['title']}" for c in state['context_history'][-5:]])
        
        result = self.auditor(
            goal=state['goal'],
            anchor_title=state['anchor_title'],
            category=state['category'],
            tab_title=state['current_tab']['title'],
            history=history_str if history_str else "New Session"
        )
        
        try:
            rel = float(result.relevance)
        except:
            rel = 0.5
            
        return {
            "relevance_score": rel,
            "reasoning": result.reasoning,
            "is_drifting": str(result.is_drifting).lower() == "true"
        }

    async def _decision_node(self, state: AgentState) -> Dict:
        """Action logic with Focus Anchor protection."""
        rel = state['relevance_score']
        cat = state['category']
        score = state['current_score']
        
        # NEVER block or warn on the Focus Anchor itself
        if state['is_focus_tab']:
            return {"decision": "ALLOW", "current_score": max(0, score - 0.2)}

        impact = (0.5 - rel) * 2
        new_score = max(0, score + impact)
        
        if cat == "HARD_DISTRACTION" and not state['is_focus_tab']:
            decision = "BLOCK"
        elif new_score > 2.0:
            decision = "BLOCK"
        elif new_score > 1.2 or (cat == "SOFT_DISTRACTION" and rel < 0.3):
            decision = "WARN"
        elif rel < 0.5:
            decision = "NOTIFY"
        else:
            decision = "ALLOW"

        return {"decision": decision, "current_score": new_score}

    async def run(self, input_data: Dict) -> Dict:
        return await self.workflow.ainvoke(input_data)

focus_agent = FocusFlowAgent()
