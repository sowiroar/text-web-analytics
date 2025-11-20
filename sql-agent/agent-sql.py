import os
import re
import sqlite3
from typing import Literal
import streamlit as st
import requests
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode


def clean_text(text: str):
    """Clean text removing thinking tags"""
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned_text.strip()


def download_chinook_db():
    """Download the Chinook database if it doesn't exist"""
    db_path = "Chinook.db"
    
    if not os.path.exists(db_path):
        with st.spinner("Descargando base de datos Chinook..."):
            url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(db_path, "wb") as file:
                        file.write(response.content)
                    st.success("Base de datos descargada exitosamente")
                    return True
                else:
                    st.error(f"Error al descargar la base de datos. Código: {response.status_code}")
                    return False
            except Exception as e:
                st.error(f"Error al descargar la base de datos: {str(e)}")
                return False
    return True


def setup_database():
    """Setup database connection and tools"""
    if not download_chinook_db():
        return None, None
    
    try:
        db = SQLDatabase.from_uri("sqlite:///Chinook.db")
        return db, True
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {str(e)}")
        return None, False


def setup_tools(db, llm):
    """Setup SQL tools"""
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
    
    get_schema_node = ToolNode([get_schema_tool], name="get_schema")
    run_query_node = ToolNode([run_query_tool], name="run_query")
    
    return tools, get_schema_tool, run_query_tool, get_schema_node, run_query_node


def list_tables(state: MessagesState, tools):
    """List all available tables in the database"""
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "lists",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Tablas disponibles: {tool_message.content}")

    return {"messages": [tool_call_message, tool_message, response]}


def call_get_schema(state: MessagesState, llm, get_schema_tool):
    """Force the model to get table schemas"""
    llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def generate_query(state: MessagesState, llm, db, run_query_tool):
    """Generate SQL query based on the question"""
    system_prompt = f"""
    Eres un agente diseñado para interactuar con una base de datos SQL.
    Dada una pregunta de entrada, crea una consulta {db.dialect} sintácticamente correcta para ejecutar,
    luego mira los resultados de la consulta y devuelve la respuesta. A menos que el usuario
    especifique un número específico de ejemplos que desea obtener, siempre limita tu
    consulta a un máximo de 5 resultados.

    Puedes ordenar los resultados por una columna relevante para devolver los ejemplos más interesantes
    en la base de datos. Nunca consultes todas las columnas de una tabla específica,
    solo solicita las columnas relevantes dada la pregunta.

    NO hagas ninguna declaración DML (INSERT, UPDATE, DELETE, DROP etc.) en la base de datos.
    """
    
    system_message = {
        "role": "system",
        "content": system_prompt,
    }
    
    llm_with_tools = llm.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])
    
    return {"messages": [response]}


def check_query(state: MessagesState, llm, db, run_query_tool):
    """Check the generated query for common mistakes"""
    system_prompt = f"""
    Eres un experto en SQL con gran atención al detalle.
    Verifica la consulta {db.dialect} en busca de errores comunes, incluyendo:
    - Usar NOT IN con valores NULL
    - Usar UNION cuando debería haberse usado UNION ALL
    - Usar BETWEEN para rangos exclusivos
    - Discrepancia de tipos de datos en predicados
    - Citar correctamente los identificadores
    - Usar el número correcto de argumentos para funciones
    - Convertir al tipo de datos correcto
    - Usar las columnas apropiadas para joins

    Si hay alguno de los errores anteriores, reescribe la consulta. Si no hay errores,
    simplemente reproduce la consulta original.

    Llamarás la herramienta apropiada para ejecutar la consulta después de ejecutar esta verificación.
    """
    
    system_message = {
        "role": "system",
        "content": system_prompt,
    }

    # Generate an artificial user message to check
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id

    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal[END, "check_query"]:
    """Decide whether to continue or end the conversation"""
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "check_query"


