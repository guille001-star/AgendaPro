from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from app.models.time_block import TimeBlock
from datetime import datetime, date, time as dt_time, timedelta
import mercadopago

public = Blueprint('public', __name__)

@public.route('/')
def home(): return redirect(url_for('auth.login'))

@public.route('/directorio')
def lista():
    users = User.query.all()
    return render_template('public/lista.html', users=users)

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        date_str = request.form['date']
        time_str = request.form['time_slot']
        client_name = request.form['name']
        client_email = request.form.get('email')
        client_phone = request.form.get('phone')
        try:
            apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            apt_time = datetime.strptime(time_str, '%H:%M').time()
        except:
            flash('Error en datos.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))
        day = AvailableDay.query.filter_by(professional_id=professional.id, date=apt_date).first()
        if not day:
            flash('Dia no disponible.', 'danger')
            return redirect(url_for('public.agenda', slug=slug))
        requiere_pago = professional.appointment_price and professional.appointment_price > 0 and professional.mp_access_token
        status = 'pendiente' if requiere_pago else 'reservado'
        new_apt = Appointment(professional_id=professional.id, date=apt_date, time=apt_time, client_name=client_name, client_email=client_email, client_phone=client_phone, status=status)
        db.session.add(new_apt); db.session.commit()
        
        if requiere_pago:
            try:
                sdk = mercadopago.SDK(professional.mp_access_token)
                base_url = request.host_url.rstrip('/')
                preference_data = {"items": [{"title": f"Turno {professional.name} - {apt_date}", "quantity": 1, "currency_id": "ARS", "unit_price": float(professional.appointment_price)}], "payer": {"email": client_email}, "back_urls": {"success": f"{base_url}/pago/exito", "failure": f"{base_url}/pago/error"}, "auto_return": "approved", "external_reference": str(new_apt.id)}
                pref_response = sdk.preference().create(preference_data)
                pay_url = pref_response["response"].get("init_point") or pref_response["response"].get("sandbox_init_point")
                if pay_url: return redirect(pay_url)
                flash('Error MP.', 'danger')
                db.session.delete(new_apt); db.session.commit()
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
                db.session.delete(new_apt); db.session.commit()
        
        # CAMBIO: Mostramos confirmacion directa
        return render_template('public/confirmacion.html', professional=professional, date=apt_date, time=apt_time, client_name=client_name)

    today_utc = datetime.utcnow()
    today_argentina = (today_utc - timedelta(hours=3)).date()
    enabled_days = AvailableDay.query.filter(AvailableDay.professional_id == professional.id, AvailableDay.date >= today_argentina).order_by(AvailableDay.date).all()
    enabled_dates = [d.date for d in enabled_days]
    return render_template('public/agenda.html', professional=professional, enabled_dates=enabled_dates)

# --- API HORARIOS ---
@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'slots': []}), 404
    try: d = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'slots': []}), 400
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=d).first()
    if not day: return jsonify({'slots': []})

    apps = Appointment.query.filter_by(professional_id=professional.id, date=d).filter(Appointment.status.in_(['reservado', 'pendiente'])).all()
    booked = [a.time for a in apps]
    slots = []

    blocks = TimeBlock.query.filter_by(available_day_id=day.id).order_by(TimeBlock.start_time).all()
    if blocks:
        for b in blocks:
            if b.is_public:
                try:
                    t = datetime.strptime(b.start_time, '%H:%M').time()
                    if t not in booked: slots.append(b.start_time)
                except: pass
    else:
        start = day.start_time or dt_time(9,0)
        end = day.end_time or dt_time(18,0)
        dur = day.slot_duration or 30
        curr = datetime.combine(d, start)
        end_dt = datetime.combine(d, end)
        while curr < end_dt:
            if curr.time() not in booked: slots.append(curr.time().strftime('%H:%M'))
            curr += timedelta(minutes=dur)
    return jsonify({'slots': slots})

@public.route('/pago/exito')
def pago_exito():
    ref = request.args.get('external_reference')
    if ref:
        try:
            apt = Appointment.query.get(int(ref))
            if apt and apt.status == 'pendiente':
                apt.status = 'reservado'; db.session.commit()
                prof = User.query.get(apt.professional_id)
                # CAMBIO: Usamos plantilla unificada
                return render_template('public/confirmacion.html', professional=prof, date=apt.date, time=apt.time, client_name=apt.client_name)
        except: pass
    flash('Pago recibido.', 'success')
    return redirect(url_for('public.home'))

@public.route('/pago/error')
def pago_error():
    flash('El pago fue rechazado.', 'danger')
    return redirect(url_for('public.home'))
