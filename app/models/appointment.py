from app import db

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(20))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='reservado')
    notes = db.Column(db.Text)
    
    # ELIMINADOS: payment_id, etc.

    def __repr__(self):
        return f'<Appointment {self.date} {self.time}>'
