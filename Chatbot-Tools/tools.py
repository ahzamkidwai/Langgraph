# -*- coding: utf-8 -*-
"""Corrected LangGraph chatbot with tools"""

# Install required packages (if not already installed)
# !pip install langchain langgraph langchain_core langchain_google_genai langchain_groq dotenv langchain_community ddgs

import os
import requests
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq

# Load environment variables (for Groq API key and Alpha Vantage key)
load_dotenv()

# In Colab, you can use userdata; for local, use env vars.
try:
    from google.colab import userdata
    groq_api_key = userdata.get("GROQ_API_KEY")
except ImportError:
    groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
)

# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------

# DuckDuckGo search tool
search_tool = DuckDuckGoSearchRun(region='us-en')

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div.
    Returns a dict with 'result' or 'error'.
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Cannot divide by zero"}
            result = first_num / second_num
        else:
            return {"error": f"Invalid operation '{operation}'. Supported: add, sub, mul, div"}
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch the latest stock price for a given symbol (e.g., 'AAPL', 'GOOGL').
    Uses Alpha Vantage API.
    """
    # Get API key from environment; fallback to a demo key (but replace with your own)
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "UZ0JWRB1M6FI46UB")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Check if the response contains the expected data
        if "Global Quote" in data and data["Global Quote"]:
            price = data["Global Quote"].get("05. price", "N/A")
            return {"symbol": symbol.upper(), "price": price}
        else:
            # Possibly an error message from Alpha Vantage
            return {"error": data.get("Note", "No data found for symbol")}
    except Exception as e:
        return {"error": str(e)}

# List of tools
tools = [get_stock_price, search_tool, calculator]

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# ----------------------------------------------------------------------
# State and Graph
# ----------------------------------------------------------------------

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """LLM node that may respond directly or request a tool call."""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Tool node (prebuilt)
tool_node = ToolNode(tools)

# Build the graph
graph = StateGraph(ChatState)

# Add nodes
graph.add_node("chat_mode", chat_node)
graph.add_node("tools", tool_node)

# Edges
graph.add_edge(START, "chat_mode")

# Conditional edge: if tools are called, go to "tools"; otherwise END
graph.add_conditional_edges("chat_mode", tools_condition)

# After tools are executed, go back to chat_mode to let LLM process results
graph.add_edge("tools", "chat_mode")

# Compile the graph
chatbot = graph.compile()

# ----------------------------------------------------------------------
# Test the chatbot
# ----------------------------------------------------------------------

def run_chat(message: str):
    """Helper to invoke the chatbot and print the final answer."""
    result = chatbot.invoke({"messages": [HumanMessage(content=message)]})
    # The last message should be the LLM's final answer (after tools if any)
    last_msg = result['messages'][-1]
    if hasattr(last_msg, 'content'):
        print(f"User: {message}")
        print(f"Assistant: {last_msg.content}\n")
    else:
        print(f"User: {message}")
        print("Assistant: (No text response, maybe tool call was not processed?)\n")

# Example invocations
run_chat("Hello!")
run_chat("What is 5 multiplied by 8?")
run_chat("What is the stock price of AAPL?")