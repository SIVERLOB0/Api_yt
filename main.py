import os
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

print("🐺 WOLF API (TUNNEL ENGINE): ONLINE...")

@app.route('/')
def home():
    return "🐺 WOLF API: PROXY TUNNEL READY."

# --- ENDPOINT 1: EXTRACTOR (Obtiene la Info y el Link Real) ---
@app.route('/download', methods=['GET'])
def get_info():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video') # 'video' o 'audio'
    
    if not url:
        return jsonify({"status": False, "error": "Falta parametro url"}), 400

    print(f"📥 Procesando: {url} [{tipo}]")

    # Configuración de yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    # Ajuste de formato según tipo
    if tipo == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        # Prioridad: MP4 con video+audio, si no, lo mejor disponible
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Si es una playlist o mix, tomamos el primero
            if 'entries' in info:
                info = info['entries'][0]

            # INTENTO DE OBTENER URL DIRECTA
            real_url = info.get('url')
            
            # Si 'url' está vacío (común en TikTok/YT), buscamos en 'requested_formats' o 'formats'
            if not real_url:
                if 'requested_formats' in info:
                    real_url = info['requested_formats'][0]['url']
                elif 'formats' in info:
                    real_url = info['formats'][-1]['url'] # El último suele ser el mejor

            if not real_url:
                raise Exception("No se pudo extraer el enlace directo de descarga.")

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": info.get('title', 'Wolf Media'),
                    "plataforma": info.get('extractor_key', 'Web'),
                    "tipo": tipo,
                    "duracion": info.get('duration_string', '0:00'),
                    "imagen": info.get('thumbnail', ''),
                    # IMPORTANTE: Enviamos el link real para que el bot lo use en el puente
                    "descarga_original": real_url 
                }
            })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500


# --- ENDPOINT 2: EL TÚNEL / PUENTE (La Magia Anti-Bloqueo) ---
@app.route('/stream', methods=['GET'])
def stream_media():
    file_url = request.args.get('url')
    
    if not file_url:
        return "Falta parametro url", 400

    try:
        # La API de Railway descarga el archivo (IP Limpia)
        # stream=True es vital para no llenar la RAM del servidor
        req = requests.get(file_url, stream=True, timeout=15)
        
        # Pasamos los headers correctos (como el Content-Type)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in req.raw.headers.items()
                   if name.lower() not in excluded_headers]

        # Retransmitimos los datos al Bot "chorrito a chorrito" (chunks)
        return Response(stream_with_context(req.iter_content(chunk_size=1024 * 8)),
                        headers=headers,
                        content_type=req.headers.get('content-type'))
    
    except Exception as e:
        print(f"❌ Error en Túnel: {str(e)}")
        return "Error en el servidor proxy", 500

if __name__ == '__main__':
    # Puerto dinámico para Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
