from app import db
class TimeBlock(db.Model):
    __tablename__ = 'time_block'
    id = db.Column(db.Integer, primary_key=True)
    available_day_id = db.Column(db.Integer, db.ForeignKey('available_day.id'), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    duration = db.Column(db.Integer, default=30)
    is_public = db.Column(db.Boolean, default=True)
    day = db.relationship('AvailableDay', backref='blocks')
