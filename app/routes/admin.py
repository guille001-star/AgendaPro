from flask import Blueprint, render_template_string, request, flash, redirect, url_for
from app import db
from app.models.user import User

admin = Blueprint('admin', __name__)

CLAVE_MAESTRA = "agendapromaster2026"

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
    <input type='password' name='clave' placeholder='Clave Maestra' required class='w-full border p-2 rounded mb-4'>
    <button class='w-full bg-red-500 text-white py-2 rounded font-bold'>Acceder</button>
    </form></div></body></html>
    """)

@admin.route('/super-admin/panel')
def panel():
    users = User.query.all()
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-5xl mx-auto'>
        <div class='flex justify-between items-center mb-6'>
            <h1 class='text-2xl font-bold'>Panel Super Admin</h1>
            <a href='/' class='text-red-600 font-bold text-sm'>Salir</a>
        </div>
        <div class='bg-white shadow rounded-xl overflow-hidden'>
        <table class='w-full text-sm'>
        <thead class='bg-slate-800 text-white'><tr><th class='p-3 text-left'>Nombre</th><th class='p-3 text-left'>Email</th><th class='p-3'>Link Público</th><th class='p-3'>Resetear Clave</th></tr></thead>
        <tbody>
        {% for u in users %}
        <tr class='border-b hover:bg-gray-50'>
            <td class='p-3 font-medium'>{{ u.name }}</td>
            <td class='p-3'>{{ u.email }}</td>
            <td class='p-3 text-xs text-indigo-600'>/agenda/{{ u.slug }}</td>
            <td class='p-3 text-center'><a href='{{ url_for('admin.reset_pwd', uid=u.id) }}' class='bg-yellow-100 text-yellow-700 px-2 py-1 rounded'>Resetear a 1234</a></td>
        </tr>
        {% endfor %}
        </tbody></table></div>
    </div>
    </body></html>
    """, users=users)

@admin.route('/super-admin/reset/<int:uid>')
def reset_pwd(uid):
    u = User.query.get(uid)
    if u:
        u.set_password('1234')
        db.session.commit()
        flash(f'Clave de {u.name} reseteada a: 1234', 'success')
    return redirect(url_for('admin.panel'))
