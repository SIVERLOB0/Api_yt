from flask import Flask, request, jsonify
import yt_dlp
import os
import time
import shutil

app = Flask(__name__)

# Ruta temporal segura para servidores Linux (Railway)
BASE_DIR = "/tmp/descargas_wolf"
os.makedirs(BASE_DIR, exist_ok=True)

def limpiar_basura():
    """Protocolo de limpieza: elimina carpetas con más de 10 minutos de antigüedad"""
    ahora = time.time()
    for nombre_carpeta in os.listdir(BASE_DIR):
        ruta_carpeta = os.path.join(BASE_DIR, nombre_carpeta)
        if os.path.isdir(ruta_carpeta):
            # Si la carpeta tiene más de 600 segundos (10 minutos)
            if os.path.getctime(ruta_carpeta) < ahora - 600:
                try:
                    shutil.rmtree(ruta_carpeta)
                except:
                    pass

def procesar_descarga(link, tipo):
    # Ejecutar limpieza antes de procesar una nueva orden
    limpiar_basura()
    
    if not link:
        return {"status": "error", "mensaje": "Vector vacio. Usa el parametro ?link="}, 400

    # Limpieza del enlace y creación de ruta
    link_base = link.split('?')[0]
    link_limpio = ''.join(e for e in link_base.replace('https://', '').replace('http://', '') if e.isalnum() or e == '_')[:80]
    
    if not link_limpio:
        link_limpio = f"descarga_{int(time.time())}"

    ruta_destino = os.path.join(BASE_DIR, link_limpio)
    os.makedirs(ruta_destino, exist_ok=True)

    # Configuración de yt-dlp modo sigilo
    ydl_opts = {
        'outtmpl': f'{ruta_destino}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    if tipo == 'audio':
        ydl_opts['format'] = 'ba'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
            
        return {
            "status": "success",
            "tipo": tipo,
            "ruta": ruta_destino,
            "mensaje": "Descarga exitosa. El archivo se auto-destruira en 10 minutos."
        }, 200

    except Exception as e:
        # Destruir evidencia si la descarga falla
        if os.path.exists(ruta_destino):
            shutil.rmtree(ruta_destino, ignore_errors=True)
        return {"status": "error", "mensaje": f"Mision abortada. Error: {str(e)}"}, 500

# --- ENDPOINTS ---
@app.route('/api/video', methods=['GET'])
def api_video():
    link = request.args.get('link')
    respuesta, codigo = procesar_descarga(link, 'video')
    return jsonify(respuesta), codigo

@app.route('/api/audio', methods=['GET'])
def api_audio():
    link = request.args.get('link')
    respuesta, codigo = procesar_descarga(link, 'audio')
    return jsonify(respuesta), codigo

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "sistema": "WOLFNET API v2.0"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