def build_agent(llm, db):
    """Build the LangGraph agent"""
    tools, get_schema_tool, run_query_tool, get_schema_node, run_query_node = setup_tools(db, llm)
    
    builder = StateGraph(MessagesState)
    
    # Add nodes with partial functions
    builder.add_node("list_tables", lambda state: list_tables(state, tools))
    builder.add_node("call_get_schema", lambda state: call_get_schema(state, llm, get_schema_tool))
    builder.add_node("get_schema", get_schema_node)
    builder.add_node("generate_query", lambda state: generate_query(state, llm, db, run_query_tool))
    builder.add_node("check_query", lambda state: check_query(state, llm, db, run_query_tool))
    builder.add_node("run_query", run_query_node)

    # Add edges
    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")
    builder.add_conditional_edges(
        "generate_query",
        should_continue,
    )
    builder.add_edge("check_query", "run_query")
    builder.add_edge("run_query", "generate_query")

    return builder.compile()


def stream_response(agent, question):
    """Stream the agent's response"""
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        yield step["messages"][-1]

st.set_page_config(
    page_title="Agente SQL con LangGraph", 
    page_icon="🗃️",
    layout="wide"
)

st.title("Agente SQL con LangGraph y Ollama")
st.markdown("### Haz preguntas sobre la base de datos Chinook en lenguaje natural")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuración")
    
    # Model selection
    model_name = st.selectbox(
        "Selecciona el modelo Ollama:",
        ["qwen3", "deepseek-r1:7b"],
        index=0
    )
    
    # Database info
    st.subheader("Base de Datos")
    if st.button("Recargar Base de Datos"):
        if "db" in st.session_state:
            del st.session_state["db"]
        if "agent" in st.session_state:
            del st.session_state["agent"]

# Initialize database and model
if "db" not in st.session_state:
    db, success = setup_database()
    if success:
        st.session_state["db"] = db
        with st.sidebar:
            st.success("Base de datos conectada")
            st.write(f"**Dialecto:** {db.dialect}")
            st.write(f"**Tablas disponibles:** {len(db.get_usable_table_names())}")
            with st.expander("Ver tablas"):
                for table in db.get_usable_table_names():
                    st.write(f"• {table}")
    else:
        st.error("Error al conectar con la base de datos")
        st.stop()

# Initialize model and agent
if "agent" not in st.session_state:
    try:
        llm = ChatOllama(model=model_name, temperature=0)
        st.session_state["agent"] = build_agent(llm, st.session_state["db"])
        st.success(f"Agente SQL inicializado con modelo {model_name}")
    except Exception as e:
        st.error(f"Error al inicializar el modelo: {str(e)}")
        st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hola, soy tu agente SQL. Puedes hacerme preguntas sobre la base de datos Chinook como:\n\n• ¿Qué género tiene las canciones más largas en promedio?\n• ¿Cuáles son los 5 artistas con más ventas?\n• ¿Qué país tiene más clientes?"}
    ]

# Display chat history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if question := st.chat_input("Haz una pregunta sobre la base de datos..."):
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    
    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            with st.spinner("Analizando pregunta y generando consulta SQL..."):
                # Stream the agent's response
                for message in stream_response(st.session_state["agent"], question):
                    if hasattr(message, 'content') and message.content:
                        content = clean_text(message.content)
                        if content and content not in full_response:
                            full_response = content
                            message_placeholder.write(full_response)
            
            if not full_response:
                full_response = "No pude generar una respuesta. Por favor, intenta reformular tu pregunta."
                message_placeholder.write(full_response)
            
        except Exception as e:
            error_msg = f"Error al procesar la pregunta: {str(e)}"
            st.error(error_msg)
            full_response = "Ocurrió un error al procesar tu pregunta. Por favor, intenta de nuevo."
            message_placeholder.write(full_response)
    
    # Add assistant message to history
    st.session_state["messages"].append({"role": "assistant", "content": full_response})