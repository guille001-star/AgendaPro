from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import date, datetime, timedelta
import calendar
import csv
from io import StringIO
import json

dashboard = Blueprint('dashboard', __name__)

def get_local_date():
    return (datetime.utcnow() - timedelta(hours=3)).date()

@dashboard.route('/')
@login_required
def index():
    today = get_local_date()
    todays = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    upcoming = Appointment.query.filter(Appointment.professional_id == current_user.id, Appointment.status == 'reservado', Appointment.date > today).order_by(Appointment.date, Appointment.time).limit(10).all()
    enabled = AvailableDay.query.filter_by(professional_id=current_user.id).filter(AvailableDay.date >= today).all()
    enabled_dates = [d.date for d in enabled]
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(today.year, today.month)
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    next_weeks = cal.monthdatescalendar(next_year, next_month)
    next_name = (today.replace(day=28) + timedelta(days=10)).strftime('%B %Y')
    return render_template('dashboard/index.html', todays_appointments=todays, upcoming_appointments=upcoming, enabled_dates=enabled_dates, current_month_days=weeks, next_month_days=next_weeks, next_month_name=next_name, today=today)

@dashboard.route('/toggle-day/<date_str>', methods=['POST'])
@login_required
def toggle_day(date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d').date()
        ex = AvailableDay.query.filter_by(professional_id=current_user.id, date=d).first()
        if ex: db.session.delete(ex); act='removed'
        else:
            # Por defecto crea un día simple (el modo actual)
            db.session.add(AvailableDay(professional_id=current_user.id, date=d, start_time=datetime.strptime('09:00','%H:%M').time(), end_time=datetime.strptime('18:00','%H:%M').time(), slot_duration=30))
            act='added'
        db.session.commit()
        return jsonify({'status':'success', 'action':act})
    except Exception as e: return jsonify({'status':'error', 'msg':str(e)}), 500

# --- MODO SIMPLE (EXISTENTE - SIN CAMBIOS) ---
@dashboard.route('/set-hours-by-date/<date_str>', methods=['POST'])
@login_required
def set_hours(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if not day: return jsonify({'status':'error'}), 404
    data = request.get_json()
    try:
        day.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        day.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        day.slot_duration = int(data.get('slot_duration', 30))
        # Si usa modo simple, borramos los custom para evitar conflicto
        day.custom_slots = None
        db.session.commit()
        return jsonify({'status':'success'})
    except: return jsonify({'status':'error'}), 400

# --- MODO AVANZADO (NUEVO) ---
@dashboard.route('/save-custom-slots/<date_str>', methods=['POST'])
@login_required
def save_custom_slots(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if not day:
        return jsonify({'status':'error', 'msg':'Día no habilitado'}), 404
    
    data = request.get_json()
    # Esperamos: [{start: "08:00", dur: 40, public: true}, ...]
    slots = data.get('slots', [])
    
    if not slots:
        return jsonify({'status':'error', 'msg':'No hay turnos'}), 400

    # Guardamos JSON
    day.custom_slots = slots
    # Limpiamos modo simple para que no interfiera
    day.start_time = None
    day.end_time = None
    day.slot_duration = None
    
    db.session.commit()
    return jsonify({'status':'success'})

@dashboard.route('/get-day-config/<date_str>')
@login_required
def get_config(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if day:
        return jsonify({
            'start_time': day.start_time.strftime('%H:%M') if day.start_time else '09:00',
            'end_time': day.end_time.strftime('%H:%M') if day.end_time else '18:00',
            'slot_duration': day.slot_duration or 30,
            # Si tiene custom_slots, los enviamos para que el JS decida qué mostrar
            'custom_slots': day.custom_slots or []
        })
    return jsonify({'start_time':'09:00', 'end_time':'18:00', 'slot_duration':30, 'custom_slots':[]})

@dashboard.route('/live-data')
@login_required
def live_data():
    t = get_local_date()
    todays = Appointment.query.filter_by(professional_id=current_user.id, date=t, status='reservado').order_by(Appointment.time).all()
    up = Appointment.query.filter(Appointment.professional_id==current_user.id, Appointment.status=='reservado', Appointment.date > t).order_by(Appointment.date, Appointment.time).limit(4).all()
    return jsonify({'todays':[{'time':a.time.strftime('%H:%M'), 'name':a.client_name} for a in todays], 'upcoming':[{'date':a.date.strftime('%d/%m'), 'time':a.time.strftime('%H:%M'), 'name':a.client_name} for a in up]})

@dashboard.route('/export-csv')
@login_required
def export_csv():
    out = StringIO()
    w = csv.writer(out)
    w.writerow(['Fecha', 'Hora', 'Paciente', 'Telefono'])
    for a in Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.date.desc()).all():
        w.writerow([a.date.strftime('%d/%m/%Y'), a.time.strftime('%H:%M'), a.client_name, a.client_phone])
    out.seek(0)
    return Response(out, mimetype='text/csv', headers={'Content-Disposition':'attachment;filename=agenda.csv'})

@dashboard.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        price = request.form.get('price', 0, type=float)
        token = request.form.get('token', '').strip()
        public_key = request.form.get('public_key', '').strip()
        current_user.appointment_price = price
        current_user.mp_public_key = public_key if public_key else None
        if token: current_user.mp_access_token = token
        else: current_user.mp_access_token = None
        db.session.commit()
        flash('Configuracion actualizada.', 'success')
        return redirect(url_for('dashboard.settings'))

    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-xl mx-auto bg-white p-6 rounded-xl shadow'>
    <h2 class='text-xl font-bold mb-4'>Configuracion de Cobros</h2>
    <p class='text-xs text-gray-500 mb-4'>Deja los campos vacíos para desactivar pagos.</p>
    <form method='POST'>
    <div class='mb-4'><label>Precio ($)</label><input type='number' step='0.01' name='price' value='{{ current_user.appointment_price or "" }}' class='w-full border p-2 rounded'></div>
    <div class='mb-4'><label>Access Token</label><input type='text' name='token' placeholder='Vacío=borrar' value='{{ current_user.mp_access_token or "" }}' class='w-full border p-2 rounded text-xs font-mono'></div>
    <div class='mb-4'><label>Public Key</label><input type='text' name='public_key' placeholder='Vacío=borrar' value='{{ current_user.mp_public_key or "" }}' class='w-full border p-2 rounded text-xs font-mono'></div>
    <button class='w-full bg-indigo-600 text-white py-2 rounded font-bold'>Guardar</button>
    </form>
    <a href="{{ url_for('dashboard.index') }}" class="block text-center text-sm mt-4">Volver</a>
    </div></body></html>
    """)
