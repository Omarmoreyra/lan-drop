import os
import socket
import threading
import uuid
import zipfile
from flask import Flask, request, render_template_string, Response, send_from_directory, jsonify
from functools import wraps
from werkzeug.utils import secure_filename
import qrcode
import pystray
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# Configuración
# =========================

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", r"./Compartidos")
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", r"./Descargas")


def ensure_directory(name, path):
    if not path or not isinstance(path, str):
        raise ValueError(f"{name} inválida: define una ruta válida.")

    abs_path = os.path.abspath(path)

    if os.path.exists(abs_path):
        if not os.path.isdir(abs_path):
            raise ValueError(f"{name} inválida: {abs_path} no es un directorio.")
    else:
        try:
            os.makedirs(abs_path, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"No se pudo crear {name} en {abs_path}: {exc}") from exc

    return abs_path


UPLOAD_FOLDER = ensure_directory("UPLOAD_FOLDER", UPLOAD_FOLDER)
DOWNLOAD_FOLDER = ensure_directory("DOWNLOAD_FOLDER", DOWNLOAD_FOLDER)

# =========================
# Icono de bandeja 
# =========================

tray_icon = None


def create_tray_image():
    size = 64
    img = Image.new("RGB", (size, size), (15, 32, 55))
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, size - 9, size - 9], outline=(0, 123, 255), width=4)
    draw.rectangle([18, 18, size - 19, size - 19], fill=(0, 123, 255))
    draw.rectangle([24, 24, size - 25, size - 25], fill=(255, 255, 255))
    return img


def start_tray(server_url):
    # Mantener la referencia global evita que el icono sea recolectado.
    global tray_icon

    def on_exit(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("LAN Drop", None, enabled=False),
        pystray.MenuItem(server_url, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", on_exit)
    )

    tray_icon = pystray.Icon("LAN Drop", create_tray_image(), "LAN Drop", menu)
    tray_icon.run()


def start_tray_async(server_url):
    thread = threading.Thread(target=start_tray, args=(server_url,), daemon=True)
    thread.start()
    return thread

USERNAME =os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "password")

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB total request

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# =========================
# HTML 
# =========================

HTML_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAN Drop</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
}

.card {
    width: 100%;
    max-width: 420px;
    background: #ffffff;
    padding: 28px;
    border-radius: 22px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
}

h2 {
    text-align: center;
    margin-bottom: 25px;
}

.tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 20px;
    background: #f4f6f8;
    padding: 6px;
    border-radius: 14px;
}

.tab-btn {
    border: none;
    padding: 12px 10px;
    border-radius: 10px;
    font-weight: 600;
    background: #e2e6ea;
    color: #333;
    cursor: pointer;
    transition: 0.2s;
}

.tab-btn.active {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    box-shadow: 0 8px 20px rgba(0, 123, 255, 0.3);
}

.tab-pane { display: none; }
.tab-pane.active { display: block; }

.file-input { display: none; }

.file-btn {
    display: block;
    width: fit-content;
    min-width: 220px;
    padding: 16px 22px;
    margin: 0 auto;
    border-radius: 18px;
    border: none;
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    font-weight: 600;
    text-align: center;
    cursor: pointer;
    transition: 0.2s;
}

.file-btn:hover {
    opacity: 0.9;
}

.file-btn:active {
    transform: scale(0.98);
}

#fileName {
    margin-top: 8px;
    font-size: 13px;
    color: #555;
    word-break: break-word;
}

.preview {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}

.preview img {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 6px;
}

.text-label {
    margin-top: 30px;   /* separación real del botón */
    font-weight: 600;
    display: block;
}

textarea {
    width: 100%;
    padding: 14px;
    border-radius: 16px;
    border: 1px solid #ccc;
    margin-top: 10px;
    resize: none;
}

button {
    width: 100%;
    padding: 16px;
    border-radius: 18px;
    border: none;
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    font-weight: 600;
    margin-top: 20px;
    cursor: pointer;
}

.shutdown-btn {
    background: linear-gradient(135deg, #dc3545, #a71d2a);
}

.progress-container {
    width: 100%;
    background: #eee;
    border-radius: 6px;
    margin-top: 15px;
}

.progress-bar {
    width: 0%;
    height: 8px;
    background: #28a745;
    border-radius: 6px;
}

.success {
    margin-top: 15px;
    background: #e6f9ec;
    padding: 10px;
    border-radius: 10px;
}

.file-list {
    list-style: none;
    padding: 0;
    margin: 16px 0 0 0;
}

.file-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    background: #f7f9fb;
    margin-bottom: 10px;
    border: 1px solid #e5e7eb;
}

.file-item a {
    color: #0056b3;
    font-weight: 600;
    text-decoration: none;
}

.file-item a:hover { text-decoration: underline; }

.file-thumb {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    background: #fff;
}
</style>
</head>

<body>

<div class="card">
<h2>LAN Drop</h2>

<div class="tabs">
    <button class="tab-btn active" data-tab="uploadTab">Subir a PC</button>
    <button class="tab-btn" data-tab="downloadTab">Descargas desde PC</button>
</div>

<div id="uploadTab" class="tab-pane active">
    <label for="fileInput" class="file-btn">
    Seleccionar archivos
    </label>
    <input type="file" id="fileInput" class="file-input" multiple>
    <div id="fileName"></div>

    <div class="preview" id="preview"></div>

    <label class="text-label">Texto</label>
    <textarea id="textContent" rows="4" placeholder="Pega un link o texto aquí..."></textarea>

    <button onclick="uploadData()">Enviar</button>

    <div class="progress-container">
    <div class="progress-bar" id="progressBar"></div>
    </div>

    <form method="post" action="/shutdown"
    onsubmit="return confirm('¿Seguro que quieres cerrar el servidor?');">
    <button class="shutdown-btn">Cerrar Servidor</button>
    </form>

    <div id="status"></div>
