class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_name = db.Column(db.String(120), nullable=False)
    feedback_type = db.Column(db.String(20), nullable=False)  # e.g., 'like', 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))
