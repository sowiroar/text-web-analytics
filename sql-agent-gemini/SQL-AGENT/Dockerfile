# Usa una imagen base oficial de Python 3.12
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para sqlite3
# sqlite3 viene preinstalado en python:3.12-slim, pero instalamos librerías adicionales
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requirements al contenedor
COPY requirements.txt .

# Instala las dependencias de Python
# --no-cache-dir reduce el tamaño de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de la aplicación al contenedor
COPY . .

# Expone el puerto 8501 (puerto por defecto de Streamlit)
EXPOSE 8501

# Comando para ejecutar la aplicación Streamlit
# --server.port=8501: Puerto en el que se ejecutará la app
# --server.address=0.0.0.0: Permite conexiones desde cualquier IP (necesario para Docker)
# --server.headless=true: Ejecuta sin abrir el navegador automáticamente
CMD ["streamlit", "run", "agent-sql.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
