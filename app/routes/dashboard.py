from flask import Blueprint, render_template_string, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import date, datetime, timedelta
import calendar
import csv
from io import StringIO

dashboard = Blueprint('dashboard', __name__)

def get_local_date():
    return (datetime.utcnow() - timedelta(hours=3)).date()

# HTML CON MODAL DE HORARIOS
TPL_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { font-family: 'Segoe UI', sans-serif; }</style>
</head>
<body class="bg-slate-50">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        <div class="fixed top-0 right-0 m-4 z-50">
            {% for category, message in messages %}
            <div class="bg-{{ 'red' if category == 'danger' else 'green' }}-100 border-l-4 border-{{ 'red' if category == 'danger' else 'green' }}-500 text-{{ 'red' if category == 'danger' else 'green' }}-700 p-2 rounded shadow mb-2">{{ message }}</div>
            {% endfor %}
        </div>
        {% endif %}
    {% endwith %}

    <div class="bg-slate-100 min-h-screen pb-10">
        <header class="bg-slate-900 text-white py-4 px-6 flex justify-between items-center sticky top-0 z-40 border-b-4 border-indigo-600">
            <div>
                <p class="text-xs text-slate-400 uppercase">Panel de Control</p>
                <h1 class="text-xl font-bold">{{ current_user.name }}</h1>
            </div>
            <div class="flex items-center gap-2">
                <a href="{{ url_for('auth.change_password') }}" class="text-xs bg-slate-700 px-3 py-2 rounded">Clave</a>
                <a href="{{ url_for('dashboard.export_csv') }}" class="text-xs bg-slate-700 px-3 py-2 rounded">Exportar</a>
                <a href="{{ url_for('auth.logout') }}" class="text-xs bg-red-600 px-3 py-2 rounded">Salir</a>
            </div>
        </header>

        <div class="flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto">
            <div class="lg:w-2/3 bg-white rounded-xl shadow-lg p-6">
                <h2 class="text-lg font-bold text-slate-800 mb-4">Calendario (Clic para activar/configurar)</h2>
                
                <h3 class="text-center font-bold text-slate-700 mb-2 uppercase">{{ today.strftime('%B %Y') }}</h3>
                <div class="grid grid-cols-7 gap-1 text-center text-xs font-bold text-slate-500 mb-2">
                    <div>Dom</div><div>Lun</div><div>Mar</div><div>Mie</div><div>Jue</div><div>Vie</div><div>Sab</div>
                </div>
                <div class="grid grid-cols-7 gap-1">
                    {% for week in current_month_days %}
                        {% for day in week %}
                            {% if day.month == today.month %}
                            <div onclick="handleDayClick('{{ day }}')" id="day-{{ day }}" 
                                class="cursor-pointer p-2 rounded text-center text-sm font-medium transition-all
                                {% if day < today %} text-slate-300 bg-slate-50 cursor-not-allowed
                                {% elif day in enabled_dates %} bg-green-500 text-white hover:bg-green-600 shadow-md
                                {% else %} bg-slate-100 text-slate-700 hover:bg-slate-200 {% endif %}">
                                {{ day.day }}
                            </div>
                            {% else %}<div class="p-2"></div>{% endif %}
                        {% endfor %}
                    {% endfor %}
                </div>
            </div>

            <div class="lg:w-1/3 space-y-6">
                <div class="bg-white p-6 rounded-xl shadow-lg">
                    <h3 class="font-bold text-slate-800 mb-2">Turnos de Hoy</h3>
                    <span id="today-badge" class="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-1 rounded-full">{{ todays_appointments|length }}</span>
                    <ul id="list-today" class="space-y-2 text-sm mt-2">
                        {% for apt in todays_appointments %}
                        <li class="flex justify-between p-2 bg-slate-50 rounded">
                            <span class="font-bold text-indigo-600">{{ apt.time.strftime('%H:%M') }}</span>
                            <span>{{ apt.client_name }}</span>
                        </li>
                        {% else %}<li class="text-slate-400 text-center py-2">Sin turnos.</li>{% endfor %}
                    </ul>
                </div>
                <div class="bg-white p-6 rounded-xl shadow-lg text-center">
                    <h3 class="font-bold text-slate-800 mb-3">Tu Link</h3>
                    <input type="text" readonly value="{{ request.host_url }}agenda/{{ current_user.slug }}" id="myLink" class="w-full bg-slate-100 text-center text-xs p-2 rounded mb-3 border">
                    <button onclick="copyLink()" class="bg-indigo-600 text-white text-sm px-4 py-2 rounded w-full font-bold hover:bg-indigo-700">Copiar Link</button>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ request.host_url }}agenda/{{ current_user.slug }}" class="mx-auto rounded mt-4">
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL PARA DEFINIR HORARIOS -->
    <div id="hours-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl w-full max-w-sm">
            <h3 class="text-lg font-bold mb-4 text-slate-800">Configurar Horario</h3>
            <p class="text-sm text-slate-600 mb-4">Fecha: <span id="modal-date" class="font-bold"></span></p>
            <form id="hours-form" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-slate-700">Hora Inicio</label>
                    <input type="time" id="start-time" class="w-full border p-2 rounded" value="09:00">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">Hora Fin</label>
                    <input type="time" id="end-time" class="w-full border p-2 rounded" value="18:00">
                </div>
                <div class="flex gap-2 mt-4">
                    <button type="submit" class="flex-1 bg-indigo-600 text-white py-2 rounded font-bold">Guardar</button>
                    <button type="button" onclick="closeModal()" class="flex-1 bg-slate-200 py-2 rounded">Cancelar</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentDate = null;
        
        function handleDayClick(d) {
            const el = document.getElementById('day-'+d);
            if(el.classList.contains('bg-slate-100')){
                // Dia gris: Activar y luego abrir modal
                fetch('/dashboard/toggle-day/'+d, {method:'POST'}).then(r=>r.json()).then(data => {
                    if(data.status==='success'){
                        el.classList.remove('bg-slate-100','text-slate-700');
                        el.classList.add('bg-green-500','text-white','shadow-md');
                        openModal(d);
                    }
                });
            } else if(el.classList.contains('bg-green-500')){
                // Dia verde: Solo abrir modal
                openModal(d);
            }
        }

        function openModal(d) {
            currentDate = d;
            document.getElementById('modal-date').innerText = d;
            // Cargar config existente
            fetch('/dashboard/get-config/'+d).then(r=>r.json()).then(data => {
                document.getElementById('start-time').value = data.start || '09:00';
                document.getElementById('end-time').value = data.end || '18:00';
            });
            document.getElementById('hours-modal').classList.remove('hidden');
            document.getElementById('hours-modal').classList.add('flex');
        }

        function closeModal() {
            document.getElementById('hours-modal').classList.add('hidden');
            document.getElementById('hours-modal').classList.remove('flex');
        }

        document.getElementById('hours-form').addEventListener('submit', function(e){
            e.preventDefault();
            fetch('/dashboard/set-hours/'+currentDate, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    start: document.getElementById('start-time').value,
                    end: document.getElementById('end-time').value
                })
            }).then(r=>r.json()).then(res => {
                if(res.status==='success'){
                    alert('Horarios guardados');
                    closeModal();
                } else {
                    alert('Error');
                }
            });
        });

        function copyLink() { var c = document.getElementById("myLink"); c.select(); document.execCommand("copy"); alert("Copiado!"); }
        
        setInterval(function(){
            fetch('/dashboard/live-data').then(r=>r.json()).then(d=>{
                document.getElementById('today-badge').innerText=d.todays.length;
                document.getElementById('list-today').innerHTML = d.todays.map(a=>`<li class="flex justify-between p-2 bg-slate-50 rounded"><span class="font-bold text-indigo-600">${a.time}</span><span>${a.name}</span></li>`).join('') || '<li class="text-slate-400 text-center py-2">Sin turnos.</li>';
            });
        }, 5000);
    </script>
