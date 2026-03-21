from app import db

class TimeBlock(db.Model):
    __tablename__ = 'time_block'
    id = db.Column(db.Integer, primary_key=True)
    available_day_id = db.Column(db.Integer, db.ForeignKey('available_day.id'), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # Formato "HH:MM"
    duration = db.Column(db.Integer, default=30)         # Minutos
    is_public = db.Column(db.Boolean, default=True)      # Visible en agenda

    # Relación inversa (opcional pero útil)
    day = db.relationship('AvailableDay', backref='blocks')

    def __repr__(self):
        return f'<Block {self.start_time} ({self.duration}m)>'
