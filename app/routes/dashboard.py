import io

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, timedelta, date
import calendar
import csv

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@login_required
def index():
    public_url = url_for('public.agenda', slug=current_user.slug, _external=True)
    
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    cal = calendar.Calendar()
    month_days = cal.itermonthdays2(year, month)
    enabled_dates = AvailableDay.query.filter_by(professional_id=current_user.id).all()
    enabled_map = {d.date: d for d in enabled_dates}
    
    calendar_data = []
    for day, weekday in month_days:
        if day == 0:
            calendar_data.append({'type': 'empty'})
        else:
            current_date = date(year, month, day)
            is_enabled = current_date in enabled_map
            is_past = current_date < date.today()
            calendar_data.append({
                'type': 'day', 'day': day, 'date': current_date,
                'is_enabled': is_enabled, 'is_past': is_past,
                'start': enabled_map.get(current_date).start_time if is_enabled else None,
                'end': enabled_map.get(current_date).end_time if is_enabled else None
            })

    hoy = date.today()
    turnos_hoy = Appointment.query.filter_by(professional_id=current_user.id, status='reservado')\
        .filter(Appointment.date == hoy).order_by(Appointment.time).all()
    proximos = Appointment.query.filter_by(professional_id=current_user.id, status='reservado')\
        .filter(Appointment.date > hoy).order_by(Appointment.date, Appointment.time).limit(10).all()
    
    month_name = datetime(year, month, 1).strftime("%B").capitalize()

    return render_template('dashboard/index.html', 
                           turnos_hoy=turnos_hoy, proximos=proximos,
                           public_url=public_url,
                           calendar_data=calendar_data, 
                           year=year, month=month, month_name=month_name)

@dashboard.route('/settings', methods=['POST'])
@login_required
def settings():
    duration = request.form.get('duration')
    if duration:
        current_user.appointment_duration = int(duration)
        db.session.commit()
        flash('Duración actualizada.')
    return redirect(url_for('dashboard.index'))

# NUEVO: Exportar CSV
@dashboard.route('/export')
@login_required
def export_csv():
    turnos = Appointment.query.filter_by(professional_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    def generate():
        data = [['Fecha', 'Hora', 'Cliente', 'Telefono', 'Notas', 'Estado']]
        for t in turnos:
            data.append([t.date, t.time, t.client_name, t.client_phone, t.notes or '', t.status])
        
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerows(data)
        return si.getvalue()

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=turnos.csv"}
    )

# NUEVO: Cancelar Turno
@dashboard.route('/cancel/<int:id>')
@login_required
def cancel_appointment(id):
    turno = Appointment.query.get_or_404(id)
    if turno.professional_id == current_user.id:
        turno.status = 'cancelado'
        db.session.commit()
        flash('Turno cancelado. El horario quedó libre para nuevos pacientes.')
    return redirect(url_for('dashboard.index'))

@dashboard.route('/save_day', methods=['POST'])
@login_required
def save_day():
    data = request.get_json()
    date_obj = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    start_obj = datetime.strptime(data.get('start_time'), '%H:%M').time()
    end_obj = datetime.strptime(data.get('end_time'), '%H:%M').time()
    
    avail = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
    if avail:
        avail.start_time = start_obj
        avail.end_time = end_obj
    else:
        new_avail = AvailableDay(professional_id=current_user.id, date=date_obj, start_time=start_obj, end_time=end_obj)
        db.session.add(new_avail)
    db.session.commit()
    return jsonify({'status': 'success'})

@dashboard.route('/delete_day', methods=['POST'])
@login_required
def delete_day():
    date_obj = datetime.strptime(request.get_json().get('date'), '%Y-%m-%d').date()
    avail = AvailableDay.query.filter_by(professional_id=current_user.id, date=date_obj).first()
    if avail:
        db.session.delete(avail)
        db.session.commit()
    return jsonify({'status': 'success'})

@dashboard.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_pass = request.form.get('new_password')
    if new_pass and len(new_pass) >= 4:
        current_user.set_password(new_pass)
        db.session.commit()
        flash('Contraseña actualizada correctamente.')
    else:
        flash('La contraseña debe tener al menos 4 caracteres.')
    return redirect(url_for('dashboard.index'))
