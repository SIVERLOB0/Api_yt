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

print("🐺 WOLF API (TIKTOK FIX): ONLINE...")

def limpiar_basura():
    while True:
        try:
            now = time.time()
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                if os.stat(f).st_mtime < now - 600: 
                    os.remove(f)
        except Exception:
            pass
        time.sleep(600)

threading.Thread(target=limpiar_basura, daemon=True).start()

@app.route('/')
def home():
    return "🐺 WOLF API: ONLINE"

@app.route('/process', methods=['GET'])
def process_media():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video')
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"📥 Procesando: {url}")
    file_id = str(uuid.uuid4())
    
    # AJUSTE PARA TIKTOK: User Agent de Android genérico suele funcionar mejor
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Usamos un User Agent más genérico de Android
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    }

    # LÓGICA DE FORMATOS SIMPLIFICADA
    if tipo == 'video':
        # "best" a secas es más seguro para TikTok. 
        # Si pides "best[ext=mp4]" a veces falla si TikTok sirve .mov o .webm
        ydl_opts['format'] = 'best'
    else:
        # Audio
        ydl_opts['format'] = 'bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            titulo = info.get('title', 'Wolf Media')
            duracion = info.get('duration_string', '0:00')
            imagen = info.get('thumbnail', '')
            ext_final = info.get('ext', 'mp4') # Detectar extensión real

            # Buscamos el archivo exacto creado
            patron = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.*")
            archivos = glob.glob(patron)
            
            if not archivos:
                raise Exception("Archivo no encontrado en disco tras descarga")
            
            nombre_real = os.path.basename(archivos[0])
            mi_link = f"{request.host_url}file/{nombre_real}"

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "duracion": duracion,
                    "imagen": imagen,
                    "descarga": mi_link,
                    "formato": ext_final
                }
            })

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR CRÍTICO: {error_msg}")
        
        # AHORA LA API TE DIRÁ EXACTAMENTE QUÉ PASÓ
        return jsonify({
            "status": False, 
            "error": error_msg, # <--- Aquí veremos el error real
            "code": 500
        }), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        else:
            return "Archivo expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