</body>
</html>
"""

@dashboard.route('/')
@login_required
def index():
    today = get_local_date()
    todays_appointments = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    enabled_days = AvailableDay.query.filter_by(professional_id=current_user.id).filter(AvailableDay.date >= today).all()
    enabled_dates = [d.date for d in enabled_days]
    cal = calendar.Calendar(firstweekday=6)
    current_month_days = cal.monthdatescalendar(today.year, today.month)
    return render_template_string(TPL_DASHBOARD, todays_appointments=todays_appointments, enabled_dates=enabled_dates, current_month_days=current_month_days, today=today)

@dashboard.route('/toggle-day/<date_str>', methods=['POST'])
@login_required
def toggle_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
        if existing:
            db.session.delete(existing); action = 'removed'
        else:
            new_day = AvailableDay(professional_id=current_user.id, date=date_obj)
            db.session.add(new_day); action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        return jsonify({'status': 'error'}), 500

@dashboard.route('/get-config/<date_str>')
@login_required
def get_config(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if day:
        return jsonify({'start': day.start_time.strftime('%H:%M') if day.start_time else '09:00', 'end': day.end_time.strftime('%H:%M') if day.end_time else '18:00'})
    return jsonify({'start': '09:00', 'end': '18:00'})

@dashboard.route('/set-hours/<date_str>', methods=['POST'])
@login_required
def set_hours(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if not day:
        return jsonify({'status': 'error'}), 404
    data = request.get_json()
    try:
        day.start_time = datetime.strptime(data['start'], '%H:%M').time()
        day.end_time = datetime.strptime(data['end'], '%H:%M').time()
        db.session.commit()
        return jsonify({'status': 'success'})
    except:
        return jsonify({'status': 'error'}), 400

@dashboard.route('/live-data')
@login_required
def live_data():
    today = get_local_date()
    todays = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    return jsonify({'todays': [{'id': a.id, 'time': a.time.strftime('%H:%M'), 'name': a.client_name} for a in todays]})

@dashboard.route('/export-csv')
@login_required
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Hora', 'Paciente', 'Telefono', 'Email', 'Estado'])
    for apt in Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.date.desc()).all():
        writer.writerow([apt.date.strftime('%d/%m/%Y'), apt.time.strftime('%H:%M'), apt.client_name, apt.client_phone, apt.client_email or '', apt.status])
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=agenda.csv'})
