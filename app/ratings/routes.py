from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from . import ratings
from ..models import db, Review, User, Job, Application


@ratings.route('/review/<username>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def leave_review(username, job_id):
    reviewee = User.query.filter_by(username=username).first_or_404()
    job = Job.query.get_or_404(job_id)

    if reviewee.id == current_user.id:
        flash('You cannot review yourself.', 'warning')
        return redirect(url_for('main.profile', username=username))

    # Check eligibility: job must be completed and user must be involved
    if job.status not in ('completed',):
        flash('Reviews can only be left for completed jobs.', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

    # Only poster can review freelancer and vice versa
    involved = (job.poster_id == current_user.id and job.accepted_applicant_id == reviewee.id) or \
               (job.accepted_applicant_id == current_user.id and job.poster_id == reviewee.id)
    if not involved:
        abort(403)

    existing = Review.query.filter_by(
        reviewer_id=current_user.id, reviewee_id=reviewee.id, job_id=job_id
    ).first()
    if existing:
        flash('You have already reviewed this person for this job.', 'warning')
        return redirect(url_for('main.profile', username=username))

    if request.method == 'POST':
        rating_val = request.form.get('rating', 0)
        comment = request.form.get('comment', '').strip()

        try:
            rating_val = int(rating_val)
            if not 1 <= rating_val <= 5:
                raise ValueError
        except ValueError:
            flash('Please select a rating between 1 and 5.', 'danger')
            return render_template('ratings/leave_review.html', reviewee=reviewee, job=job)

        review = Review(reviewer_id=current_user.id, reviewee_id=reviewee.id,
                        job_id=job_id, rating=rating_val, comment=comment)
        db.session.add(review)
        db.session.commit()
        # Update user's avg rating
        reviewee.update_avg_rating()
        db.session.commit()
        flash(f'Review submitted for {reviewee.username}! ⭐', 'success')
        return redirect(url_for('main.profile', username=username))

    return render_template('ratings/leave_review.html', reviewee=reviewee, job=job)
