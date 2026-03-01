from flask import Blueprint, render_template_string, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import date, datetime, timedelta
import calendar
import csv
from io import StringIO
from flask import Response

dashboard = Blueprint('dashboard', __name__)

def get_local_date():
    return (datetime.utcnow() - timedelta(hours=3)).date()

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgendaPro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { font-family: 'Segoe UI', sans-serif; }</style>
</head>
<body class="bg-slate-50">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        <div class="fixed top-0 right-0 m-4 z-50">
            {% for category, message in messages %}
            <div class="bg-{{ 'red' if category == 'danger' else 'green' }}-100 border-l-4 border-{{ 'red' if category == 'danger' else 'green' }}-500 text-{{ 'red' if category == 'danger' else 'green' }}-700 p-2 rounded shadow mb-2">
                <p>{{ message }}</p>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    {% endwith %}

    <div class="bg-slate-100 min-h-screen pb-10">
        <header class="bg-slate-900 text-white py-4 px-6 flex justify-between items-center sticky top-0 z-40 border-b-4 border-indigo-600">
            <div>
                <p class="text-xs text-slate-400 uppercase tracking-wider">Panel de Control</p>
                <h1 class="text-xl font-bold">{{ current_user.name }}</h1>
            </div>
            <div class="flex items-center gap-2 flex-wrap justify-end">
                <a href="{{ url_for('auth.change_password') }}" class="text-xs bg-slate-700 px-3 py-2 rounded hover:bg-slate-600">Cambiar Clave</a>
                <a href="{{ url_for('dashboard.export_csv') }}" class="text-xs bg-slate-700 px-3 py-2 rounded hover:bg-slate-600">Exportar</a>
                <a href="{{ url_for('auth.logout') }}" class="text-xs bg-red-600 px-3 py-2 rounded hover:bg-red-700">Salir</a>
            </div>
        </header>

        <div class="flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto">
            <div class="lg:w-2/3 space-y-6">
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <h2 class="text-lg font-bold text-slate-800 mb-4">Calendario</h2>
                    <h3 class="text-center font-bold text-slate-700 mb-2 uppercase tracking-wider">{{ today.strftime('%B %Y') }}</h3>
                    <div class="grid grid-cols-7 gap-1 text-center text-xs font-bold text-slate-500 mb-2">
                        <div>Dom</div><div>Lun</div><div>Mar</div><div>Mie</div><div>Jue</div><div>Vie</div><div>Sab</div>
                    </div>
                    <div class="grid grid-cols-7 gap-1">
                        {% for week in current_month_days %}
                            {% for day in week %}
                                {% if day.month == today.month %}
                                <div onclick="handleDayClick('{{ day }}')" id="day-{{ day }}" class="cursor-pointer p-2 rounded text-center transition-all duration-200 text-sm font-medium
                                    {% if day < today %} text-slate-300 cursor-not-allowed bg-slate-50 {% endif %}
                                    {% if day >= today %}
                                        {% if day in enabled_dates %} bg-green-500 text-white hover:bg-green-600 shadow-md transform scale-105 {% else %} bg-slate-100 text-slate-700 hover:bg-slate-200 {% endif %}
                                    {% endif %}
                                "><span>{{ day.day }}</span></div>
                                {% else %}
                                <div class="p-2 text-slate-200 text-sm"></div>
                                {% endif %}
                            {% endfor %}
                        {% endfor %}
                    </div>
                    
                    <h3 class="text-center font-bold text-slate-700 mb-2 mt-8 uppercase tracking-wider">{{ next_month_name }}</h3>
                    <div class="grid grid-cols-7 gap-1 text-center text-xs font-bold text-slate-500 mb-2">
                        <div>Dom</div><div>Lun</div><div>Mar</div><div>Mie</div><div>Jue</div><div>Vie</div><div>Sab</div>
                    </div>
                    <div class="grid grid-cols-7 gap-1">
                        {% for week in next_month_days %}
                            {% for day in week %}
                                {% if day.month != today.month %}
                                <div onclick="handleDayClick('{{ day }}')" id="day-{{ day }}" class="cursor-pointer p-2 rounded text-center transition-all duration-200 text-sm font-medium
                                    {% if day in enabled_dates %} bg-green-500 text-white hover:bg-green-600 shadow-md transform scale-105 {% else %} bg-slate-100 text-slate-700 hover:bg-slate-200 {% endif %}
                                "><span>{{ day.day }}</span></div>
                                {% else %}
                                <div class="p-2 text-slate-200 text-sm"></div>
                                {% endif %}
                            {% endfor %}
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div class="lg:w-1/3 space-y-6">
                <div class="bg-white p-6 rounded-xl shadow-lg">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="font-bold text-slate-800">Turnos de Hoy</h3>
                        <span id="today-badge" class="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-1 rounded-full">{{ todays_appointments|length }}</span>
                    </div>
                    <ul id="list-today" class="space-y-3 text-sm max-h-40 overflow-y-auto">
                        {% for apt in todays_appointments %}
                        <li class="flex justify-between items-center p-2 bg-slate-50 rounded">
                            <span class="font-bold text-indigo-600">{{ apt.time.strftime('%H:%M') }}</span>
                            <span class="font-medium">{{ apt.client_name }}</span>
                        </li>
                        {% else %}
                        <li class="text-slate-400 text-center py-4">Sin turnos hoy.</li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="bg-white p-6 rounded-xl shadow-lg">
                    <h3 class="font-bold text-slate-800 mb-4">Próximos Turnos</h3>
                    <ul id="list-upcoming" class="space-y-3 text-sm max-h-60 overflow-y-auto">
                        {% for apt in upcoming_appointments %}
                        <li class="flex justify-between items-center p-2 bg-slate-50 rounded">
                            <div>
                                <span class="font-bold text-slate-700">{{ apt.client_name }}</span>
                                <span class="block text-xs text-slate-500">{{ apt.date|format_date }} - {{ apt.time.strftime('%H:%M') }}</span>
                            </div>
                        </li>
                        {% else %}
                        <li class="text-slate-400 text-center py-4">Sin turnos futuros.</li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="bg-white p-6 rounded-xl shadow-lg text-center">
                    <h3 class="font-bold text-slate-800 mb-3">Tu Link y QR</h3>
                    <input type="text" readonly value="{{ request.host_url }}agenda/{{ current_user.slug }}" class="w-full bg-slate-100 text-center text-xs p-2 rounded mb-3 border" id="myLink">
                    <button onclick="copyLink()" class="bg-indigo-600 text-white text-sm px-4 py-2 rounded w-full font-bold hover:bg-indigo-700 mb-4">Copiar Link</button>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ request.host_url }}agenda/{{ current_user.slug }}" alt="QR" class="mx-auto rounded">
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL DE HORARIOS -->
    <div id="hours-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl w-full max-w-sm">
            <h3 class="text-lg font-bold mb-4 text-slate-800">Configurar Horario</h3>
            <p class="text-sm text-slate-600 mb-4">Fecha: <span id="modal-date" class="font-bold"></span></p>
            <form id="hours-form" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-slate-700">Hora Inicio</label>
                    <input type="time" id="start-time" name="start_time" class="w-full border border-slate-300 p-2 rounded">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">Hora Fin</label>
                    <input type="time" id="end-time" name="end_time" class="w-full border border-slate-300 p-2 rounded">
                </div>
                <div class="flex gap-2 mt-4">
                    <button type="submit" class="flex-1 bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700">Guardar</button>
                    <button type="button" onclick="hideHoursModal()" class="flex-1 bg-slate-200 py-2 rounded hover:bg-slate-300">Cancelar</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentEditingDate = null;

        function handleDayClick(dateStr) {
            const el = document.getElementById('day-' + dateStr);
            if(el.classList.contains('bg-green-500')){
                showHoursModal(dateStr);
            } else {
                toggleDay(dateStr);
            }
        }

        function toggleDay(dateStr) {
            fetch('/dashboard/toggle-day/' + dateStr, {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success'){
                    const el = document.getElementById('day-' + dateStr);
                    if(data.action === 'added'){
                        el.classList.remove('bg-slate-100', 'text-slate-700', 'hover:bg-slate-200');
                        el.classList.add('bg-green-500', 'text-white', 'hover:bg-green-600', 'shadow-md', 'transform', 'scale-105');
                        showHoursModal(dateStr);
                    } else {
                        el.classList.add('bg-slate-100', 'text-slate-700', 'hover:bg-slate-200');
                        el.classList.remove('bg-green-500', 'text-white', 'hover:bg-green-600', 'shadow-md', 'transform', 'scale-105');
                    }
                }
            });
        }

        function showHoursModal(dateStr) {
            currentEditingDate = dateStr;
            document.getElementById('modal-date').innerText = dateStr;
            document.getElementById('start-time').value = '09:00';
            document.getElementById('end-time').value = '18:00';
            
            fetch('/dashboard/get-day-config/' + dateStr)
            .then(r => r.json())
            .then(data => {
                if(data.status === 'found'){
                    document.getElementById('start-time').value = data.start_time;
                    document.getElementById('end-time').value = data.end_time;
                }
            });
            
            const modal = document.getElementById('hours-modal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }

        function hideHoursModal() {
            const modal = document.getElementById('hours-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }

        document.getElementById('hours-form').addEventListener('submit', function(e){
            e.preventDefault();
            fetch('/dashboard/set-hours-by-date/' + currentEditingDate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    start_time: document.getElementById('start-time').value, 
                    end_time: document.getElementById('end-time').value 
                })
            })
            .then(r => r.json())
            .then(res => {
                if(res.status === 'success'){
                    alert('Horarios guardados');
                    hideHoursModal();
                } else {
                    alert('Error: ' + res.message);
                }
            });
        });

        function copyLink() {
            var copyText = document.getElementById("myLink"); copyText.select(); document.execCommand("copy"); alert("Copiado!");
        }
        
        setInterval(function() {
            fetch('/dashboard/live-data?v=' + new Date().getTime())
            .then(response => response.json())
            .then(data => {
                document.getElementById('today-badge').innerText = data.todays.length;
                const listToday = document.getElementById('list-today');
                if(data.todays.length > 0){ listToday.innerHTML = data.todays.map(apt => `<li class="flex justify-between items-center p-2 bg-slate-50 rounded"><span class="font-bold text-indigo-600">${apt.time}</span><span class="font-medium">${apt.name}</span></li>`).join(''); } 
                else { listToday.innerHTML = '<li class="text-slate-400 text-center py-4">Sin turnos hoy.</li>'; }
                const listUpcoming = document.getElementById('list-upcoming');
                if(data.upcoming.length > 0){ listUpcoming.innerHTML = data.upcoming.map(apt => `<li class="flex justify-between items-center p-2 bg-slate-50 rounded"><div><span class="font-bold text-slate-700">${apt.name}</span><span class="block text-xs text-slate-500">${apt.date} - ${apt.time}</span></div></li>`).join(''); } 
                else { listUpcoming.innerHTML = '<li class="text-slate-400 text-center py-4">Sin turnos futuros.</li>'; }
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
    upcoming_appointments = Appointment.query.filter(Appointment.professional_id==current_user.id, Appointment.status == 'reservado', Appointment.date > today).order_by(Appointment.date, Appointment.time).limit(10).all()
    enabled_days = AvailableDay.query.filter_by(professional_id=current_user.id).filter(AvailableDay.date >= today).all()
    enabled_dates = [d.date for d in enabled_days]
    cal = calendar.Calendar(firstweekday=6) 
    current_month_days = cal.monthdatescalendar(today.year, today.month)
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    next_month_days = cal.monthdatescalendar(next_year, next_month)
    next_month_date = today.replace(day=28) + timedelta(days=10)
    next_month_name = next_month_date.strftime('%B %Y')
    return render_template_string(HTML_DASHBOARD, todays_appointments=todays_appointments, upcoming_appointments=upcoming_appointments, enabled_dates=enabled_dates, current_month_days=current_month_days, next_month_days=next_month_days, next_month_name=next_month_name, today=today)

@dashboard.route('/toggle-day/<date_str>', methods=['POST'])
@login_required
def toggle_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
        if existing:
            db.session.delete(existing); action = 'removed'
        else:
            new_day = AvailableDay(professional_id=current_user.id, date=date_obj, start_time=datetime.strptime('09:00', '%H:%M').time(), end_time=datetime.strptime('18:00', '%H:%M').time())
            db.session.add(new_day); action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@dashboard.route('/set-hours-by-date/<date_str>', methods=['POST'])
@login_required
def set_hours_by_date(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if not day: return jsonify({'status': 'error', 'message': 'Dia no habilitado'}), 404
    data = request.get_json()
    if data.get('start_time') and data.get('end_time'):
        try:
            day.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            day.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            db.session.commit()
            return jsonify({'status': 'success'})
        except: return jsonify({'status': 'error'}), 400
    return jsonify({'status': 'error'}), 400

@dashboard.route('/get-day-config/<date_str>')
@login_required
def get_day_config(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if day:
        return jsonify({'status': 'found', 'start_time': day.start_time.strftime('%H:%M') if day.start_time else '09:00', 'end_time': day.end_time.strftime('%H:%M') if day.end_time else '18:00'})
    return jsonify({'status': 'not_found'})

@dashboard.route('/live-data')
@login_required
def live_data():
    today = get_local_date()
    todays = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    upcoming = Appointment.query.filter(Appointment.professional_id==current_user.id, Appointment.status == 'reservado', Appointment.date > today).order_by(Appointment.date, Appointment.time).limit(4).all()
    return jsonify({'todays': [{'id': a.id, 'time': a.time.strftime('%H:%M'), 'name': a.client_name} for a in todays], 'upcoming': [{'id': a.id, 'date': a.date.strftime('%d/%m'), 'time': a.time.strftime('%H:%M'), 'name': a.client_name} for a in upcoming]})

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
