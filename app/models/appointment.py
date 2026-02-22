from app import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=True) # NUEVO CAMPO
    client_phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='reservado')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
