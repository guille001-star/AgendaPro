from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
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

@dashboard.route('/')
@login_required
def index():
    today = get_local_date()
    todays_appointments = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    upcoming_appointments = Appointment.query.filter(Appointment.professional_id == current_user.id, Appointment.status == 'reservado', Appointment.date > today).order_by(Appointment.date, Appointment.time).limit(10).all()
    enabled_days = AvailableDay.query.filter_by(professional_id=current_user.id).filter(AvailableDay.date >= today).all()
    enabled_dates = [d.date for d in enabled_days]
    cal = calendar.Calendar(firstweekday=6) 
    current_month_days = cal.monthdatescalendar(today.year, today.month)
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    next_month_days = cal.monthdatescalendar(next_year, next_month)
    next_month_date = today.replace(day=28) + timedelta(days=10)
    next_month_name = next_month_date.strftime('%B %Y')
    return render_template('dashboard/index.html', todays_appointments=todays_appointments, upcoming_appointments=upcoming_appointments, enabled_dates=enabled_dates, current_month_days=current_month_days, next_month_days=next_month_days, next_month_name=next_month_name, today=today)

@dashboard.route('/toggle-day/<date_str>', methods=['POST'])
@login_required
def toggle_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
        if existing:
            db.session.delete(existing)
            action = 'removed'
        else:
            new_day = AvailableDay(
                professional_id=current_user.id, 
                date=date_obj,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('18:00', '%H:%M').time(),
                slot_duration=30
            )
            db.session.add(new_day)
            action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@dashboard.route('/get-day-config/<date_str>')
@login_required
def get_day_config(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if day:
        return jsonify({
            'status': 'found',
            'start_time': day.start_time.strftime('%H:%M') if day.start_time else '09:00',
            'end_time': day.end_time.strftime('%H:%M') if day.end_time else '18:00',
            'slot_duration': day.slot_duration or 30
        })
    return jsonify({'status': 'not_found'})

@dashboard.route('/set-hours-by-date/<date_str>', methods=['POST'])
@login_required
def set_hours_by_date(date_str):
    day = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_str).first()
    if not day:
        return jsonify({'status': 'error', 'message': 'Día no habilitado'}), 404
    
    data = request.get_json()
    start_str = data.get('start_time')
    end_str = data.get('end_time')
    
    # CORRECCIÓN: Forma correcta de leer el entero
    try:
        duration = int(data.get('slot_duration', 30))
    except:
        duration = 30
    
    if start_str and end_str:
        try:
            day.start_time = datetime.strptime(start_str, '%H:%M').time()
            day.end_time = datetime.strptime(end_str, '%H:%M').time()
            day.slot_duration = duration
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
    return jsonify({'status': 'error', 'message': 'Datos incompletos'}), 400

@dashboard.route('/live-data')
@login_required
def live_data():
    today = get_local_date()
    todays = Appointment.query.filter_by(professional_id=current_user.id, date=today, status='reservado').order_by(Appointment.time).all()
    upcoming = Appointment.query.filter(Appointment.professional_id==current_user.id, Appointment.status == 'reservado', Appointment.date > today).order_by(Appointment.date, Appointment.time).limit(4).all()
    return jsonify({
        'todays': [{'id': a.id, 'time': a.time.strftime('%H:%M'), 'name': a.client_name, 'phone': a.client_phone} for a in todays],
        'upcoming': [{'id': a.id, 'date': a.date.strftime('%d/%m'), 'time': a.time.strftime('%H:%M'), 'name': a.client_name} for a in upcoming]
    })

@dashboard.route('/export-csv')
@login_required
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Hora', 'Paciente', 'Telefono', 'Email', 'Estado'])
    appointments = Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.date.desc()).all()
    for apt in appointments:
        writer.writerow([apt.date.strftime('%d/%m/%Y'), apt.time.strftime('%H:%M'), apt.client_name, apt.client_phone, apt.client_email or '', apt.status])
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=agenda.csv'})

# --- CONFIGURACIÓN DE PAGOS ---
@dashboard.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Guardar datos
        current_user.mp_access_token = request.form.get('mp_access_token')
        current_user.mp_public_key = request.form.get('mp_public_key')
        price_str = request.form.get('appointment_price', '0').replace(',', '.')
        try:
            current_user.appointment_price = float(price_str)
        except:
            current_user.appointment_price = 0.0
        
        db.session.commit()
        flash('Configuración guardada.', 'success')
        return redirect(url_for('dashboard.settings'))
        
    return render_template('dashboard/settings.html')

# --- CONFIGURACIÓN DE PAGOS ---
@dashboard.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        price = request.form.get('price', 0, type=float)
        token = request.form.get('token')
        public_key = request.form.get('public_key')
        
        current_user.appointment_price = price
        current_user.mp_public_key = public_key
        if token: # Solo actualizar si se proporciona uno nuevo
            current_user.mp_access_token = token
        db.session.commit()
        flash('Configuracion guardada.', 'success')
        return redirect(url_for('dashboard.settings'))
        
    return render_template_string("""
    <html><head><meta charset='UTF-8'><script src='https://cdn.tailwindcss.com'></script></head>
    <body class='bg-gray-100 p-8'>
    <div class='max-w-xl mx-auto bg-white p-6 rounded-xl shadow'>
    <h2 class='text-xl font-bold mb-4'>Configuracion de Cobros</h2>
    <form method='POST'>
    <div class='mb-4'><label>Precio del Turno ($)</label><input type='number' step='0.01' name='price' value='{{ current_user.appointment_price or "" }}' class='w-full border p-2 rounded'></div>
    <div class='mb-4'><label>Access Token (MP)</label><input type='text' name='token' placeholder='TEST-...' class='w-full border p-2 rounded text-xs font-mono'>
    <p class='text-xs text-gray-400 mt-1'>Tu token actual está encriptado. Ingrese uno nuevo solo si desea cambiarlo.</p></div>
    <div class='mb-4'><label>Public Key (MP)</label><input type='text' name='public_key' value='{{ current_user.mp_public_key or "" }}' class='w-full border p-2 rounded text-xs font-mono'></div>
    <button class='w-full bg-indigo-600 text-white py-2 rounded font-bold'>Guardar</button>
    </form></div></body></html>
    """)