</div>

<div id="downloadTab" class="tab-pane">
    <p><strong>Hub de descargas:</strong> Archivos disponibles en la carpeta de descargas.</p>
    <button onclick="fetchFiles()">Actualizar lista</button>
    <ul id="fileList" class="file-list"></ul>
</div>

</div>

<script>
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

function switchTab(tabId) {
    tabButtons.forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
    tabPanes.forEach(p => p.classList.toggle('active', p.id === tabId));
    if (tabId === 'downloadTab') {
        fetchFiles();
    }
}

const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const fileNameDiv = document.getElementById('fileName');

fileInput.addEventListener('change', function() {

    preview.innerHTML = "";

    const names = Array.from(this.files).map(f => f.name);
    fileNameDiv.innerText = names.length ? names.join(", ") : "";

    Array.from(this.files).forEach(file => {
        if (file.type.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            preview.appendChild(img);
        }
    });
});

function uploadData() {
    const files = fileInput.files;
    const text = document.getElementById("textContent").value;

    const formData = new FormData();

    for (let file of files) {
        formData.append("file", file);
    }

    formData.append("text_content", text);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            document.getElementById("progressBar").style.width = percent + "%";
        }
    };

    xhr.onload = function() {
        document.getElementById("status").innerText = xhr.responseText;
        document.getElementById("progressBar").style.width = "0%";
        preview.innerHTML = "";
        fileInput.value = "";
        fileNameDiv.innerText = "";
        document.getElementById("textContent").value = "";
    };

    xhr.send(formData);
}

function fetchFiles() {
    const list = document.getElementById('fileList');
    list.innerHTML = '<li>Cargando...</li>';

    fetch('/list-files')
        .then(res => {
            if (!res.ok) throw new Error('No se pudo obtener la lista');
            return res.json();
        })
        .then(data => {
            list.innerHTML = '';
            if (!data.files || !data.files.length) {
                list.innerHTML = '<li>No hay archivos disponibles.</li>';
                return;
            }

            const isImage = (name) => /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(name);

            data.files.forEach(name => {
                const li = document.createElement('li');
                li.className = 'file-item';

                if (isImage(name)) {
                    const img = document.createElement('img');
                    img.className = 'file-thumb';
                    img.src = '/preview/' + encodeURIComponent(name);
                    img.alt = name;
                    li.appendChild(img);
                }

                const link = document.createElement('a');
                link.href = '/download/' + encodeURIComponent(name);
                link.innerText = name;

                li.appendChild(link);
                list.appendChild(li);
            });
        })
        .catch(err => {
            list.innerHTML = `<li>Error: ${err.message}</li>`;
        });
}
</script>

</body>
</html>
"""

# =========================
# Autenticación
# =========================

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response('Credenciales requeridas', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# =========================
# Rutas
# =========================

@app.route('/')
@requires_auth
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload', methods=['POST'])
@requires_auth
def upload():
    files = request.files.getlist('file')
    text = request.form.get('text_content')

    response_msg = ""

    # Guardar texto si existe
    if text and text.strip():
        with open(os.path.join(UPLOAD_FOLDER, "links_y_textos.txt"),
                  "a", encoding="utf-8") as f:
            f.write(f"---\n{text}\n")
        response_msg += "Texto guardado. "

    # Manejo de archivos
    if files and any(f.filename for f in files):

        if len(files) > 1:
            zip_name = f"upload_{uuid.uuid4().hex}.zip"
            zip_path = os.path.join(UPLOAD_FOLDER, zip_name)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        unique = f"{uuid.uuid4().hex}_{filename}"
                        temp_path = os.path.join(UPLOAD_FOLDER, unique)
                        file.save(temp_path)
                        zipf.write(temp_path, arcname=filename)
                        os.remove(temp_path)

            response_msg += f"Archivos comprimidos en {zip_name}"

        else:
            file = files[0]
            filename = secure_filename(file.filename)
            unique = f"{uuid.uuid4().hex}_{filename}"
            file.save(os.path.join(UPLOAD_FOLDER, unique))
            response_msg += f"Archivo guardado como {unique}"

    if not response_msg:
        response_msg = "Nada enviado."

    return response_msg


@app.route('/list-files', methods=['GET'])
@requires_auth
def list_files():
    try:
        files = [f for f in os.listdir(DOWNLOAD_FOLDER)
                 if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))]
        return jsonify({"files": sorted(files)})
    except Exception as exc:
        return jsonify({"error": str(exc), "files": []}), 500


@app.route('/download/<path:filename>', methods=['GET'])
@requires_auth
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


@app.route('/preview/<path:filename>', methods=['GET'])
@requires_auth
def preview(filename):
    # Sirve el archivo para previsualización sin forzar descarga.
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)


@app.route('/shutdown', methods=['POST'])
@requires_auth
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    else:
        os._exit(0)
    return "Servidor apagado."


# =========================
# Main
# =========================

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def show_qr(url):
    # Print and save a small QR so other devices can scan the server URL.
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(UPLOAD_FOLDER, "server_qr.png")
    qr_img.save(qr_path)
    print("QR guardado en:", qr_path)


if __name__ == '__main__':
    ip = get_local_ip()
    port = 5000
    server_url = f"https://{ip}:{port}"
    print("Servidor activo en:", server_url)
    show_qr(server_url)
    start_tray_async(server_url)
    app.run(host='0.0.0.0', port=port, ssl_context='adhoc')
