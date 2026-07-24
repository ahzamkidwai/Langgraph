from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
import sqlite3

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

connection = sqlite3.connect(database='chatbot_db.sqlite', check_same_thread=False)

checkpointer = SqliteSaver(conn=connection)
graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

workflow = graph.compile(checkpointer=checkpointer)

print("Before Loop\n\n")

def retrieve_all_threads():
  all_set = set()

  for checkpoint in checkpointer.list(None):
    # print(checkpoint.config['configurable']['thread_id'])
    all_set.add(checkpoint.config['configurable']['thread_id'])

  print("List of All Threads : \n", list(all_set))
  return list(all_set)