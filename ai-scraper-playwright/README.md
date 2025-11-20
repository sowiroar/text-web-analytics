# 🌐 AI Scraper con Playwright

Un agente inteligente de automatización web que utiliza LangChain, Playwright y Google Gemini para navegar e interactuar con sitios web usando lenguaje natural.

## ✨ Características

- 🤖 **Agente inteligente**: Usa Google Gemini para interpretar comandos en lenguaje natural
- 🌐 **Automatización web completa**: Navega, hace clic, extrae datos y más
- 📝 **Extracción de contenido**: Extrae texto, enlaces y elementos de páginas web
- 🖱️ **Interacción con páginas**: Hace clic en botones, llena formularios, etc.
- 💬 **Interfaz conversacional**: Interfaz de chat intuitiva con Streamlit
- 🔄 **Historial de conversación**: Mantiene el contexto de tus comandos

## 🛠️ Herramientas Disponibles

El agente tiene acceso a las siguientes herramientas de Playwright:

1. **navigate_browser**: Navega a una URL específica
2. **previous_page**: Vuelve a la página anterior en el historial
3. **click_element**: Hace clic en un elemento usando selectores CSS
4. **extract_text**: Extrae todo el texto visible de la página actual
5. **extract_hyperlinks**: Extrae todos los enlaces de la página
6. **get_elements**: Selecciona elementos específicos por selector CSS
7. **current_page**: Obtiene la URL de la página actual

## 📋 Requisitos Previos

- Python 3.8 o superior
- Google API Key ([Obtener aquí](https://makersuite.google.com/app/apikey))
- Navegadores de Playwright instalados

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
cd ai-scraper-playwright
```

### 2. Crear un entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores de Playwright

```bash
playwright install
```

### 5. Configurar variables de entorno

Crea un archivo `.env` en el directorio del proyecto:

```env
GOOGLE_API_KEY=tu-api-key-aqui
```

## 🎮 Uso

### Ejecutar la aplicación

```bash
streamlit run ai_scraper_play.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### Ejemplos de Comandos

#### Navegación básica
```
Ve a google.com y busca "inteligencia artificial"
Navega a wikipedia.org y busca información sobre Python
Abre github.com y ve al repositorio de langchain
```

#### Extracción de datos
```
Ve a https://python.langchain.com y extrae todos los títulos
Navega a https://news.ycombinator.com y dame los 5 artículos principales
Abre https://example.com y extrae todos los enlaces
```

#### Interacción con páginas
```
Ve a [URL] y haz clic en el botón de login
Navega a [URL] y dame un resumen de la página
Abre [URL] y extrae información de contacto
```

#### Análisis de contenido
```
Ve a [URL] y dame un resumen de los productos disponibles
Navega a [URL] y extrae todos los precios
Abre [URL] y dime cuáles son las secciones principales
```

## 🔧 Configuración Avanzada

### Modelos disponibles

Puedes cambiar el modelo en la barra lateral:

- **gemini-2.0-flash-exp** (predeterminado) - Más rápido y económico
- **gemini-1.5-flash** - Balance entre velocidad y capacidad
- **gemini-1.5-pro** - Mayor capacidad de razonamiento

### Ajustes del agente

En el código, puedes modificar estos parámetros:

```python
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,              # Muestra el proceso de razonamiento
    handle_parsing_errors=True, # Maneja errores de parseo automáticamente
    max_iterations=10          # Máximo de iteraciones del agente
)
```

## 📝 Notas Importantes

### Versiones específicas

Este proyecto usa versiones específicas de LangChain debido a un problema conocido con Pydantic V2:

```
langchain 0.2.16
langchain-community 0.2.17
langchain-core 0.2.41
playwright 1.48.0
pydantic 2.9.2
```

No actualices estas versiones hasta que se resuelva el issue en GitHub.

### Limitaciones

- **Sitios con CAPTCHA**: El agente no puede resolver CAPTCHAs
- **Autenticación**: No maneja login/password automáticamente
- **JavaScript pesado**: Puede tener problemas con SPAs muy complejas
- **Rate limiting**: Respeta los límites de las páginas web

## 🐛 Solución de Problemas

### Error: "No module named 'playwright'"

```bash
pip install playwright
playwright install
```

### Error: "API key not valid"

Verifica que:
1. Tu API key sea correcta
2. La API "Generative Language API" esté habilitada en Google Cloud
3. El archivo `.env` esté en el directorio correcto

### Error: "KeyError: 'data'"

Asegúrate de usar las versiones específicas del `requirements.txt`:

```bash
pip uninstall langchain langchain-community langchain-core
pip install -r requirements.txt
```

### El navegador no se abre

Reinstala los navegadores de Playwright:

```bash
playwright install --force
```

### Timeout errors

Aumenta el tiempo de espera en el código:

```python
sync_browser = create_sync_playwright_browser(
    timeout=30000  # 30 segundos
)
```

## 🔐 Seguridad

- **Nunca compartas tu API key**
- El archivo `.env` está en `.gitignore` por defecto
- Ten cuidado con los sitios que visitas automáticamente
- Respeta los `robots.txt` de los sitios web
- No uses el scraper para actividades maliciosas

## 📚 Recursos Adicionales

- [Documentación de LangChain](https://python.langchain.com/)
- [Playwright Python](https://playwright.dev/python/)
- [Google Gemini API](https://ai.google.dev/)
- [Streamlit Docs](https://docs.streamlit.io/)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## ⚠️ Disclaimer

Esta herramienta está diseñada para propósitos educativos y de investigación. Asegúrate de cumplir con los términos de servicio de los sitios web que automatices y respeta las leyes de privacidad y protección de datos.

## 🙏 Agradecimientos

- [LangChain](https://github.com/langchain-ai/langchain) por el framework de agentes
- [Playwright](https://github.com/microsoft/playwright-python) por las herramientas de automatización
- [Google](https://ai.google.dev/) por Gemini API
- [Streamlit](https://streamlit.io/) por la interfaz de usuario

---

**Desarrollado con ❤️ usando LangChain, Playwright y Google Gemini**
