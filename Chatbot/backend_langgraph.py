from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
print("Grok API Key : ", groq_api_key)

class ChatState(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]
  
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
)

def chat_node(state: ChatState) -> ChatState: 
  messages = state['messages']
  response = llm.invoke(messages)
  return {'messages': [response]}


checkpointer = MemorySaver()
graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer=checkpointer)
