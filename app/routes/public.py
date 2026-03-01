from flask import Blueprint, render_template_string, request, redirect, url_for, flash, jsonify
from app import db
from app.models.user import User
from app.models.appointment import Appointment
from app.models.available_day import AvailableDay
from datetime import datetime, date, time as dt_time, timedelta

public = Blueprint('public', __name__)

TPL_AGENDA = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Agenda</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 min-h-screen">
<div class="bg-white shadow p-6 text-center max-w-4xl mx-auto"><h1 class="text-2xl font-bold">{{ professional.name }}</h1><p class="text-gray-500 text-sm mt-1">Seleccione dia.</p></div>
<div class="max-w-4xl mx-auto p-6 grid md:grid-cols-2 gap-6">
<div class="bg-white p-6 rounded-xl shadow-lg">
<h2 class="font-bold mb-4">Fechas</h2>
<div class="grid grid-cols-7 gap-1" id="calendar-container">
{% for day in enabled_dates %}
<div onclick="selectDate('{{ day }}')" class="cursor-pointer p-2 rounded text-center text-sm font-medium bg-gray-100 hover:bg-indigo-100" id="day-{{ day }}">{{ day.day }}</div>
{% else %}<p class="col-span-7 text-center text-gray-400 py-4">No hay fechas.</p>{% endfor %}
</div>
<form id="booking-form" method="POST" class="hidden mt-6"><input type="hidden" name="date" id="input-date"><input type="hidden" name="time_slot" id="input-time">
<div class="mb-4"><label class="block font-bold mb-2">Horario:</label><div id="slots-container" class="grid grid-cols-4 gap-2"></div></div>
<div class="border-t pt-4">
<h2 class="font-bold mb-2">Datos</h2>
<input type="text" name="name" placeholder="Nombre" required class="w-full border p-2 rounded mb-2">
<input type="email" name="email" placeholder="Email" required class="w-full border p-2 rounded mb-2">
<input type="tel" name="phone" placeholder="Telefono" required class="w-full border p-2 rounded mb-4">
<button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded">Reservar</button>
</div></form></div>
<div class="bg-white p-6 rounded-xl shadow-lg text-center"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ request.host_url }}agenda/{{ professional.slug }}" class="mx-auto rounded mb-4"></div>
</div>
<script>
function selectDate(dateStr) {
document.querySelectorAll('#calendar-container div').forEach(el => el.classList.remove('bg-indigo-500', 'text-white'));
document.getElementById('day-'+dateStr).classList.add('bg-indigo-500', 'text-white');
document.getElementById('input-date').value = dateStr; document.getElementById('booking-form').classList.remove('hidden');
fetch(`/agenda/get-slots/{{ professional.slug }}/${dateStr}`).then(r=>r.json()).then(data => {
const c = document.getElementById('slots-container'); c.innerHTML = '';
if(data.slots){ data.slots.forEach(s => { const b = document.createElement('button'); b.type='button'; b.innerText=s; b.className='p-2 border rounded hover:bg-gray-100'; b.onclick=()=>selectSlot(s,b); c.appendChild(b); }); }
else { c.innerHTML = '<p class="col-span-4 text-gray-400 text-sm">No hay turnos.</p>'; }
});
}
function selectSlot(time, btn) {
document.querySelectorAll('#slots-container button').forEach(el => el.classList.remove('bg-indigo-500', 'text-white'));
btn.classList.add('bg-indigo-500', 'text-white');
document.getElementById('input-time').value = time;
}
</script>
</body></html>
"""

@public.route('/')
def home(): return redirect(url_for('auth.login'))

@public.route('/agenda/<slug>', methods=['GET', 'POST'])
def agenda(slug):
    professional = User.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        try:
            apt_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            apt_time = datetime.strptime(request.form['time_slot'], '%H:%M').time()
            new_apt = Appointment(professional_id=professional.id, date=apt_date, time=apt_time, client_name=request.form['name'], client_email=request.form.get('email'), client_phone=request.form.get('phone'), status='reservado')
            db.session.add(new_apt); db.session.commit()
            flash('Reservado', 'success')
        except: flash('Error', 'danger')
        return redirect(url_for('public.agenda', slug=slug))
    today = date.today()
    enabled = AvailableDay.query.filter(AvailableDay.professional_id == professional.id, AvailableDay.date >= today).order_by(AvailableDay.date).all()
    return render_template_string(TPL_AGENDA, professional=professional, enabled_dates=enabled)

@public.route('/agenda/get-slots/<slug>/<date_str>')
def get_slots(slug, date_str):
    professional = User.query.filter_by(slug=slug).first()
    if not professional: return jsonify({'error': 'No'}), 404
    try: selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'error': 'Fecha'}), 400
    day = AvailableDay.query.filter_by(professional_id=professional.id, date=selected_date).first()
    if not day: return jsonify({'message': 'No habilitado.'})
    
    start_time = day.start_time if day.start_time else dt_time(9, 0)
    end_time = day.end_time if day.end_time else dt_time(18, 0)
    
    appointments = Appointment.query.filter_by(professional_id=professional.id, date=selected_date, status='reservado').all()
    booked = [a.time for a in appointments]
    slots = []
    curr = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)
    while curr < end:
        if curr.time() not in booked: slots.append(curr.time().strftime('%H:%M'))
        curr += timedelta(minutes=30)
    return jsonify({'slots': slots})
