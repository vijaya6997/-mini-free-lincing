import os
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import main
from ..models import db, User, Job, Application, Message, Review, JOB_CATEGORIES


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@main.route('/')
def index():
    recent_jobs = Job.query.filter_by(status='open').order_by(Job.created_at.desc()).limit(6).all()
    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_completed = Job.query.filter_by(status='completed').count()
    top_freelancers = User.query.filter(User.rating_count > 0)\
        .order_by(User.avg_rating.desc()).limit(4).all()
    return render_template('index.html', recent_jobs=recent_jobs, categories=JOB_CATEGORIES,
                           total_users=total_users, total_jobs=total_jobs,
                           total_completed=total_completed, top_freelancers=top_freelancers)


@main.route('/dashboard')
@login_required
def dashboard():
    posted_jobs = current_user.jobs_posted.order_by(Job.created_at.desc()).limit(5).all()
    my_apps = Application.query.filter_by(applicant_id=current_user.id)\
        .order_by(Application.created_at.desc()).limit(5).all()
    unread_count = current_user.unread_messages_count()
    recent_reviews = Review.query.filter_by(reviewee_id=current_user.id)\
        .order_by(Review.created_at.desc()).limit(3).all()
    open_jobs_count = current_user.jobs_posted.filter_by(status='open').count()
    active_jobs_count = current_user.jobs_posted.filter_by(status='in_progress').count()
    completed_jobs = current_user.jobs_posted.filter_by(status='completed').count()
    apps_pending = Application.query.filter_by(applicant_id=current_user.id, status='pending').count()
    apps_accepted = Application.query.filter_by(applicant_id=current_user.id, status='accepted').count()
    return render_template('dashboard.html',
                           posted_jobs=posted_jobs, my_apps=my_apps,
                           unread_count=unread_count, recent_reviews=recent_reviews,
                           open_jobs_count=open_jobs_count, active_jobs_count=active_jobs_count,
                           completed_jobs=completed_jobs, apps_pending=apps_pending,
                           apps_accepted=apps_accepted)


@main.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posted_jobs = user.jobs_posted.order_by(Job.created_at.desc()).limit(6).all()
    reviews = user.reviews_received.order_by(Review.created_at.desc()).all()
    can_message = current_user.is_authenticated and current_user.id != user.id
    return render_template('profile/profile.html', user=user, posted_jobs=posted_jobs,
                           reviews=reviews, can_message=can_message)


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        location = request.form.get('location', '').strip()
        skills = request.form.get('skills', '').strip()

        current_user.full_name = full_name
        current_user.bio = bio
        current_user.location = location
        current_user.skills = skills

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                current_user.profile_pic = filename

        db.session.commit()
        flash('Profile updated successfully! ✅', 'success')
        return redirect(url_for('main.profile', username=current_user.username))

    return render_template('profile/edit_profile.html')


@main.route('/my-jobs')
@login_required
def my_jobs():
    posted = current_user.jobs_posted.order_by(Job.created_at.desc()).all()
    return render_template('jobs/my_jobs.html', jobs=posted)


@main.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403
