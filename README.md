# FocusFlow 🧠✨
### The Agentic AI Productivity Observer

FocusFlow is a high-performance, agentic productivity ecosystem that doesn't just track your time—it **understands your intent.** By leveraging **LangGraph** and the **Groq Llama-3-70b Engine**, FocusFlow autonomously protects your deep-work sessions while allowing for logical research progressions.

---

## 🚀 Key Features

### 1. Agentic Autonomous Decision Loop (LangGraph)
Unlike static blockers that rely on blacklists, FocusFlow uses a sophisticated **LangGraph workflow** to analyze your browsing in real-time.
- **Node-based Reasoning:** The "Brain" evaluates your current tab against your session goal, analyzes recent context history, and determines an autonomous strategy.
- **Adaptive Interventions:** Action selection ranges from gentle reminders for "soft distractions" to hard blocks for "rabbit holes."

### 2. Focus Anchor (Tab Locking)
Lock your session onto a specific **Focus Tab** (e.g., VS Code, GitHub, or Documentation). FocusFlow treats this as your "Anchor." Any deviation from this anchor triggers a higher scrutiny level from the AI Agent.

### 3. Semantic Context Window
The Agent maintains a sliding window of your recent browsing history. It understands if you're switching to Stack Overflow to solve a bug found in your Focus Tab, or if you've drifted into unrelated territory.

### 4. Premium Chrome Observer
- **Vibrant UI:** A sleek, modern dashboard built with Glassmorphism and minimalist design.
- **Real-time Feedback:** Integrated content scripts provide beautiful, non-intrusive (or highly intrusive, if you're failing!) blocking overlays.
- **Productivity Overrides:** One-click "Actually Productive" feedback to train your personal agent in real-time.

---

## 🛠️ Architecture

FocusFlow follows a dual-component architecture:
1.  **The Observer (Chrome Extension):** Built with Manifest V3. Monitors active tab telemetry and enforces agentic decisions via WebSockets.
2.  **The Brain (FastAPI + LangGraph):** The orchestration layer. Receives events, runs them through the LangGraph reasoning chain, and executes autonomous actions via Groq's high-speed inference.

---

## 🏁 Getting Started (Phase 3 Alpha)

### Requirements
- Python 3.10+
- `uv` (modern package manager)
- Groq API Key

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/FocusFlow.ai.git
    cd FocusFlow.ai/backend
    ```

2.  **Setup Environment:**
    ```bash
    # Create .env file
    echo "GROQ_API_KEY=your_key_here" > .env
    ```

3.  **Run the Brain:**
    ```bash
    uv run uvicorn main:app --reload
    ```

4.  **Install the Observer:**
    - Open `chrome://extensions/`.
    - Enable "Developer mode".
    - Click "Load unpacked" and select the `extension/` folder in this repo.

---

## 🗺️ Roadmap
- [x] **Phase 1:** Core Classification & Blocking.
- [x] **Phase 2:** Multi-user support & Focus Anchoring.
- [/] **Phase 3:** LangGraph Agentic Transition (In Development).
- [ ] **Phase 4:** Long-term memory & fine-tuning based on user history.

---

Built with ❤️ for focused builders.