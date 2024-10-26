from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from flask import Flask, render_template, request, jsonify
from markupsafe import Markup  # Importar Markup desde markupsafe
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para evitar problemas de GUI
import matplotlib.pyplot as plt
import pandas as pd
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.io import capture_output



# Ruta al archivo de lecciones
LECCIONES_FILE = 'lecciones.txt'
app = Flask(__name__)
app.secret_key = 'clave-secreta'  # Cambia esta clave por una segura
app.config['SESSION_TYPE'] = 'filesystem'  # Guardar las sesiones en el sistema de archivos
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'flask_session:'
# Inicializar Flask-Session
Session(app)

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simulación de usuarios en la base de datos (puedes reemplazar con una base de datos real)
users = {'alumno1': {'password': 'password123'}, 'alumno2': {'password': 'password456'}}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

def cargar_lecciones():
    lecciones = []
    with open('lecciones.txt', 'r', encoding='utf-8') as file:  # Abrir archivo con codificación Latin-1
        contenido = file.read().strip()
        lecciones_raw = contenido.split("--- LECCION ---")  # Usar el nuevo delimitador
        for leccion in lecciones_raw:
            if leccion.strip():  # Asegurarse de que no esté vacío
                partes = leccion.split("\n")
                nombre = partes[0].strip()
                explicacion = partes[1].strip()
                codigo_base = "\n".join(partes[3:]).strip()  # Unir el código base
                lecciones.append({'nombre': nombre, 'explicacion': explicacion, 'codigo': codigo_base})
    return lecciones



@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return 'Credenciales inválidas', 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('kernel.html', user=current_user.id)

@app.route('/ejecutar', methods=['POST'])
@login_required
def ejecutar():
    codigo = request.json.get('codigo', '')
    
    resultado_html = ''
    error = ''
    
    try:
        exec_locals = {}
        exec(codigo, {}, exec_locals)

        # Capturamos el resultado si se ha definido
        if 'resultado' in exec_locals:
            resultado_html = f"<pre>{exec_locals['resultado']}</pre>"
        else:
            resultado_html = "<pre>No se definió 'resultado'.</pre>"

    except Exception as e:
        # Captura el error y devuelve su mensaje
        error = f"<div style='color: red;'>Error: {str(e)}</div>"

    # Devolvemos tanto el resultado como el error
    return jsonify({'resultado': Markup(resultado_html), 'error': Markup(error)})



@app.route('/lecciones')
def lecciones():
    lecciones = cargar_lecciones()
    print("Lecciones cargadas:", lecciones)  # Mensaje de depuración
    return render_template('lecciones.html', lecciones=lecciones)

@app.route('/leccion/<int:leccion_id>')
def leccion(leccion_id):
    lecciones = cargar_lecciones()
    if leccion_id < len(lecciones):
        leccion = lecciones[leccion_id]
        siguiente_id = leccion_id + 1 if leccion_id + 1 < len(lecciones) else None
        return render_template('leccion.html', leccion=leccion, siguiente_id=siguiente_id)
    return "Lección no encontrada", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
