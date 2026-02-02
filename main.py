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

print("🐺 WOLF API (LITE VERSION): ONLINE...")

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
    return "🐺 WOLF API: LITE MODE READY."

@app.route('/process', methods=['GET'])
def process_media():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video') # 'video' o 'audio'
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"📥 Wolf procesando: {url}")

    file_id = str(uuid.uuid4())
    
    # NOTA: Sin FFmpeg, no podemos forzar MP3. 
    # Usaremos m4a para audio (muy compatible) y mp4 para video.
    
    # Configuración base
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    }

    # LÓGICA SIN FFMPEG
    if tipo == 'video':
        # best[ext=mp4]: Busca el mejor archivo ÚNICO que sea mp4.
        # usually esto descarga 720p o 360p (tu "calidad 400").
        # has_video+has_audio: Asegura que no baje solo video mudo.
        ydl_opts['format'] = 'best[ext=mp4][has_audio]/best[ext=mp4]/best'
    else:
        # AUDIO: bestaudio[ext=m4a]. M4A es nativo de iPhone/Android.
        # No intentamos convertir a MP3 para no usar CPU.
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            titulo = info.get('title', 'Wolf Media')
            duracion = info.get('duration_string', '0:00')
            imagen = info.get('thumbnail', '')
            
            # Buscamos qué archivo se creó realmente
            patron = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*")
            archivos_encontrados = glob.glob(patron)
            
            if not archivos_encontrados:
                raise Exception("El archivo no aparece tras la descarga.")
            
            nombre_final = os.path.basename(archivos_encontrados[0])
            mi_link = f"{request.host_url}file/{nombre_final}"

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "duracion": duracion,
                    "imagen": imagen,
                    "descarga": mi_link,
                    "nota": "Modo Lite (Sin conversión)"
                }
            })

    except Exception as e:
        print(f"❌ Error Wolf: {str(e)}")
        return jsonify({"status": False, "error": "Error al procesar"}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            # Forzamos la descarga con el nombre correcto para el navegador
            return send_file(path, as_attachment=True)
        else:
            return "Archivo expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
