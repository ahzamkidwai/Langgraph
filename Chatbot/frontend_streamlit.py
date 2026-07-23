import streamlit as st
from backend_langgraph import workflow
from langchain_core.messages import HumanMessage

CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

message_history = st.session_state['message_history']

# Loading the conversation history
for message in message_history:
    with st.chat_message(message['role']):
        st.text(message['content'])
    
user_input = st.chat_input('Type your query here')

if user_input:
    
    message_history.append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
        
        
    # response = workflow.invoke({ 'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    # ai_message = response['messages'][-1].content
    # message_history.append({'role': 'assistant', 'content': ai_message})
    # with st.chat_message('assistant'):
    #         st.text(ai_message)
    
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in workflow.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config={'configurable': {'thread_id': 'thread-1'}},
                stream_mode='messages'
            )
        )
    
    message_history.append({'role': 'assistant', 'content': ai_message})