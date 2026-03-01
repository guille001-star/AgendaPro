from flask import Blueprint, render_template_string, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
import uuid

auth = Blueprint('auth', __name__)

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 class="text-2xl font-bold text-center mb-6">Iniciar Sesión</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input type="email" name="email" required class="w-full border p-2 rounded">
            </div>
            <div class="mb-6">
                <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
                <input type="password" name="password" required class="w-full border p-2 rounded">
            </div>
            <button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded font-bold hover:bg-indigo-700">Entrar</button>
        </form>
        <p class="text-center text-sm mt-4">¿No tienes cuenta? <a href="{{ url_for('auth.register') }}" class="text-indigo-600 hover:underline">Crear Cuenta</a></p>
    </div>
</body>
</html>
"""

HTML_REGISTER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 class="text-2xl font-bold text-center mb-6">Crear Cuenta</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
                <input type="text" name="name" required class="w-full border p-2 rounded">
            </div>
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input type="email" name="email" required class="w-full border p-2 rounded">
            </div>
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
                <input type="password" name="password" required class="w-full border p-2 rounded">
            </div>
            <div class="mb-6">
                <label class="block text-sm font-medium text-slate-700 mb-1">Confirmar</label>
                <input type="password" name="confirm" required class="w-full border p-2 rounded">
            </div>
            <button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded font-bold hover:bg-indigo-700">Registrarse</button>
        </form>
        <p class="text-center text-sm mt-4">¿Ya tienes cuenta? <a href="{{ url_for('auth.login') }}" class="text-indigo-600 hover:underline">Iniciar Sesión</a></p>
    </div>
</body>
</html>
"""

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template_string(HTML_LOGIN)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('El email ya existe.', 'danger')
            return redirect(url_for('auth.register'))
        new_user = User(email=email, name=name, slug=uuid.uuid4().hex[:8])
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Cuenta creada. Inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template_string(HTML_REGISTER)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form.get('old_password')
        new = request.form.get('new_password')
        if current_user.check_password(old):
            current_user.set_password(new)
            db.session.commit()
            flash('Contraseña actualizada.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Contraseña actual incorrecta.', 'danger')
    return render_template_string("""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
<div class="bg-white p-6 rounded-xl shadow-lg w-full max-w-md">
<h2 class="text-xl font-bold mb-4">Cambiar Contraseña</h2>
<form method="POST">
<div class="mb-4"><label>Actual</label><input type="password" name="old_password" required class="w-full border p-2 rounded"></div>
<div class="mb-4"><label>Nueva</label><input type="password" name="new_password" required class="w-full border p-2 rounded"></div>
<button type="submit" class="w-full bg-slate-700 text-white py-2 rounded font-bold">Actualizar</button>
</form>
<a href="{{ url_for('dashboard.index') }}" class="block text-center text-sm mt-4">Volver</a>
</div></body></html>
""")
