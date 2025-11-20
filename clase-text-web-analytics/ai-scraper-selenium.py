import streamlit as st
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

system = """
Eres un asistente para tareas de preguntas y respuestas. Usa los siguientes fragmentos de contexto recuperado para responder la pregunta. Si no sabes la respuesta, 
simplemente di que no lo sabes. Usa máximo tres oraciones y mantén la respuesta concisa.
Pregunta: {question} 
Contexto: {context} 
Respuesta:
"""
#Vectoriza el texto con el modelo de GPT
embeddings = OllamaEmbeddings(model="mistral")
#Guarda los vectores en memoria
vector_store = InMemoryVectorStore(embeddings)

llm = OllamaLLM(model="mistral")

#Herramienta para cargar páginas web con Selenium
# y retorna la informacion en una variable
def load_page(url):
    loader = SeleniumURLLoader(
        urls=[url]
    )
    documents = loader.load()
    return documents

#Divido el texto en fragmentos mas pequeños
#Para facilitar vectorizacion y búsqueda
def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap = 200,
        add_start_index = True
    )
    data = text_splitter.split_documents(documents)
    return data

#Indexar los documentos en la biblioteca
def index_docs(documents):
    vector_store.add_documents(documents)

#Recuperar documentos similares a la consulta
def retrieve_docs(query):
    return vector_store.similarity_search(query)

#Generar respuesta en base a la pregunta

def answer_question(question,context):
    prompt = ChatPromptTemplate.from_template(system)
    chain = prompt | llm
    return chain.invoke({"question": question, "context": context} )

#Configuro streamlit
st.title("AI Crawler con GPT-OSS")
url = st.text_input("Enter URL:")

documents = load_page(url)
chunked_documents = split_text(documents)

index_docs(chunked_documents)

question = st.chat_input()
if question:
    st.chat_message("user").write(question)
    retrieve_documents = retrieve_docs(question)
    context = "\n\n".join([doc.page_content for doc in retrieve_documents])
    answer = answer_question(question, context)
    st.chat_message("assistant").write(answer)