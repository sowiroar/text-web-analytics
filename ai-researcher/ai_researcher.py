import re
import streamlit as st
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from typing_extensions import TypedDict
from dotenv import load_dotenv
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles


load_dotenv()
# Prompt para resumir cada resultado de búsqueda
summary_template = """
Resume el siguiente contenido en un párrafo conciso que responda directamente a la consulta. 
Asegúrate de resaltar los puntos clave relevantes manteniendo claridad y completitud.

Consulta: {query}
Contenido: {content}
"""

# Prompt para generar la respuesta final basada en los resúmenes
generate_response_template = """    
Dada la siguiente consulta del usuario y el contexto proporcionado, genera una respuesta que responda 
directamente a la pregunta usando información relevante del contexto. 
Asegúrate de que la respuesta sea clara, concisa y bien estructurada. 
Además, proporciona un breve resumen de los puntos clave de la respuesta.

Pregunta: {question} 
Contexto: {context} 
Respuesta:
"""

# Estado del grafo: contiene todos los datos que fluyen entre nodos
class ResearchState(TypedDict):
    query: str  # Consulta del usuario
    sources: list[str]  # URLs de las fuentes
    web_results: list[str]  # Contenido crudo de las búsquedas
    summarized_results: list[str]  # Resúmenes de cada resultado
    response: str  # Respuesta final generada

# Estado de entrada: solo necesita la consulta
class ResearchStateInput(TypedDict):
    query: str

# Estado de salida: retorna fuentes y respuesta final
class ResearchStateOutput(TypedDict):
    sources: list[str]
    response: str

# NODO 1: Buscar en la web usando Tavily
def search_web(state: ResearchState):
    """
    Busca información en la web usando Tavily API.
    Retorna las URLs (sources) y el contenido crudo (web_results).
    """
    search = TavilySearchResults(max_results=3)
    search_results = search.invoke(state["query"])

    return  {
        "sources": [result['url'] for result in search_results],
        "web_results": [result['content'] for result in search_results]
    }

# NODO 2: Resumir cada resultado individualmente
def summarize_results(state: ResearchState):
    """
    Toma cada resultado de búsqueda y genera un resumen usando el LLM.
    Limpia el texto para remover tags de pensamiento (<think>).
    """
    model = ChatOllama(model="gpt-oss:120b-cloud")
    prompt = ChatPromptTemplate.from_template(summary_template)
    chain = prompt | model

    summarized_results = []
    for content in state["web_results"]:
        summary = chain.invoke({"query": state["query"], "content": content})
        clean_content = clean_text(summary.content)
        summarized_results.append(clean_content)

    return {
        "summarized_results": summarized_results
    }

# NODO 3: Generar respuesta final basada en los resúmenes
def generate_response(state: ResearchState):
    """
    Combina todos los resúmenes y genera una respuesta coherente
    que responde directamente a la consulta del usuario.
    """
    model = ChatOllama(model="gpt-oss:120b-cloud")
    prompt = ChatPromptTemplate.from_template(generate_response_template)
    chain = prompt | model

    # Unir todos los resúmenes en un solo contexto
    content = "\n\n".join([summary for summary in state["summarized_results"]])

    return {
        "response": chain.invoke({"question": state["query"], "context": content})
    }

# Función auxiliar para limpiar texto de modelos razonadores
def clean_text(text: str):
    """
    Remueve los tags <think>...</think> que usan modelos como DeepSeek-R1
    para mostrar su proceso de razonamiento interno.
    """
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned_text.strip()

# Construir el grafo de flujo de trabajo con LangGraph
builder = StateGraph(
    ResearchState,  # Estado que fluye entre nodos
    input=ResearchStateInput,  # Solo recibe la consulta
    output=ResearchStateOutput  # Solo retorna fuentes y respuesta
)

# Agregar los 3 nodos del proceso
builder.add_node("search_web", search_web)  # 1. Buscar en web
builder.add_node("summarize_results", summarize_results)  # 2. Resumir resultados
builder.add_node("generate_response", generate_response)  # 3. Generar respuesta final

# Definir el flujo: START -> búsqueda -> resumen -> respuesta -> END
builder.add_edge(START, "search_web")
builder.add_edge("search_web", "summarize_results")
builder.add_edge("summarize_results", "generate_response")
builder.add_edge("generate_response", END)

# Compilar el grafo para ejecutarlo
graph = builder.compile()
#Guardar el grafico del grafo 
graph_png_data = graph.get_graph().draw_mermaid_png(
    output_file_path="my_graph.png"
)
# Interfaz de Streamlit
st.title("🔍 AI Researcher")
st.markdown("Realiza investigaciones web usando IA para buscar, resumir y responder")

query = st.text_input("Ingresa tu consulta de investigación:")

if query:
    with st.spinner("🔎 Buscando información en la web..."):
        # Ejecutar todo el grafo con la consulta
        response_state = graph.invoke({"query": query})
    
    # Mostrar respuesta final (sin tags de pensamiento)
    st.markdown("### 📝 Respuesta:")
    st.write(clean_text(response_state["response"].content))

    # Mostrar fuentes consultadas
    st.markdown("### 📚 Fuentes:")
    for i, source in enumerate(response_state["sources"], 1):
        st.write(f"{i}. {source}")