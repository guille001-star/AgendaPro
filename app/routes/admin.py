from flask import Blueprint, render_template_string, request, flash, redirect, url_for
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from flask_login import login_user
import uuid

admin = Blueprint('admin', __name__)

CLAVE_MAESTRA = "agendapromaster2026"

# --- 1. LOGIN ADMIN ---
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

# --- 2. PANEL PRINCIPAL (LISTADO) ---
@admin.route('/super-admin/panel', methods=['GET', 'POST'])
def panel():
    # Agregar nuevo
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        if name and email:
            if User.query.filter_by(email=email).first():
                flash('Email ya existe.', 'danger')
            else:
                u = User(name=name, email=email, slug=uuid.uuid4().hex[:8])
                u.set_password('1234')
                db.session.add(u); db.session.commit()
                flash(f'Creado. Clave: 1234', 'success')
                return redirect(url_for('admin.panel'))

    users = User.query.all()
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-6xl mx-auto'>
        <h1 class='text-2xl font-bold mb-6'>Panel Super Admin</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for cat, msg in messages %}
            <div class="bg-{{ 'green' if cat=='success' else 'red' }}-100 text-{{ 'green' if cat=='success' else 'red' }}-700 p-3 rounded mb-4">{{ msg }}</div>
            {% endfor %}
        {% endwith %}

        <!-- AGREGAR -->
        <div class="bg-white p-4 rounded-xl shadow mb-6">
            <h2 class="font-bold mb-2">Agregar Nuevo</h2>
            <form method="POST" class="flex gap-2">
                <input type="text" name="name" placeholder="Nombre" required class="flex-1 border p-2 rounded">
                <input type="email" name="email" placeholder="Email" required class="flex-1 border p-2 rounded">
                <button class="bg-indigo-600 text-white px-4 py-2 rounded font-bold">Crear</button>
            </form>
        </div>

        <!-- LISTA -->
        <div class="bg-white rounded-xl shadow overflow-x-auto">
        <table class='w-full text-sm'>
        <thead class='bg-slate-800 text-white'><tr>
            <th class='p-3 text-left'>Profesional</th>
            <th class='p-3 text-left'>Email</th>
            <th class='p-3 text-center'>Acciones</th>
        </tr></thead>
        <tbody>
        {% for u in users %}
        <tr class='border-b hover:bg-gray-50'>
            <td class='p-3 font-medium'>{{ u.name }}</td>
            <td class='p-3'>{{ u.email }}</td>
            <td class='p-3 text-center space-x-1 whitespace-nowrap'>
                <a href='{{ url_for('admin.view_user', uid=u.id) }}' class="bg-blue-500 text-white px-2 py-1 rounded text-xs">Detalles</a>
                <a href='{{ url_for('admin.login_as', uid=u.id) }}' class="bg-purple-500 text-white px-2 py-1 rounded text-xs">Entrar</a>
                <a href='{{ url_for('public.agenda', slug=u.slug) }}' target="_blank" class="bg-green-500 text-white px-2 py-1 rounded text-xs">Link</a>
            </td>
        </tr>
        {% endfor %}
        </tbody></table></div>
    </div>
    </body></html>
    """, users=users)

# --- 3. VER DETALLES ---
@admin.route('/super-admin/user/<int:uid>')
def view_user(uid):
    u = User.query.get_or_404(uid)
    total_turnos = Appointment.query.filter_by(professional_id=u.id).count()
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-2xl mx-auto'>
        <a href='{{ url_for('admin.panel') }}' class="text-indigo-600 text-sm">← Volver al listado</a>
        <div class="bg-white rounded-xl shadow p-6 mt-4">
            <h1 class='text-2xl font-bold mb-4'>{{ u.name }}</h1>
            <div class="space-y-2 text-sm">
                <p><b>Email:</b> {{ u.email }}</p>
                <p><b>Clave:</b> ****** <a href='{{ url_for('admin.reset_pwd', uid=u.id) }}' class="text-yellow-600">(Resetear a 1234)</a></p>
                <p><b>Total Turnos:</b> {{ total }}</p>
            </div>
            <hr class="my-4">
            <h2 class="font-bold mb-2">Links</h2>
            <div class="space-y-2">
                <a href='{{ url_for('public.agenda', slug=u.slug) }}' target="_blank" class="block bg-green-100 text-green-800 p-2 rounded text-xs">Link Público: /agenda/{{ u.slug }}</a>
            </div>
            <hr class="my-4">
            <div class="flex gap-2">
                <a href='{{ url_for('admin.edit_user', uid=u.id) }}' class="bg-blue-600 text-white px-4 py-2 rounded text-sm font-bold">Editar Datos</a>
                <a href='{{ url_for('admin.login_as', uid=u.id) }}' class="bg-purple-600 text-white px-4 py-2 rounded text-sm font-bold">Entrar como él</a>
            </div>
        </div>
    </div>
    </body></html>
    """, u=u, total=total_turnos)

# --- 4. EDITAR PROFESIONAL ---
@admin.route('/super-admin/edit/<int:uid>', methods=['GET', 'POST'])
def edit_user(uid):
    u = User.query.get_or_404(uid)
    if request.method == 'POST':
        u.name = request.form.get('name')
        u.email = request.form.get('email')
        db.session.commit()
        flash('Actualizado.', 'success')
        return redirect(url_for('admin.view_user', uid=uid))
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-md mx-auto bg-white p-6 rounded-xl shadow'>
        <h2 class='text-xl font-bold mb-4'>Editar Profesional</h2>
        <form method='POST'>
        <div class="mb-4"><label>Nombre</label><input type="text" name="name" value="{{ u.name }}" required class="w-full border p-2 rounded"></div>
        <div class="mb-4"><label>Email</label><input type="email" name="email" value="{{ u.email }}" required class="w-full border p-2 rounded"></div>
        <button class="w-full bg-indigo-600 text-white py-2 rounded font-bold">Guardar</button>
        </form>
        <a href='{{ url_for('admin.view_user', uid=u.id) }}' class="block text-center text-sm mt-4">Cancelar</a>
    </div>
    </body></html>
    """, u=u)

# --- 5. ENTRAR COMO (IMPERSONATE) ---
@admin.route('/super-admin/login-as/<int:uid>')
def login_as(uid):
    u = User.query.get_or_404(uid)
    login_user(u)
    flash(f'Has entrado como {u.name}', 'success')
    return redirect(url_for('dashboard.index'))

# --- 6. RESETEAR CLAVE ---
@admin.route('/super-admin/reset/<int:uid>')
def reset_pwd(uid):
    u = User.query.get_or_404(uid)
    u.set_password('1234')
    db.session.commit()
    flash(f'Clave de {u.name} reseteada a: 1234', 'success')
    return redirect(url_for('admin.view_user', uid=uid))
