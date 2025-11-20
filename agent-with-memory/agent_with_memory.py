import re
import streamlit as st
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent


def clean_text(text: str):
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned_text.strip()

st.title("Agent with Memory")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "¿En qué puedo ayudarte?"}]

if "memory" not in st.session_state:
    memory = MemorySaver()
    st.session_state.memory = memory

for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

model = ChatOllama(model="qwen3")
chat_agent = create_react_agent(
    model=model,
    tools=[],
    name="chat_agent",
    checkpointer=st.session_state.memory
)

question = st.chat_input()

if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    st.chat_message("user").write(question)

    result = chat_agent.invoke(
        {
            "messages":  [
                {
                    "role": "user",
                    "content": question
                }
            ]
        },
        config={"configurable": {"thread_id": "1"}}
    )

    # if question:
    #     st.session_state["messages"].append({"role": "user", "content": question})
    #     st.chat_message("user").write(question)

    #     # Generar un thread_id único por sesión de Streamlit si no existe
    #     if "thread_id" not in st.session_state:
    #         import uuid
    #         st.session_state.thread_id = str(uuid.uuid4())

    #     # Convertir el historial completo al formato esperado por el agente
    #     messages_for_agent = []
    #     for msg in st.session_state["messages"]:
    #         messages_for_agent.append({
    #             "role": msg["role"],
    #             "content": msg["content"]
    #         })

    #     result = chat_agent.invoke(
    #         {
    #             "messages": messages_for_agent
    #         },
    #         config={"configurable": {"thread_id": st.session_state.thread_id}}
    #     )

    response = clean_text(result["messages"][-1].content)

    st.session_state["messages"].append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
