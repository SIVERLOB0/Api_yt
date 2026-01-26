from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app) # Permite que tu bot Node.js le hable a este servidor

print("🐺 WOLF API (PYTHON ENGINE) INICIANDO...")

@app.route('/')
def home():
    return "🐺 WOLF API PYTHON: ACTIVO Y LISTO."

@app.route('/ytmp3', methods=['GET'])
def descargar_mp3():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"status": False, "error": "Falta la URL"}), 400

    print(f"📥 Procesando: {video_url}")

    # Configuración de yt-dlp para obtener el link directo
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True, # Esto nos da la info sin descargar el archivo al disco
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Extraemos lo que nos interesa
            titulo = info.get('title', 'Audio Desconocido')
            url_directa = info.get('url', None) # El link mágico directo a Google
            thumbnail = info.get('thumbnail', '')
            duracion = info.get('duration_string', '')

            if not url_directa:
                return jsonify({"status": False, "error": "No se pudo extraer el link"}), 500

            return jsonify({
                "status": True,
                "resultado": {
                    "titulo": titulo,
                    "descarga": url_directa,
                    "imagen": thumbnail,
                    "duracion": duracion
                }
            })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Ejecutamos en el puerto 5000
    app.run(host='0.0.0.0', port=5000)
