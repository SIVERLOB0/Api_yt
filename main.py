import os
import uuid
import time
import threading
import glob
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Carpeta temporal para guardar los videos
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF API (STORAGE MODE): ONLINE...")

# --- SISTEMA DE AUTO-LIMPIEZA (Borra archivos de más de 10 min) ---
def limpiar_basura():
    while True:
        try:
            now = time.time()
            # Busca todos los archivos en la carpeta downloads
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                # Si el archivo tiene más de 600 segundos (10 min)
                if os.stat(f).st_mtime < now - 600:
                    os.remove(f)
                    print(f"🗑️ Archivo borrado por vejez: {f}")
        except Exception as e:
            print(f"Error en limpieza: {e}")
        time.sleep(600) # Revisa cada 10 minutos

# Iniciamos el basurero en segundo plano
threading.Thread(target=limpiar_basura, daemon=True).start()


@app.route('/')
def home():
    return "🐺 WOLF API: STORAGE SERVER READY."

# --- ENDPOINT 1: PROCESAR Y GUARDAR ---
@app.route('/process', methods=['GET'])
def process_media():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video') # 'video' o 'audio'
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"📥 Descargando localmente: {url}")

    # Nombre de archivo único para evitar conflictos
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp4" if tipo == 'video' else f"{file_id}.mp3"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    # Configuración yt-dlp para guardar en disco
    ydl_opts = {
        'outtmpl': filepath, # Guardar en nuestra carpeta
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if tipo == 'audio' else 'best[ext=mp4]/best',
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True) # download=True para guardar
            
            # Datos visuales
            titulo = info.get('title', 'Wolf Media')
            duracion = info.get('duration_string', '0:00')
            imagen = info.get('thumbnail', '')

            # Construimos TU link propio
            # request.host_url es "https://tu-api.railway.app/"
            mi_link_seguro = f"{request.host_url}file/{filename}"

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "duracion": duracion,
                    "imagen": imagen,
                    "descarga": mi_link_seguro # <--- ESTE ES EL LINK ORO
                }
            })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500


# --- ENDPOINT 2: ENTREGAR EL ARCHIVO ---
@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path)
        else:
            return "Archivo expirado o no existe", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
