from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

print("🐺 WOLF API (PYTHON ENGINE) MULTIMEDIA: INICIANDO...")

@app.route('/')
def home():
    return "🐺 WOLF API: READY FOR ALL PLATFORMS."

@app.route('/download', methods=['GET'])
def descargar_media():
    url = request.args.get('url')
    tipo = request.args.get('type', 'video') # Por defecto descarga video, si quieres audio envía ?type=audio
    
    if not url:
        return jsonify({"status": False, "error": "Falta la URL"}), 400

    print(f"📥 Wolf procesando [{tipo}]: {url}")

    # Configuración inteligente
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True, 
        'extract_flat': False,
        # Opciones para evadir algunos bloqueos simples
        'nocheckcertificate': True,
        'geo_bypass': True,
        # User Agent genérico para que TikTok/FB no nos detecten tan rápido como bot
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # Lógica de selección de formato
    if tipo == 'audio':
        # Si pide audio, buscamos el mejor audio posible
        ydl_opts['format'] = 'bestaudio/best'
    else:
        # Si es video, priorizamos MP4 para compatibilidad con WhatsApp/Web
        # Si no hay mp4, baja el mejor disponible
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Extraemos la info sin descargar
            info = ydl.extract_info(url, download=False)
            
            # 2. Manejo de casos donde el link es una playlist o un reel complejo
            if 'entries' in info:
                # Tomamos el primer video si es una lista/feed
                info = info['entries'][0]

            titulo = info.get('title', 'Video Wolf')
            url_directa = info.get('url', None)
            thumbnail = info.get('thumbnail', '')
            duracion = info.get('duration_string', '')
            plataforma = info.get('extractor_key', 'Desconocida')

            # Verificación extra por si la URL está escondida
            if not url_directa and 'requested_formats' in info:
                url_directa = info['requested_formats'][0]['url']

            if not url_directa:
                return jsonify({"status": False, "error": "No se pudo extraer el enlace directo"}), 500

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "plataforma": plataforma,
                    "tipo": tipo,
                    "descarga": url_directa,
                    "imagen": thumbnail,
                    "duracion": duracion
                }
            })

    except Exception as e:
        print(f"❌ Error Wolf: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
