from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from openai import OpenAI
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

# Instancia el cliente de OpenAI con tu clave de API
client = key
def cargar_lecciones():
    lecciones = []
    with open('lecciones.txt', 'r', encoding='utf-8') as file:
        contenido = file.read().strip()
        lecciones_raw = contenido.split("--- LECCION ---")
        for leccion in lecciones_raw:
            if leccion.strip():
                partes = leccion.split('|')
                if len(partes) >= 4:  # Asegurarse de que haya al menos 4 secciones (nombre, explicación, pasos, código)
                    nombre = partes[0].strip()
                    explicacion = partes[1].strip()
                    pasos = partes[2].strip()
                    codigo = partes[3].strip()  # Separar el código de los comentarios
                    lecciones.append({
                        'nombre': nombre, 
                        'explicacion': explicacion, 
                        'codigo': codigo
                    })
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
    
    if 'exec_count' not in session:
        session['exec_count'] = 0

    resultado_html = ''
    error = ''
    chat_response = ''

    try:
        exec_locals = {}
        exec(codigo, {}, exec_locals)

        if 'resultado' in exec_locals:
            resultado_html = f"<pre>{exec_locals['resultado']}</pre>"
        else:
            resultado_html = "<pre>No se definió 'resultado'.</pre>"

        # Detectar si es la primera o segunda ejecución
        if session['exec_count'] == 0:
            # Primera ejecución
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil que ayuda a los estudiantes con Python."},
                    {"role": "user", "content": f"Proporciona un ejercicio muy muy basico y siempre que use el caso base pero diferente en pocas palabras para el siguiente código: {codigo}"}
                ]
            )
            chat_response = response.choices[0].message.content
            session['exec_count'] += 1
            session['last_reponse']=chat_response
        else:
            # Segunda ejecución: revisión del código
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Revisa si el ejercicio es correcto tu le pediste {session['last_reponse']}  y aplico tus instrucciones al detalle por ejemplo nombres no debe usar cosas difernetes a la originales contesta si o no siempre recurda tus instrucciones si el estudiante no nombro de manera correcta la funcion o nu uso los argumentos correctos di no en caso de no dale un pequeño tip de que mejorar" },
                    {"role": "user", "content": f"Hola ejecute este código: {codigo}. ¿Está correcto?"}
                ]
            )
            chat_response = response.choices[0].message.content

    except Exception as e:
        error = f"<div style='color: red;'>Error: {str(e)}</div>"

    return jsonify({'resultado': Markup(resultado_html), 'error': Markup(error), 'chat_response': chat_response})


@app.route('/lecciones')
def lecciones():
    lecciones = cargar_lecciones()
    print("Lecciones cargadas:", lecciones)  # Mensaje de depuración
    return render_template('lecciones.html', lecciones=lecciones)

@app.route('/leccion/<int:leccion_id>')
def leccion(leccion_id):
    session['exec_count'] = 0 
    lecciones = cargar_lecciones()
    if leccion_id < len(lecciones):
        leccion = lecciones[leccion_id]
        siguiente_id = leccion_id + 1 if leccion_id + 1 < len(lecciones) else None
        return render_template('leccion.html', leccion=leccion, siguiente_id=siguiente_id)
    return "Lección no encontrada", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
