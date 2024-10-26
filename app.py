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




app = Flask(__name__)
app.secret_key = 'clave-secreta'  # Cambia esta clave por una segura
app.config['SESSION_TYPE'] = 'filesystem'  # Guardar las sesiones en el sistema de archivos

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
def ejecutar():
    codigo = request.json.get('codigo', '')

    # Variables para almacenar el resultado y los errores
    resultado_html = ''
    error = ''
    
    try:
        # Capturar la salida de la ejecución con IPython
        with capture_output() as output:
            # Ejecutar el código proporcionado
            exec_locals = {}
            exec(codigo, globals(), exec_locals)

        # Obtener el texto de la salida capturada
        output_text = output.stdout

        # Verificar la última variable en exec_locals
        ultimo_resultado = None
        if exec_locals:
            # Obtener la última variable definida
            ultimo_resultado = list(exec_locals.values())[-1]

        # Verificar si se generó una figura
        img_base64 = ''
        fig = plt.gcf()
        if fig.get_axes():  # Si hay una figura activa
            img = io.BytesIO()
            fig.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode()
            plt.close(fig)

            # Formatear la imagen como HTML
            resultado_html = f"<img src='data:image/png;base64,{img_base64}'/>"
        elif ultimo_resultado is not None:
            # Mostrar el último resultado como HTML
            resultado_html = f"<pre>{ultimo_resultado}</pre>"
        elif output_text:
            # Mostrar el texto capturado como HTML
            resultado_html = f"<pre>{output_text}</pre>"
        else:
            resultado_html = "<pre>No se generó ninguna salida.</pre>"

    except Exception as e:
        error = f"<div style='color: red;'>Error: {str(e)}</div>"

    return jsonify({'resultado': Markup(resultado_html), 'error': Markup(error)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
