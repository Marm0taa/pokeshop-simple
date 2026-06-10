# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PokéShop TCG — con Admin y Servicios
#  Tecnologías: Flask, SQLite, HTML, CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'pokeshop123'

# Credenciales del administrador (fijas, no se registra)
ADMIN_USUARIO  = 'admin'
ADMIN_PASSWORD = 'admin123'

# --- Conectar a la base de datos ---
def get_db():
    conn = sqlite3.connect('tienda.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Crear tablas si no existen ---
def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario  TEXT UNIQUE NOT NULL,
                email    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cartas (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre  TEXT NOT NULL,
                precio  INTEGER NOT NULL,
                imagen  TEXT NOT NULL
            );
        ''')

def encriptar(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ══════════════════════════════════════════════
#  RUTAS PÚBLICAS
# ══════════════════════════════════════════════

@app.route('/')
def inicio():
    return render_template('inicio.html', usuario=session.get('usuario'))

# CATÁLOGO — lee las cartas desde la base de datos
@app.route('/catalogo')
def catalogo():
    with get_db() as db:
        cartas = db.execute('SELECT * FROM cartas').fetchall()
    return render_template('catalogo.html', cartas=cartas, usuario=session.get('usuario'))

# SERVICIOS — página de gradeado
@app.route('/servicios')
def servicios():
    return render_template('servicios.html', usuario=session.get('usuario'))

# ══════════════════════════════════════════════
#  REGISTRO Y LOGIN
# ══════════════════════════════════════════════

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario  = request.form['usuario']
        email    = request.form['email']
        password = request.form['password']
        try:
            with get_db() as db:
                db.execute(
                    'INSERT INTO usuarios (usuario, email, password) VALUES (?, ?, ?)',
                    (usuario, email, encriptar(password))
                )
            flash('¡Cuenta creada! Ahora puedes iniciar sesión.', 'ok')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ese usuario o correo ya existe.', 'error')
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario  = request.form['usuario']
        password = request.form['password']
        with get_db() as db:
            user = db.execute(
                'SELECT * FROM usuarios WHERE usuario=? AND password=?',
                (usuario, encriptar(password))
            ).fetchone()
        if user:
            session['usuario'] = user['usuario']
            flash(f'Bienvenido, {user["usuario"]}!', 'ok')
            return redirect(url_for('catalogo'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

# ══════════════════════════════════════════════
#  CARRITO
# ══════════════════════════════════════════════

@app.route('/carrito')
def carrito():
    mi_carrito = session.get('carrito', [])
    total = sum(item['precio'] * item['cantidad'] for item in mi_carrito)
    return render_template('carrito.html', carrito=mi_carrito, total=total, usuario=session.get('usuario'))

@app.route('/agregar/<nombre>/<int:precio>')
def agregar(nombre, precio):
    carrito = session.get('carrito', [])
    for item in carrito:
        if item['nombre'] == nombre:
            item['cantidad'] += 1
            session['carrito'] = carrito
            flash(f'{nombre} actualizado en el carrito.', 'ok')
            return redirect(url_for('catalogo'))
    carrito.append({'nombre': nombre, 'precio': precio, 'cantidad': 1})
    session['carrito'] = carrito
    flash(f'{nombre} agregado al carrito!', 'ok')
    return redirect(url_for('catalogo'))

@app.route('/vaciar')
def vaciar():
    session.pop('carrito', None)
    return redirect(url_for('carrito'))

# ══════════════════════════════════════════════
#  PANEL ADMIN
# ══════════════════════════════════════════════

# LOGIN ADMIN
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['usuario'] == ADMIN_USUARIO and \
           request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True  # Marcar sesión como admin
            return redirect(url_for('admin_panel'))
        flash('Credenciales incorrectas.', 'error')
    return render_template('admin_login.html')

# PANEL PRINCIPAL — lista todas las cartas
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):  # Si no es admin, redirigir
        return redirect(url_for('admin_login'))
    with get_db() as db:
        cartas = db.execute('SELECT * FROM cartas').fetchall()
    return render_template('admin_panel.html', cartas=cartas)

# AGREGAR CARTA
@app.route('/admin/agregar', methods=['POST'])
def admin_agregar():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    nombre = request.form['nombre']
    precio = request.form['precio']
    imagen = request.form['imagen']
    with get_db() as db:
        db.execute('INSERT INTO cartas (nombre, precio, imagen) VALUES (?, ?, ?)',
                   (nombre, precio, imagen))
    flash(f'Carta "{nombre}" agregada correctamente.', 'ok')
    return redirect(url_for('admin_panel'))

# ELIMINAR CARTA
@app.route('/admin/eliminar/<int:id>')
def admin_eliminar(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    with get_db() as db:
        db.execute('DELETE FROM cartas WHERE id=?', (id,))
    flash('Carta eliminada.', 'ok')
    return redirect(url_for('admin_panel'))

# LOGOUT ADMIN
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('inicio'))

# ══════════════════════════════════════════════
#  INICIAR APP
# ══════════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
