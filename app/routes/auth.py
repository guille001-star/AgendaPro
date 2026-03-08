from flask import Blueprint, render_template_string, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
import uuid

auth = Blueprint('auth', __name__)

# --- LOGIN ---
TPL_LOGIN = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
<div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
<h2 class="text-2xl font-bold text-center mb-6">Iniciar Sesion</h2>
<form method="POST">
<div class="mb-4"><label>Email</label><input type="email" name="email" required class="w-full border p-2 rounded"></div>
<div class="mb-6"><label>Contrasena</label><input type="password" name="password" required class="w-full border p-2 rounded"></div>
<button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded font-bold">Entrar</button>
</form>
<p class="text-center text-sm mt-4">¿No tienes cuenta? <a href="{{ url_for('auth.register') }}" class="text-indigo-600">Crear Cuenta</a></p>
<hr class="my-4">
<a href="{{ url_for('auth.admin_login') }}" class="block text-center text-sm text-slate-500 hover:text-slate-800">🔐 Super Admin</a>
</div></body></html>
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
    return render_template_string(TPL_LOGIN)

# --- REGISTER ---
TPL_REG = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Registro</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-100 min-h-screen flex items-center justify-center">
<div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
<h2 class="text-2xl font-bold text-center mb-6">Crear Cuenta</h2>
<form method="POST">
<div class="mb-4"><label>Nombre</label><input type="text" name="name" required class="w-full border p-2 rounded"></div>
<div class="mb-4"><label>Email</label><input type="email" name="email" required class="w-full border p-2 rounded"></div>
<div class="mb-4"><label>Contrasena</label><input type="password" name="password" required class="w-full border p-2 rounded"></div>
<div class="mb-6"><label>Confirmar</label><input type="password" name="confirm" required class="w-full border p-2 rounded"></div>
<button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded font-bold">Registrarse</button>
</form>
<p class="text-center text-sm mt-4">¿Ya tienes cuenta? <a href="{{ url_for('auth.login') }}" class="text-indigo-600">Iniciar Sesion</a></p>
</div></body></html>
"""

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm: flash('No coinciden', 'danger'); return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first(): flash('Existe', 'danger'); return redirect(url_for('auth.register'))
        new_user = User(email=email, name=name, slug=uuid.uuid4().hex[:8])
        new_user.set_password(password)
        db.session.add(new_user); db.session.commit()
        flash('Cuenta creada.', 'success')
        return redirect(url_for('auth.login'))
    return render_template_string(TPL_REG)

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
            current_user.set_password(new); db.session.commit()
            flash('Actualizada.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Incorrecta.', 'danger')
    return render_template_string("""<!DOCTYPE html><html><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-slate-100 min-h-screen flex items-center justify-center"><div class="bg-white p-6 rounded-xl shadow-lg w-full max-w-md"><h2 class="text-xl font-bold mb-4">Cambiar Contrasena</h2><form method="POST"><div class="mb-4"><label>Actual</label><input type="password" name="old_password" required class="w-full border p-2 rounded"></div><div class="mb-4"><label>Nueva</label><input type="password" name="new_password" required class="w-full border p-2 rounded"></div><button type="submit" class="w-full bg-slate-700 text-white py-2 rounded font-bold">Actualizar</button></form><a href="{{ url_for('dashboard.index') }}" class="block text-center text-sm mt-4">Volver</a></div></body></html>""")

# --- SUPER ADMIN ---
ADMIN_KEY = "superadmin123" 

@auth.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('key') == ADMIN_KEY:
            return redirect(url_for('auth.admin_panel'))
        flash('Clave incorrecta', 'danger')
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 flex items-center justify-center min-h-screen">
<div class="bg-slate-800 p-8 rounded-xl w-full max-w-sm">
<h2 class="text-xl font-bold text-white mb-4 text-center">Super Admin</h2>
<form method="POST">
<input type="password" name="key" placeholder="Clave Maestra" required class="w-full bg-slate-700 text-white p-3 rounded mb-4">
<button class="w-full bg-red-500 text-white py-2 rounded">Entrar</button>
</form></div></body></html>
""")

@auth.route('/admin/panel')
def admin_panel():
    users = User.query.all()
    return render_template_string("""
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-100 p-8">
<div class="max-w-5xl mx-auto">
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Panel Super Admin</h1>
    <a href="{{ url_for('auth.login') }}" class="text-red-600 font-bold text-sm">Salir</a>
</div>
<div class="bg-white shadow rounded-xl overflow-hidden">
<table class="w-full text-sm">
<thead class="bg-slate-800 text-white"><tr><th class="p-3 text-left">Profesional</th><th class="p-3 text-left">Email</th><th class="p-3">Link</th><th class="p-3">Accion</th></tr></thead>
<tbody>
{% for u in users %}
<tr class="border-b hover:bg-gray-50">
<td class="p-3 font-medium">{{ u.name }}</td>
<td class="p-3">{{ u.email }}</td>
<td class="p-3 text-xs text-indigo-600 truncate max-w-xs">{{ request.host_url }}agenda/{{ u.slug }}</td>
<td class="p-3 text-center"><a href="{{ url_for('auth.reset_pwd', uid=u.id) }}" class="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs">Resetear Clave</a></td>
</tr>{% endfor %}
</tbody></table></div></div></body></html>
""", users=users)

@auth.route('/admin/reset/<int:uid>')
def reset_pwd(uid):
    u = User.query.get(uid)
    if u:
        u.set_password('1234')
        db.session.commit()
        flash(f'Clave de {u.name} reseteada a: 1234', 'success')
    return redirect(url_for('auth.admin_panel'))
