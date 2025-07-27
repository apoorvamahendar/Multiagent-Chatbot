
# 🧠 LangGraph Multi-Agent Chatbot

A conversational AI chatbot built with **LangGraph**, **Streamlit**, and **Groq**, capable of intelligently answering questions about **weather**, **stocks**, or **general topics** by routing through specialized tools. Supports both **Auto Mode** and **Human-in-the-Loop (HITL)** approval for production-ready conversations.

---

## 🌟 Key Features

- 🤖 **Multi-Agent Architecture**  
  Uses dynamic tool selection based on user input:
  - `weather_agent`: Weather queries (forecast, temperature)
  - `stock_agent`: Stock market info (prices, tickers)
  - `qa_agent`: Final answer summarization (always last)

- 🔁 **LLM-based Tool Planner**  
  Powered by Groq’s `llama3-70b-8192`, which selects relevant tools for each input.

- 🧠 **LangGraph Flow Control**  
  Orchestrates multi-step reasoning via conditional graph edges between agents.

- ✅ **Human-in-the-Loop (HITL)** Mode  
  Pause bot responses for manual **Approve** / **Reject** flow with feedback logging.

- ⚡ **Auto Mode**  
  Skips approval and responds instantly — useful for fast prototyping or live deployment.

- 💬 **Streamlit Chat Interface**  
  Clean UI with chat bubbles, feedback handling, sidebar toggles, and log export.

- 📝 **Session Memory**  
  Maintains conversation context and supports full-session summarization.

- 📂 **Logging and Auditing**  
  All interactions (approved, rejected, edited) are saved to `history.txt`.

---

## 🖥️ Demo Preview

```
User: What is the weather in Bangalore today?
Bot: 🌦️ It's partly cloudy in Bangalore with a temperature of 25.2°C.

---
👤 Awaiting human approval...
```

---

## 📦 Project Structure

```
.
├── main.py                  # LangGraph + Streamlit chatbot
├── tools/
│   ├── tool1_weather.py     # Weather API tool
│   ├── tool2_stock.py       # Stock data extractor (e.g. Yahoo)
│   └── tool3_general_qa.py  # General Q&A fallback
├── .env                     # API keys (Groq)
├── history.txt              # Logs of interactions
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/langgraph-multiagent-chatbot.git
cd langgraph-multiagent-chatbot
```

### 2. Add Your `.env` File

Create a `.env` file in the root directory and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Install Python Dependencies

Make sure you're using Python **3.8+**.

```bash
pip install -r requirements.txt
```

### 4. Run the Chatbot (Streamlit UI)

```bash
streamlit run main.py
```

---

## 🧠 How It Works

1. **User Input** is captured via chat.
2. **Planner Node** analyzes the last few messages and chooses which tools to run.
3. **Tool Execution** follows a LangGraph flow:
    - `weather_agent` and/or `stock_agent` gather context.
    - `qa_agent` composes the final response using gathered context + chat history.
4. The bot shows the final answer either:
    - Immediately (Auto Mode)
    - Or waits for **approval/rejection** (HITL Mode)
5. All interactions are saved to `history.txt` with approval status.

---

## 🛠️ Tool Summary

| Tool Name      | Function                                         |
|----------------|--------------------------------------------------|
| `weather_agent`| Fetches weather details from the query context  |
| `stock_agent`  | Extracts company/ticker info and fetches stock data |
| `qa_agent`     | Generates the final answer using all gathered context |

---

## 🧍 Human-in-the-Loop Mode (HITL)

When **Auto Mode** is disabled (via sidebar checkbox), each response is held for manual review:

- ✅ Approve: Final answer is accepted and logged.
- ❌ Reject: You can provide a correction or rephrase the question.
- 📝 Feedback: All rephrased queries are re-evaluated by the planner.
- 📄 Logged to `history.txt` for auditing and fine-tuning.

---

## ⚡ Auto Mode

Enable the **Auto Mode** checkbox in the sidebar to let the chatbot respond without human approval.

Ideal for:
- Fast interactions
- Live demos
- Testing agent flow

---

## 📜 Logging Format

All interactions are logged to `history.txt` like this:

```
User: What's the weather in Delhi?
Bot: ☀️ It's sunny in Delhi today with 0% rain probability.
Approved: True
```

Rejected or edited responses are also logged.

---

## 🧪 CLI Mode (Optional)

If Streamlit isn't available or you're running in headless environments:

```bash
python main.py
```

You can type queries in the terminal and receive multi-agent responses.

---

## ✅ Requirements

Ensure the following Python libraries are installed:

- `streamlit`
- `langchain`
- `langgraph`
- `langchain-groq`
- `python-dotenv`
- `ast` *(builtin)*

Install all at once using:

```bash
pip install -r requirements.txt
```

---

## 🔒 API Keys

Only your **Groq API key** is required. You can use the `.env` file to keep credentials secure.

```
GROQ_API_KEY=your_groq_key_here
```

---

## 🙏 Acknowledgements

- [LangChain](https://www.langchain.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Groq](https://console.groq.com/)
- [Streamlit](https://streamlit.io/)

---

## 📄 License

MIT License  
© 2025 [Apoorva Mahendar M](https://github.com/apoorvamahendar)
