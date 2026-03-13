from flask import Blueprint, render_template_string, request, flash, redirect, url_for
from app import db
from app.models.user import User
import uuid

admin = Blueprint('admin', __name__)

CLAVE_MAESTRA = "agendapromaster2026"

# --- LOGIN ADMIN ---
@admin.route('/super-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        if request.form.get('clave') == CLAVE_MAESTRA:
            return redirect(url_for('admin.panel'))
        flash('Clave incorrecta', 'danger')
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-900 flex items-center justify-center h-screen'>
    <div class='bg-white p-8 rounded-xl shadow-xl w-96'>
    <h1 class='text-2xl font-bold mb-4 text-center'>🔐 Super Admin</h1>
    <form method='POST'>
    <input type='password' name='clave' placeholder='Clave Maestra' required class='w-full border p-3 rounded mb-4'>
    <button class='w-full bg-red-500 text-white py-2 rounded font-bold'>Acceder</button>
    </form></div></body></html>
    """)

# --- PANEL (AGREGAR Y LISTAR) ---
@admin.route('/super-admin/panel', methods=['GET', 'POST'])
def panel():
    # Lógica para AGREGAR
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        if name and email:
            existe = User.query.filter_by(email=email).first()
            if existe:
                flash('Ese email ya existe.', 'danger')
            else:
                nuevo = User(name=name, email=email, slug=uuid.uuid4().hex[:8])
                nuevo.set_password('1234')
                db.session.add(nuevo)
                db.session.commit()
                flash(f'Profesional "{name}" creado. Clave: 1234', 'success')
                return redirect(url_for('admin.panel'))

    # Listar existentes
    users = User.query.all()
    
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-4xl mx-auto'>
        <h1 class='text-2xl font-bold mb-6'>Panel Super Admin</h1>

        <!-- MENSAJES -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for cat, msg in messages %}
            <div class="bg-{{ 'green' if cat=='success' else 'red' }}-100 text-{{ 'green' if cat=='success' else 'red' }}-700 p-3 rounded mb-4">{{ msg }}</div>
            {% endfor %}
        {% endwith %}

        <!-- FORMULARIO -->
        <div class="bg-white p-6 rounded-xl shadow mb-6">
            <h2 class="font-bold mb-2">Agregar Nuevo Profesional</h2>
            <form method="POST" class="flex gap-2">
                <input type="text" name="name" placeholder="Nombre" required class="flex-1 border p-2 rounded">
                <input type="email" name="email" placeholder="Email" required class="flex-1 border p-2 rounded">
                <button class="bg-indigo-600 text-white px-4 py-2 rounded font-bold">Crear</button>
            </form>
        </div>

        <!-- LISTA -->
        <div class="bg-white rounded-xl shadow overflow-hidden">
            <table class="w-full text-sm">
                <thead class="bg-slate-800 text-white"><tr><th class="p-3 text-left">Nombre</th><th class="p-3 text-left">Email</th><th class="p-3">Acción</th></tr></thead>
                <tbody>
                {% for u in users %}
                <tr class="border-b">
                    <td class="p-3 font-medium">{{ u.name }}</td>
                    <td class="p-3">{{ u.email }}</td>
                    <td class="p-3"><a href="{{ url_for('admin.reset_pwd', uid=u.id) }}" class="text-yellow-600 text-xs font-bold">Resetear Clave</a></td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    </body></html>
    """, users=users)

# --- RESETEAR CLAVE ---
@admin.route('/super-admin/reset/<int:uid>')
def reset_pwd(uid):
    u = User.query.get(uid)
    if u:
        u.set_password('1234')
        db.session.commit()
        flash(f'Clave reseteada a 1234', 'success')
    return redirect(url_for('admin.panel'))
