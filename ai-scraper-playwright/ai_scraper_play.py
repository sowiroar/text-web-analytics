import streamlit as st
import os
import sys
import asyncio
from playwright.sync_api import sync_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Configurar event loop para Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Cargar variables de entorno
try:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except:
    load_dotenv()

def initialize_agent(model_name="gemini-2.5-flash"):
    """Inicializa el agente de navegación con Playwright"""
    try:
        # Crear navegador sincrónico usando subprocess
        # Esto funciona en Windows con ProactorEventLoopPolicy
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        # Crear una página por defecto
        page = browser.new_page()
        
        # Crear toolkit con el navegador sincrónico
        toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=browser, async_browser=None)
        tools = toolkit.get_tools()
        
        # Obtener el prompt del hub
        prompt = hub.pull("hwchase17/openai-tools-agent")
        
        # Inicializar el modelo LLM
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        
        # Crear el agente
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        # Crear el ejecutor del agente
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
        
        return agent_executor, browser, playwright, page
    except Exception as e:
        st.error(f"Error al inicializar el agente: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None, None

def execute_command(agent_executor, command):
    """Ejecuta un comando en el agente"""
    try:
        result = agent_executor.invoke({"input": command})
        return result.get("output", "No se obtuvo respuesta")
    except Exception as e:
        return f"Error al ejecutar el comando: {str(e)}"

# Configuración de la página
st.set_page_config(
    page_title="AI Scraper con Playwright",
    page_icon="⚡",
    layout="wide"
)

st.title("AI Scraper con Playwright")
st.markdown("### Automatiza la navegación web usando inteligencia artificial")

# Sidebar con configuración
with st.sidebar:
    st.header("Configuración")
    
    # Selección de modelo
    model_name = st.selectbox(
        "Selecciona el modelo:",
        ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-preview"],
        index=0
    )
    
    st.divider()
    
    # Información sobre herramientas disponibles
    st.subheader("Herramientas Disponibles")
    with st.expander("Ver herramientas de Playwright"):
        st.markdown("""
        - **navigate_browser**: Navega a una URL
        - **previous_page**: Vuelve a la página anterior
        - **click_element**: Hace clic en un elemento (CSS selector)
        - **extract_text**: Extrae texto de la página actual
        - **extract_hyperlinks**: Extrae enlaces de la página
        - **get_elements**: Selecciona elementos por CSS selector
        - **current_page**: Obtiene la URL actual
        """)
    
    st.divider()
    
    # Ejemplos de comandos
    st.subheader("Ejemplos de Comandos")
    with st.expander("Ver ejemplos"):
        st.markdown("""
        **Navegación básica:**
        - Ve a google.com y busca "inteligencia artificial"
        - Navega a wikipedia.org y busca información sobre Python
        
        **Extracción de datos:**
        - Ve a [URL] y extrae todos los títulos
        - Abre [URL] y dame un resumen de la página
        - Navega a [URL] y extrae todos los enlaces
        
        **Interacción:**
        - Ve a [URL] y haz clic en el botón de login
        - Abre [URL] y llena el formulario de contacto
        """)
    
    st.divider()
    
    # Botón para limpiar caché
    if st.button("Reiniciar Navegador"):
        if "page" in st.session_state and st.session_state["page"]:
            try:
                st.session_state["page"].close()
            except:
                pass
        if "browser" in st.session_state and st.session_state["browser"]:
            try:
                st.session_state["browser"].close()
            except:
                pass
        if "playwright" in st.session_state and st.session_state["playwright"]:
            try:
                st.session_state["playwright"].stop()
            except:
                pass
        if "agent_executor" in st.session_state:
            del st.session_state["agent_executor"]
        if "browser" in st.session_state:
            del st.session_state["browser"]
        if "playwright" in st.session_state:
            del st.session_state["playwright"]
        if "page" in st.session_state:
            del st.session_state["page"]
        st.rerun()

# Inicializar el agente si no existe
if "agent_executor" not in st.session_state:
    with st.spinner("Inicializando agente de navegación..."):
        agent_executor, browser, playwright, page = initialize_agent(model_name)
        if agent_executor:
            st.session_state["agent_executor"] = agent_executor
            st.session_state["browser"] = browser
            st.session_state["playwright"] = playwright
            st.session_state["page"] = page
            st.success("Agente inicializado correctamente")
        else:
            st.error("Error al inicializar el agente")
            st.stop()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": """Hola! Soy tu asistente de automatización web con Playwright.

Puedo ayudarte a:
- Navegar por sitios web
- Extraer información de páginas
- Obtener enlaces y elementos
- Interactuar con elementos de la página
- Resumir contenido web

¿Qué te gustaría que hiciera?"""
        }
    ]

# Mostrar historial de chat
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu comando aquí... (ej: 'Ve a google.com y busca Python')"):
    # Agregar mensaje del usuario
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generar respuesta del agente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("Procesando comando..."):
            try:
                response = execute_command(st.session_state["agent_executor"], prompt)
                message_placeholder.markdown(response)
                
                # Agregar respuesta al historial
                st.session_state["messages"].append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                error_msg = f"Error al procesar el comando: {str(e)}"
                message_placeholder.markdown(error_msg)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": error_msg}
                )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <b>Tip:</b> Sé específico en tus comandos para obtener mejores resultados
</div>
""", unsafe_allow_html=True)
