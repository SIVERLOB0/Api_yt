from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import time
import shutil

app = Flask(__name__)

# Ruta temporal segura para servidores Linux (Railway)
BASE_DIR = "/tmp/descargas_wolf"
os.makedirs(BASE_DIR, exist_ok=True)

# ==========================================
# 🌐 INTERFAZ WEB EMBEBIDA (HTML + CSS + JS)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WOLFNET API</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; }
        /* Animación suave para el menú */
        .fade-in { animation: fadeIn 0.3s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="min-h-screen font-sans flex flex-col">
    <nav class="bg-slate-900 p-4 shadow-xl border-b border-slate-800 relative z-50">
        <div class="container mx-auto flex justify-between items-center max-w-3xl">
            <div class="flex items-center space-x-3">
                <svg class="w-8 h-8 text-indigo-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                <span class="text-2xl font-bold text-white tracking-widest">WOLFNET</span>
            </div>
            <button id="menuBtn" class="text-gray-400 hover:text-white transition focus:outline-none">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                </svg>
            </button>
        </div>
        
        <div id="dropdownMenu" class="hidden absolute top-16 right-4 md:right-auto md:left-1/2 md:transform md:-translate-x-1/2 bg-slate-800 rounded-xl shadow-2xl border border-slate-700 w-56 fade-in">
            <button onclick="showSection('descarga')" class="w-full text-left px-5 py-4 hover:bg-slate-700 transition rounded-t-xl flex items-center">
                <svg class="w-5 h-5 mr-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                Descarga Web
            </button>
            <div class="border-t border-slate-700"></div>
            <button onclick="showSection('api')" class="w-full text-left px-5 py-4 hover:bg-slate-700 transition rounded-b-xl flex items-center">
                <svg class="w-5 h-5 mr-3 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                Probar API (JSON)
            </button>
        </div>
    </nav>

    <main class="container mx-auto mt-12 p-4 max-w-xl flex-grow">
        
        <div id="descarga-sec" class="bg-slate-800 p-8 rounded-2xl shadow-lg border border-slate-700 fade-in">
            <h2 class="text-2xl font-bold mb-6 text-white text-center">Descargar Multimedia</h2>
            <div class="space-y-5">
                <input type="url" id="linkDescarga" placeholder="Pega el enlace de TikTok, YouTube, FB..." class="w-full bg-slate-900 border border-slate-600 rounded-xl p-4 text-white focus:ring-2 focus:ring-indigo-500 outline-none transition">
                
                <div class="flex space-x-4">
                    <button onclick="ejecutar('descarga', 'video')" class="flex-1 bg-indigo-600 hover:bg-indigo-700 py-3 rounded-xl font-bold transition flex justify-center items-center">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"></path></svg> Video
                    </button>
                    <button onclick="ejecutar('descarga', 'audio')" class="flex-1 bg-emerald-600 hover:bg-emerald-700 py-3 rounded-xl font-bold transition flex justify-center items-center">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z"></path></svg> Audio
                    </button>
                </div>
                <p id="estadoInfo" class="text-sm text-center text-indigo-400 hidden animate-pulse font-medium">Procesando petición... Esto puede tardar unos segundos.</p>
            </div>
        </div>

        <div id="api-sec" class="hidden bg-slate-800 p-8 rounded-2xl shadow-lg border border-slate-700 fade-in">
            <h2 class="text-2xl font-bold mb-2 text-white text-center flex justify-center items-center">
                Consola de API
            </h2>
            <p class="text-gray-400 text-sm mb-6 text-center">Genera la ruta REST. Al dar clic, se abrirá en una nueva pestaña (Stream de bytes o JSON de error).</p>
            
            <div class="space-y-5">
                <input type="url" id="linkApi" placeholder="Enlace a procesar..." class="w-full bg-slate-900 border border-slate-600 rounded-xl p-4 text-white focus:ring-2 focus:ring-yellow-500 outline-none transition">
                
                <div class="flex space-x-4">
                    <button onclick="ejecutar('api', 'video')" class="flex-1 border-2 border-yellow-500 text-yellow-500 hover:bg-yellow-500 hover:text-slate-900 py-3 rounded-xl font-bold transition flex justify-center items-center">
                        GET /api/video
                    </button>
                    <button onclick="ejecutar('api', 'audio')" class="flex-1 border-2 border-pink-500 text-pink-500 hover:bg-pink-500 hover:text-slate-900 py-3 rounded-xl font-bold transition flex justify-center items-center">
                        GET /api/audio
                    </button>
                </div>
            </div>
        </div>
    </main>

    <script>
        const menuBtn = document.getElementById('menuBtn');
        const dropdownMenu = document.getElementById('dropdownMenu');
        
        // Abrir/Cerrar menú
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('hidden');
        });

        // Cerrar menú al dar click afuera
        document.addEventListener('click', (e) => {
            if(!dropdownMenu.classList.contains('hidden') && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.add('hidden');
            }
        });

        // Cambiar entre vista Descarga Web y API
        function showSection(sec) {
            document.getElementById('descarga-sec').classList.add('hidden');
            document.getElementById('api-sec').classList.add('hidden');
            document.getElementById(sec + '-sec').classList.remove('hidden');
            dropdownMenu.classList.add('hidden');
        }

        // Ejecutar acción dinámica
        function ejecutar(modo, tipo) {
            const inputId = modo === 'descarga' ? 'linkDescarga' : 'linkApi';
            const link = document.getElementById(inputId).value;
            
            if(!link) {
                alert('⚠️ Por favor ingresa un enlace válido.');
                return;
            }

            const urlEndpoint = `/api/${tipo}?link=${encodeURIComponent(link)}`;

            if(modo === 'descarga') {
                const estado = document.getElementById('estadoInfo');
                estado.classList.remove('hidden');
                estado.textContent = "Procesando petición... Esto puede tardar unos segundos.";
                
                // Redirigir para que el navegador descargue el archivo nativamente
                window.location.href = urlEndpoint;
                
                setTimeout(() => { estado.classList.add('hidden'); }, 8000);
            } else {
                // Modo API abre una nueva pestaña
                window.open(urlEndpoint, '_blank');
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# ⚙️ LÓGICA DEL SERVIDOR (WOLFNET CORE)
# ==========================================

def limpiar_basura():
    """Protocolo de limpieza: elimina carpetas con más de 10 minutos de antigüedad"""
    ahora = time.time()
    for nombre_carpeta in os.listdir(BASE_DIR):
        ruta_carpeta = os.path.join(BASE_DIR, nombre_carpeta)
        if os.path.isdir(ruta_carpeta):
            if os.path.getctime(ruta_carpeta) < ahora - 600:
                try:
                    shutil.rmtree(ruta_carpeta)
                except:
                    pass

def procesar_descarga(link, tipo):
    # 1. Limpiar espacio antes de empezar
    limpiar_basura()
    
    if not link:
        return jsonify({"status": "error", "mensaje": "Vector vacio. Usa el parametro ?link="}), 400

    # 2. Parseo y creación de entorno
    link_base = link.split('?')[0]
    link_limpio = ''.join(e for e in link_base.replace('https://', '').replace('http://', '') if e.isalnum() or e == '_')[:80]
    
    if not link_limpio:
        link_limpio = f"descarga_{int(time.time())}"

    ruta_destino = os.path.join(BASE_DIR, link_limpio)
    os.makedirs(ruta_destino, exist_ok=True)

    # 3. Configuración Sigilosa de YT-DLP
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

    # 4. Proceso de descarga
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
            
        # Buscar el archivo final descargado (evita archivos basura .part)
        archivos = [f for f in os.listdir(ruta_destino) if not f.endswith('.part') and not f.endswith('.ytdl')]
        
        if archivos:
            archivo_final = os.path.join(ruta_destino, archivos[0])
            # 🔥 ENVÍA EL ARCHIVO POR INTERNET (Para que la Web lo baje y el Bot de Node.js lo intercepte)
            return send_file(archivo_final, as_attachment=True)
        else:
            return jsonify({"status": "error", "mensaje": "Fallo al generar el archivo final."}), 404

    except Exception as e:
        # Destruir evidencia en caso de falla
        if os.path.exists(ruta_destino):
            shutil.rmtree(ruta_destino, ignore_errors=True)
        return jsonify({"status": "error", "mensaje": f"Mision abortada. Error interno."}), 500

# --- ENDPOINTS ---
@app.route('/', methods=['GET'])
def home():
    # Renderiza la interfaz web embebida en el dominio raíz
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/video', methods=['GET'])
def api_video():
    link = request.args.get('link')
    return procesar_descarga(link, 'video')

@app.route('/api/audio', methods=['GET'])
def api_audio():
    link = request.args.get('link')
    return procesar_descarga(link, 'audio')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
