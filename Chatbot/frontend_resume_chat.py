import streamlit as st
from backend_langgraph import workflow
from langchain_core.messages import HumanMessage
import uuid

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = uuid.uuid4()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id=thread_id)
    st.session_state['message_history'] = []
    
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversations(thread_id):
    return workflow.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']

CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
    
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
    
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])

message_history = st.session_state['message_history']
thread_id = st.session_state['thread_id']


st.sidebar.title('Langgraph Chatbot')
if st.sidebar.button('New Chat'):
    reset_chat()
st.sidebar.header('My Conversations')
# st.sidebar.text(thread_id)
for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversations(thread_id)
        
        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': messages.content})

        st.session_state['message_history'] = temp_messages

for message in message_history:
    with st.chat_message(message['role']):
        st.text(message['content'])
    
user_input = st.chat_input('Type your query here')

if user_input:
    
    message_history.append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in workflow.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config={'configurable': {'thread_id': thread_id}},
                stream_mode='messages'
            )
        )
    
    message_history.append({'role': 'assistant', 'content': ai_message})