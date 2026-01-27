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

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF API (YOUTUBE FIX): ONLINE...")

# --- LIMPIEZA AUTOMÁTICA ---
def limpiar_basura():
    while True:
        try:
            now = time.time()
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                if os.stat(f).st_mtime < now - 600: # 10 minutos
                    os.remove(f)
                    print(f"🗑️ Limpiando: {f}")
        except Exception as e:
            print(f"Error limpieza: {e}")
        time.sleep(600)

threading.Thread(target=limpiar_basura, daemon=True).start()

@app.route('/')
def home():
    return "🐺 WOLF API: YT ENGINE READY."

@app.route('/process', methods=['GET'])
def process_media():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video')
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"📥 Wolf procesando: {url}")

    file_id = str(uuid.uuid4())
    # Si es video, forzamos contenedor mp4. Si es audio, mp3.
    ext = 'mp4' if tipo == 'video' else 'mp3'
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename) # yt-dlp añade extensión a veces, ojo con esto

    # Configuración Avanzada para YouTube
    ydl_opts = {
        # NOMBRE DEL ARCHIVO
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s"),
        
        # OPCIONES DE CALIDAD Y FFMPEG
        # Si es video: Descarga lo mejor que sea mp4, o une video+audio y conviértelo a mp4
        # Si es audio: Descarga el mejor audio y conviértelo a mp3
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if tipo == 'video' else 'bestaudio/best',
        
        # SI ES AUDIO, convertir a MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if tipo == 'audio' else [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],

        # EVASIÓN DE BLOQUEOS
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Usamos un User Agent de iPhone para parecer un celular real
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            titulo = info.get('title', 'Wolf Media')
            duracion = info.get('duration_string', '0:00')
            imagen = info.get('thumbnail', '')
            
            # yt-dlp puede cambiar la extensión final (ej: .mkv -> .mp4)
            # Buscamos el archivo real que se creó con ese ID
            patron = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*")
            archivos_encontrados = glob.glob(patron)
            
            if not archivos_encontrados:
                raise Exception("El archivo no aparece tras la descarga.")
            
            # Tomamos el nombre real del archivo generado
            nombre_final = os.path.basename(archivos_encontrados[0])

            mi_link = f"{request.host_url}file/{nombre_final}"

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "duracion": duracion,
                    "imagen": imagen,
                    "descarga": mi_link
                }
            })

    except Exception as e:
        print(f"❌ Error Wolf: {str(e)}")
        # YouTube a veces da error 403 o 'Sign in'. 
        return jsonify({"status": False, "error": "Error de YouTube o Bloqueo de IP"}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path)
        else:
            return "Archivo expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
