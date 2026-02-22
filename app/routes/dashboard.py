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
    
    # DEBUG: Contadores absolutos
    total_en_db = Appointment.query.filter_by(professional_id=current_user.id).count()
    ultimos_5 = Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.created_at.desc()).limit(5).all()
    
    todays_appointments = Appointment.query.filter_by(
        professional_id=current_user.id, 
        date=today, 
        status='reservado'
    ).order_by(Appointment.time).all()
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.professional_id == current_user.id,
        Appointment.status == 'reservado',
        Appointment.date > today
    ).order_by(Appointment.date, Appointment.time).limit(4).all()
    
    enabled_days = AvailableDay.query.filter_by(
        professional_id=current_user.id
    ).filter(AvailableDay.date >= today).all()
    
    enabled_dates = [d.date for d in enabled_days]
    
    cal = calendar.Calendar(firstweekday=6) 
    current_month_days = cal.monthdatescalendar(today.year, today.month)
    
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    next_month_days = cal.monthdatescalendar(next_year, next_month)
    
    next_month_date = today.replace(day=28) + timedelta(days=10)
    next_month_name = next_month_date.strftime('%B %Y')
    
    return render_template('dashboard/index.html', 
                           todays_appointments=todays_appointments,
                           upcoming_appointments=upcoming_appointments,
                           enabled_dates=enabled_dates,
                           current_month_days=current_month_days,
                           next_month_days=next_month_days,
                           next_month_name=next_month_name,
                           today=today,
                           # Variables Debug
                           debug_total=total_en_db,
                           debug_ultimos=ultimos_5,
                           debug_user_id=current_user.id)

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
            new_day = AvailableDay(professional_id=current_user.id, date=date_obj,
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('18:00', '%H:%M').time())
            db.session.add(new_day)
            action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
