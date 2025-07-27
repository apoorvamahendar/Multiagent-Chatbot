import os
import streamlit as st
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
import ast

from tools import tool1_weather, tool2_stock, tool3_general_qa

load_dotenv()

if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "approved_history" not in st.session_state:
    st.session_state.approved_history = []
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

memory = st.session_state.memory

class AgentState(TypedDict, total=False):
    messages: Annotated[list, "shared"]
    chat_history: list
    weather_data: str
    stock_data: str
    final_answer: str
    next_tools: list[str]

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama3-70b-8192")

def planner_node(state: AgentState) -> AgentState:
    recent_chat = "\n".join([
        f"{'User' if isinstance(m, HumanMessage) else 'Bot'}: {m.content}"
        for m in state.get("messages", [])[-4:]
    ])
    tool_prompt = f"""
You are a tool selector for a multi-agent AI assistant.

Your job is to return ONLY a Python list of tool names to use (in correct order). Do NOT explain, comment, or add anything else.

Available tools:
- "weather_agent": for weather, temperature, or forecast-related queries
- "stock_agent": for stock prices, company tickers, or market-related questions
- "qa_agent": always include this LAST for summarizing final answers

Recent conversation:
{recent_chat}

Respond with a Python list of tool names. Example:
["weather_agent", "stock_agent", "qa_agent"]
"""
    raw_response = llm.invoke(tool_prompt).content.strip()
    try:
        selected_tools = ast.literal_eval(raw_response)
        if not isinstance(selected_tools, list):
            raise ValueError("Not a valid list")
    except Exception:
        selected_tools = ["qa_agent"]

    if "qa_agent" not in selected_tools:
        selected_tools.append("qa_agent")
    return {**state, "next_tools": selected_tools}

def router_fn(state: AgentState) -> str:
    tools = state.get("next_tools", [])
    return tools[0] if tools else "qa_agent"

weather_agent = RunnableLambda(lambda state: {
    **state,
    "weather_data": tool1_weather.invoke(state["messages"][-1].content),
    "next_tools": state["next_tools"][1:],
})

stock_agent = RunnableLambda(lambda state: {
    **state,
    "stock_data": tool2_stock.invoke(state["messages"][-1].content),
    "next_tools": state["next_tools"][1:],
})

def qa_agent_node(state: AgentState) -> AgentState:
    user_input = state["messages"][-1].content
    past_messages = state.get("chat_history", [])

    if "summarize" in user_input.lower() or "summary" in user_input.lower():
        filtered = [msg for msg in past_messages if "summarize" not in msg.content.lower()]
        num_user = sum(isinstance(msg, HumanMessage) for msg in filtered)
        num_bot = sum(isinstance(msg, AIMessage) for msg in filtered)
        if num_user < 1 or num_bot < 1:
            summary = "There is not enough conversation to summarize yet."
        else:
            history_text = "\n".join(
                f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
                for msg in filtered
            )
            prompt = (
                "You are a helpful assistant. Summarize the following conversation:\n\n"
                f"{history_text}\n\nWrite a clear and concise summary."
            )
            summary = llm.invoke(prompt).content.strip()
        updated_history = past_messages + [AIMessage(content=summary)]
        return {**state, "final_answer": summary, "chat_history": updated_history, "next_tools": []}

    history_text = "\n".join(
        f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
        for msg in past_messages[-6:]
    )

    context = ""
    if state.get("weather_data"):
        context += f"\n**Weather Info:**\n{state['weather_data']}\n"
    if state.get("stock_data"):
        context += f"\n**Stock Info:**\n{state['stock_data']}\n"

    prompt = (
        f"You are a helpful assistant. Use the conversation below to answer the latest user query.\n\n"
        f"{history_text}\n\nUser's latest message: \"{user_input}\"\n"
        f"{context.strip()}\n\nKeep it concise."
    )
    response = llm.invoke(prompt)
    answer = response.content.strip()

    if st.session_state.get("auto_mode", False):
        updated_history = past_messages + [
            HumanMessage(content=user_input),
            AIMessage(content=answer)
        ]
        return {
            **state,
            "final_answer": answer,
            "chat_history": updated_history,
            "next_tools": []
        }
    else:
        answer_with_note = (
            f"{answer}\n\n---\n👤 *Awaiting human approval...*\n(Approve or Reject below)"
        )
        updated_history = past_messages + [
            HumanMessage(content=user_input),
            AIMessage(content=answer_with_note)
        ]
        return {
            **state,
            "final_answer": answer_with_note,
            "chat_history": updated_history,
            "next_tools": []
        }

graph = StateGraph(AgentState)
graph.set_entry_point("planner")

