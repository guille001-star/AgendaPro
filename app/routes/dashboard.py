from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import date, datetime, timedelta
from sqlalchemy import or_

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    today = date.today()
    
    # Turnos de HOY
    todays_appointments = Appointment.query.filter_by(
        professional_id=current_user.id, 
        date=today, 
        status='reservado'
    ).order_by(Appointment.time).all()
    
    # Próximos turnos (LIMITADO A 4)
    upcoming_appointments = Appointment.query.filter(
        Appointment.professional_id == current_user.id,
        Appointment.status == 'reservado',
        Appointment.date > today
    ).order_by(Appointment.date, Appointment.time).limit(4).all()
    
    # Días disponibles futuros
    enabled_days = AvailableDay.query.filter_by(
        professional_id=current_user.id
    ).filter(AvailableDay.date >= today).order_by(AvailableDay.date).limit(30).all()
    
    # Calendario completo (para la pestaña)
    calendar_days = AvailableDay.query.filter_by(
        professional_id=current_user.id
    ).filter(AvailableDay.date >= today - timedelta(days=30)).order_by(AvailableDay.date).all()
    
    return render_template('dashboard/index.html', 
                           todays_appointments=todays_appointments,
                           upcoming_appointments=upcoming_appointments,
                           enabled_days=enabled_days,
                           calendar_days=calendar_days,
                           today=today)

@dashboard.route('/available-day', methods=['POST'])
@login_required
def add_available_day():
    date_str = request.form.get('date')
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
        if existing:
            flash('Este día ya está habilitado.', 'error')
        else:
            new_day = AvailableDay(professional_id=current_user.id, date=date_obj)
            db.session.add(new_day)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('dashboard.index'))

@dashboard.route('/set-hours/<int:day_id>', methods=['POST'])
@login_required
def set_hours(day_id):
    day = AvailableDay.query.get_or_404(day_id)
    if day.professional_id != current_user.id:
        return redirect(url_for('dashboard.index'))
    
    start_str = request.form.get('start_time')
    end_str = request.form.get('end_time')
    
    if start_str and end_str:
        day.start_time = datetime.strptime(start_str, '%H:%M').time()
        day.end_time = datetime.strptime(end_str, '%H:%M').time()
        db.session.commit()
        
    return redirect(url_for('dashboard.index'))

@dashboard.route('/toggle-availability/<int:day_id>', methods=['POST'])
@login_required
def toggle_availability(day_id):
    day = AvailableDay.query.get_or_404(day_id)
    if day.professional_id == current_user.id:
        db.session.delete(day)
        db.session.commit()
    return redirect(url_for('dashboard.index'))

@dashboard.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.professional_id == current_user.id:
        appointment.status = 'cancelado'
        db.session.commit()
    return redirect(url_for('dashboard.index'))

@dashboard.route('/export-csv')
@login_required
def export_csv():
    import csv
    from io import StringIO
    from flask import Response

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Hora', 'Paciente', 'Teléfono', 'Email', 'Notas', 'Estado'])

    appointments = Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    for apt in appointments:
        writer.writerow([
            apt.date.strftime('%d/%m/%Y'),
            apt.time.strftime('%H:%M'),
            apt.client_name,
            apt.client_phone,
            apt.client_email or '',
            apt.notes or '',
            apt.status
        ])

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=agenda.csv'}
    )
