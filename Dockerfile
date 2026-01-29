# Usamos una imagen oficial de Python (Liviana y segura)
FROM python:3.10-slim

# 1. Instalamos FFmpeg y herramientas del sistema
# Esto garantiza que yt-dlp pueda unir video y audio
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# 2. Preparamos la carpeta de trabajo
WORKDIR /app

# 3. Copiamos los requisitos e instalamos las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el resto del código
COPY . .

# 5. Comando de arranque (Detecta el puerto de Railway automáticamente)
CMD gunicorn server:app --bind 0.0.0.0:$PORT
