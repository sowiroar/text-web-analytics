import os #Libreria para acceder a archivos y comandos del sistema
from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_sync_playwright_browser
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

sync_browser = create_sync_playwright_browser()
toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
tools = toolkit.get_tools()

load_dotenv()
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

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
# llm = ChatOllama(model="gpt-oss:120b-cloud")

agent = create_openai_tools_agent(llm, tools, prompt) #el agente es basado en cadena, lineal

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) #Si uso verbose False no muestro el procedimiento

while True:
    user_input = input("User: ").strip()
    if not user_input:
        continue

    if user_input.lower() in ['salir','exit','quitar']:
        break
    
    result = agent_executor.invoke({"input": user_input})
    print(f"\nAgente: {result['output']}\n")