"""
AI Scraper con Playwright - Chatbot Simple
"""

import os
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_sync_playwright_browser
from langchain.agents import AgentExecutor
from langchain_ollama import ChatOllama
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

print("Inicializando agente...")
# load_dotenv()

# Crear navegador con Playwright
sync_browser = create_sync_playwright_browser()
toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
tools = toolkit.get_tools()

prompt = ChatPromptTemplate.from_messages([
    ("system", """Eres un asistente útil que puede navegar por la web y extraer información.
    Tienes acceso a herramientas de Playwright para interactuar con páginas web.

    Cuando te pidan navegar o extraer información:
    1. Usa navigate_browser para ir a URLs
    2. Usa extract_text para obtener contenido de páginas
    3. Usa extract_hyperlinks para obtener enlaces
    4. Usa click_element si necesitas hacer clic en algo
    5. Responde de manera clara y concisa

    Sé específico y detallado en tus respuestas."""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
# Inicializar modelo Ollama con Mistral
llm = ChatOllama(model="gpt-oss:120b-cloud", temperature=0)

# Crear agente
agent = create_openai_tools_agent(llm, tools, prompt)

# Crear ejecutor del agente
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Agente listo!\n")

# Loop de chat
print("Escribe 'salir' para terminar\n")

while True:
    user_input = input("Tu: ").strip()
    
    if not user_input:
        continue
    
    if user_input.lower() in ['salir', 'exit', 'quit']:
        print("\nCerrando...")
        break
    
    print()
    result = agent_executor.invoke({"input": user_input})
    print(f"\nAgente: {result['output']}\n")
