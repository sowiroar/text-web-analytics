import streamlit as st
import re 
from langchain_community.tools.tavily_search import TavilySearchResults
from lanchain_ollama import ChatOllama
from laggranph.graph import START, END, StateGraph
from typing_extensions import TypedDict
from dotenv import load_dotenv

load_dotenv()

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

