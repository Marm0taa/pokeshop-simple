# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PokéShop TCG — Versión Simple
#  Tecnologías: Flask, SQLite, HTML, CSS, JS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

# --- Crear la app Flask ---
app = Flask(__name__)
app.secret_key = 'pokeshop123'  # Necesario para usar sesiones

# --- Conectar a la base de datos ---
def get_db():
    conn = sqlite3.connect('tienda.db')
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

# --- Crear las tablas si no existen ---
def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario  TEXT UNIQUE NOT NULL,
                email    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')

# --- Encriptar contraseñas ---
def encriptar(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ══════════════════════════════════════════════
#  RUTAS
# ══════════════════════════════════════════════

# INICIO
@app.route('/')
def inicio():
    # Pasamos el usuario de sesión al template (None si no hay sesión)
    return render_template('inicio.html', usuario=session.get('usuario'))


# CATÁLOGO
@app.route('/catalogo')
def catalogo():
    return render_template('catalogo.html', usuario=session.get('usuario'))


# REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Obtener datos del formulario
        usuario  = request.form['usuario']
        email    = request.form['email']
        password = request.form['password']

        try:
            with get_db() as db:
                # Insertar nuevo usuario con password encriptado
                db.execute(
                    'INSERT INTO usuarios (usuario, email, password) VALUES (?, ?, ?)',
                    (usuario, email, encriptar(password))
                )
            flash('¡Cuenta creada! Ahora puedes iniciar sesión.', 'ok')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ese usuario o correo ya existe.', 'error')

    return render_template('registro.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario  = request.form['usuario']
        password = request.form['password']

        with get_db() as db:
            # Buscar usuario con ese nombre y password
            user = db.execute(
                'SELECT * FROM usuarios WHERE usuario=? AND password=?',
                (usuario, encriptar(password))
            ).fetchone()

        if user:
            # Guardar usuario en sesión
            session['usuario'] = user['usuario']
            flash(f'Bienvenido, {user["usuario"]}!', 'ok')
            return redirect(url_for('catalogo'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('login.html')


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()  # Borrar sesión
    return redirect(url_for('inicio'))


# CARRITO (página simple)
@app.route('/carrito')
def carrito():
    # El carrito se guarda en la sesión como lista
    mi_carrito = session.get('carrito', [])
    total = sum(item['precio'] * item['cantidad'] for item in mi_carrito)
    return render_template('carrito.html', carrito=mi_carrito, total=total, usuario=session.get('usuario'))


# AGREGAR AL CARRITO
@app.route('/agregar/<nombre>/<int:precio>')
def agregar(nombre, precio):
    carrito = session.get('carrito', [])

    # Ver si la carta ya está en el carrito
    for item in carrito:
        if item['nombre'] == nombre:
            item['cantidad'] += 1
            session['carrito'] = carrito
            flash(f'{nombre} actualizado en el carrito.', 'ok')
            return redirect(url_for('catalogo'))

    # Si no está, agregarla
    carrito.append({'nombre': nombre, 'precio': precio, 'cantidad': 1})
    session['carrito'] = carrito
    flash(f'{nombre} agregado al carrito!', 'ok')
    return redirect(url_for('catalogo'))


# VACIAR CARRITO
@app.route('/vaciar')
def vaciar():
    session.pop('carrito', None)
    return redirect(url_for('carrito'))


# ══════════════════════════════════════════════
#  INICIAR APP
# ══════════════════════════════════════════════
if __name__ == '__main__':
    init_db()       # Crear tablas si no existen
    app.run(debug=True)  # debug=True muestra errores en el navegador