graph.add_node("planner", planner_node)
graph.add_node("weather_agent", weather_agent)
graph.add_node("stock_agent", stock_agent)
graph.add_node("qa_agent", qa_agent_node)

graph.add_conditional_edges("planner", router_fn, {
    "weather_agent": "weather_agent",
    "stock_agent": "stock_agent",
    "qa_agent": "qa_agent",
})
graph.add_conditional_edges("weather_agent", router_fn, {
    "weather_agent": "weather_agent",
    "stock_agent": "stock_agent",
    "qa_agent": "qa_agent",
})
graph.add_conditional_edges("stock_agent", router_fn, {
    "weather_agent": "weather_agent",
    "stock_agent": "stock_agent",
    "qa_agent": "qa_agent",
})
graph.add_edge("qa_agent", END)

multiagent_app = graph.compile()

def invoke_multiagent(user_input: str) -> str:
    memory.chat_memory.add_user_message(user_input)

    approved_msgs = []
    for role, content in st.session_state.approved_history:
        if role == "user":
            approved_msgs.append(HumanMessage(content=content))
        elif role == "bot":
            approved_msgs.append(AIMessage(content=content))

    approved_msgs.append(HumanMessage(content=user_input))

    initial_state = {
        "messages": approved_msgs,
        "chat_history": approved_msgs
    }

    result = multiagent_app.invoke(initial_state)
    memory.chat_memory.add_ai_message(result["final_answer"])
    return result["final_answer"]

if __name__ == "__main__":
    try:
        import streamlit.web.bootstrap
        IS_STREAMLIT = True
    except ImportError:
        IS_STREAMLIT = False

    if IS_STREAMLIT or "STREAMLIT_SERVER_HEADLESS" in os.environ:
        st.set_page_config(page_title="LangGraph Chatbot", layout="centered")
        st.title("🧠 LangGraph Multi-Agent Chatbot")
        st.markdown("Ask about weather, stocks, or general questions!")

        st.sidebar.title("⚙️ Settings")
        auto_mode = st.sidebar.checkbox("Enable Auto Mode (No Human Approval)", value=False)
        st.session_state["auto_mode"] = auto_mode

        user_input = st.chat_input("Type your message...")

        if user_input:
            st.session_state.last_user_input = user_input
            st.session_state.chat_history.append(("user", user_input))
            with st.spinner("🧠 Thinking..."):
                reply = invoke_multiagent(user_input)
            st.session_state.chat_history.append(("bot", reply))

        for role, message in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(message)

            if role == "bot" and "Awaiting human approval" in message:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=message + "_approve"):
                        st.session_state["human_approval"] = True
                        st.success("✅ Approved! Final answer accepted.")
                        st.session_state.approved_history.append(("user", st.session_state.last_user_input))
                        st.session_state.approved_history.append(("bot", message))
                        os.makedirs("logs", exist_ok=True)
                        with open("history.txt", "a", encoding="utf-8") as f:
                            f.write(f"User: {st.session_state.last_user_input}\nBot: {message}\nApproved: True\n\n")

                with col2:
                    if st.button("❌ Reject", key=message + "_reject"):
                        st.session_state["human_approval"] = False
                        st.session_state["rejected_message"] = message
                        st.session_state["show_feedback"] = True
                        st.warning("❌ Rejected. You may rephrase your question.")
                        
                        # ✅ Ensure logs folder exists
                        os.makedirs("logs", exist_ok=True)

                        # ✅ Write to history.txt
                        try:
                            with open("history.txt", "a", encoding="utf-8") as f:
                                f.write(
                                    f"User: {st.session_state.last_user_input}\n"
                                    f"Bot: {message}\n"
                                    f"Approved: False\n\n"
                                )
                        except Exception as e:
                            st.error(f"⚠️ Failed to log rejection: {e}")

        if (
           st.session_state.get("show_feedback", False)
           and st.session_state.get("rejected_message") == message
        ):
            feedback = st.text_area("✍️ Suggest correction or rephrase your query:", key=message + "_feedback_area")

            if st.button("Submit Correction", key=message + "_submit_correction"):
                if feedback:
                    corrected_response = invoke_multiagent(feedback)
                    st.session_state.chat_history.append(("user", feedback))
                    st.session_state.chat_history.append(("bot", corrected_response))
                    with open("history.txt", "a", encoding="utf-8") as f:
                        f.write(f"User: {feedback}\nBot: {corrected_response}\nApproved: Edited\n\n")
                    st.session_state.feedback = ""
                    st.session_state.show_feedback = False
    else:
        while True:
            user_input = input("You: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                break
            response = invoke_multiagent(user_input)
            print("🤖 Bot:", response)
