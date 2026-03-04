from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from . import jobs
from ..models import db, Job, Application, User, JOB_CATEGORIES, Review


@jobs.route('/')
def list_jobs():
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    min_budget = request.args.get('min_budget', '')
    max_budget = request.args.get('max_budget', '')

    query = Job.query.filter_by(status='open')

    if q:
        query = query.filter(
            Job.title.ilike(f'%{q}%') | Job.description.ilike(f'%{q}%')
        )
    if category:
        query = query.filter_by(category=category)
    if min_budget:
        try:
            query = query.filter(Job.budget >= float(min_budget))
        except ValueError:
            pass
    if max_budget:
        try:
            query = query.filter(Job.budget <= float(max_budget))
        except ValueError:
            pass

    if sort == 'budget_high':
        query = query.order_by(Job.budget.desc())
    elif sort == 'budget_low':
        query = query.order_by(Job.budget.asc())
    else:
        query = query.order_by(Job.created_at.desc())

    all_jobs = query.all()
    return render_template('jobs/jobs.html', jobs=all_jobs, categories=JOB_CATEGORIES,
                           q=q, selected_category=category, sort=sort,
                           min_budget=min_budget, max_budget=max_budget)


@jobs.route('/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    user_application = None
    if current_user.is_authenticated:
        user_application = Application.query.filter_by(
            job_id=job_id, applicant_id=current_user.id
        ).first()
    applications = job.applications.order_by(Application.created_at.desc()).all() \
        if current_user.is_authenticated and current_user.id == job.poster_id else []
    return render_template('jobs/job_detail.html', job=job,
                           user_application=user_application,
                           applications=applications)


@jobs.route('/new', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        budget = request.form.get('budget', '0')
        location = request.form.get('location', '').strip()

        error = None
        if not title or not description or not category:
            error = 'Title, description, and category are required.'
        elif len(title) < 5:
            error = 'Title must be at least 5 characters.'

        try:
            budget_val = float(budget)
            if budget_val <= 0:
                error = 'Budget must be a positive number.'
        except ValueError:
            error = 'Invalid budget value.'
            budget_val = 0

        if error:
            flash(error, 'danger')
        else:
            job = Job(title=title, description=description, category=category,
                      budget=budget_val, location=location, poster_id=current_user.id)
            db.session.add(job)
            db.session.commit()
            flash('Job posted successfully! 🎯', 'success')
            return redirect(url_for('jobs.job_detail', job_id=job.id))

    return render_template('jobs/post_job.html', categories=JOB_CATEGORIES)


@jobs.route('/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.poster_id == current_user.id:
        flash('You cannot apply to your own job.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    if job.status != 'open':
        flash('This job is no longer accepting applications.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    existing = Application.query.filter_by(job_id=job_id, applicant_id=current_user.id).first()
    if existing:
        flash('You have already applied to this job.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    cover_letter = request.form.get('cover_letter', '').strip()
    proposed_budget = request.form.get('proposed_budget', '')

    if not cover_letter or len(cover_letter) < 20:
        flash('Cover letter must be at least 20 characters.', 'danger')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    try:
        pb = float(proposed_budget) if proposed_budget else None
    except ValueError:
        pb = None

    app_obj = Application(job_id=job_id, applicant_id=current_user.id,
                          cover_letter=cover_letter, proposed_budget=pb)
    db.session.add(app_obj)
    db.session.commit()
    flash('Application submitted successfully! ✅', 'success')
    return redirect(url_for('jobs.job_detail', job_id=job_id))


@jobs.route('/<int:job_id>/application/<int:app_id>/status', methods=['POST'])
@login_required
def update_application_status(job_id, app_id):
    job = Job.query.get_or_404(job_id)
    if job.poster_id != current_user.id:
        abort(403)

    application = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')

    if new_status not in ('accepted', 'rejected', 'pending'):
        flash('Invalid status.', 'danger')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    application.status = new_status
    if new_status == 'accepted':
        # Reject all other applications
        other_apps = Application.query.filter(
            Application.job_id == job_id,
            Application.id != app_id
        ).all()
        for a in other_apps:
            a.status = 'rejected'
        job.status = 'in_progress'
        job.accepted_applicant_id = application.applicant_id
        flash(f'Application accepted! Job is now in progress. ✅', 'success')
    elif new_status == 'rejected':
        flash('Application rejected.', 'info')
    else:
        flash('Application status updated.', 'info')

    db.session.commit()
    return redirect(url_for('jobs.job_detail', job_id=job_id))


@jobs.route('/<int:job_id>/complete', methods=['POST'])
@login_required
def complete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.poster_id != current_user.id:
        abort(403)
    if job.status != 'in_progress':
        flash('Job is not in progress.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    job.status = 'completed'
    db.session.commit()
    flash('Job marked as completed! 🎉 You can now leave a review.', 'success')
    return redirect(url_for('jobs.job_detail', job_id=job_id))


@jobs.route('/<int:job_id>/close', methods=['POST'])
@login_required
def close_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.poster_id != current_user.id:
        abort(403)
    job.status = 'closed'
    db.session.commit()
    flash('Job closed.', 'info')
    return redirect(url_for('jobs.job_detail', job_id=job_id))


@jobs.route('/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.poster_id != current_user.id:
        abort(403)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully.', 'info')
    return redirect(url_for('main.my_jobs'))


@jobs.route('/my-jobs')
@login_required
def my_jobs():
    posted = current_user.jobs_posted.order_by(Job.created_at.desc()).all()
    return render_template('jobs/my_jobs.html', jobs=posted)


@jobs.route('/my-applications')
@login_required
def my_applications():
    apps = Application.query.filter_by(applicant_id=current_user.id)\
        .order_by(Application.created_at.desc()).all()
    return render_template('jobs/my_applications.html', applications=apps)
