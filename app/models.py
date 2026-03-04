from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), default='')
    bio = db.Column(db.Text, default='')
    location = db.Column(db.String(100), default='')
    skills = db.Column(db.String(500), default='')
    profile_pic = db.Column(db.String(200), default='default.png')
    avg_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    is_active_flag = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    jobs_posted = db.relationship('Job', backref='poster', lazy='dynamic',
                                  foreign_keys='Job.poster_id', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='applicant', lazy='dynamic',
                                   foreign_keys='Application.applicant_id')
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic',
                                    foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy='dynamic',
                                        foreign_keys='Message.receiver_id')
    reviews_given = db.relationship('Review', backref='reviewer', lazy='dynamic',
                                    foreign_keys='Review.reviewer_id')
    reviews_received = db.relationship('Review', backref='reviewee', lazy='dynamic',
                                       foreign_keys='Review.reviewee_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_avg_rating(self):
        reviews = self.reviews_received.all()
        if reviews:
            self.avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
            self.rating_count = len(reviews)
        else:
            self.avg_rating = 0.0
            self.rating_count = 0

    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()] if self.skills else []

    def unread_messages_count(self):
        return self.messages_received.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.username}>'


JOB_CATEGORIES = [
    'Web Development', 'Graphic Design', 'Writing & Content',
    'Data Entry', 'Home Services', 'Teaching & Tutoring',
    'Photography', 'Delivery & Errands', 'Cooking & Catering',
    'Repair & Maintenance', 'Marketing', 'Translation',
    'Handcraft & Art', 'Fitness & Wellness', 'Other'
]


class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), default='')
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, closed
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accepted_applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='job', lazy='dynamic',
                                   cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='job', lazy='dynamic')
    accepted_applicant = db.relationship('User', foreign_keys=[accepted_applicant_id])

    def application_count(self):
        return self.applications.count()

    def user_has_applied(self, user_id):
        return self.applications.filter_by(applicant_id=user_id).first() is not None

    def __repr__(self):
        return f'<Job {self.title}>'


class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    proposed_budget = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Application job={self.job_id} user={self.applicant_id}>'


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Message from={self.sender_id} to={self.receiver_id}>'


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.rating}★ by={self.reviewer_id} for={self.reviewee_id}>'
