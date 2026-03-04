# ⚡ OneCharge AI Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain)](https://langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai)](https://openai.com/)

**OneCharge AI** is a professional-grade, agentic customer support backend for an on-demand EV service application. It uses advanced AI reasoning to provide battery swaps, roadside assistance, and real-time maintenance tracking.

---

## 🚀 Key Features

- **🧠 Agentic AI Reasoning:** Uses LangGraph's "ReAct" pattern to intelligently decide when to look up user data using custom tools.
- **🛡️ Production-Ready Security:** Implements Pydantic validation and field length limits to prevent prompt injection and malicious inputs.
- **🤝 Personalization Engine:** Automatically greets users by name during their first interaction.
- **📡 Multi-Platform Ready:** Full CORS support enabled, allowing seamless connection with Flutter, React, or mobile applications.
- **⚓ Reliability built-in:** Includes a "Safety Net" error-handling system that ensures the API stays alive even if AI services blip.

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **AI Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) / [LangChain](https://www.langchain.com/)
- **LLM:** OpenAI `gpt-4o-mini`
- **Validation:** Pydantic v2
- **Persistence:** In-memory with LangGraph `MemorySaver`

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jantheres/onecharge-ai.git
   cd onecharge-ai
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/scripts/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_key_here
   ```

5. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat/send/{user_id}` | Send a message to the AI agent. |
| `GET` | `/api/chat/history/{user_id}` | Retrieve formatted chat history for a session. |

## 🛠️ AI Tools (Mocked)
The backend is currently equipped with three simulated tools ready to be connected to your production database:
- `get_booking_details`: Checks repair slots and payment status.
- `get_ticket_status`: Monitors active service stages and wait times.
- `get_driver_gps`: Tracks driver location signal age.

---

## 🏠 Project Structure
```text
f:\onecharge_ai\
├── main.py        # Core application logic & AI Agent
├── .env           # Secrets (not committed)
├── requirements.txt
└── .gitignore     # Optimized for Python/OpenAI
```

## 📄 Documentation
For a deep dive into the business rules and FAQ knowledge base, see [`chatbot_documentation.txt`](./chatbot_documentation.txt).

---
*Created with ❤️ by jantheres*
