from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from . import messages
from ..models import db, Message, User


@messages.route('/')
@login_required
def inbox():
    # Get distinct conversations (partner users)
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)

    partner_ids = set()
    for (uid,) in sent.all():
        partner_ids.add(uid)
    for (uid,) in received.all():
        partner_ids.add(uid)

    conversations = []
    for uid in partner_ids:
        partner = User.query.get(uid)
        if not partner:
            continue
        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.timestamp.desc()).first()
        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()
        conversations.append({'partner': partner, 'last_msg': last_msg, 'unread': unread_count})

    conversations.sort(key=lambda x: x['last_msg'].timestamp, reverse=True)
    return render_template('messages/inbox.html', conversations=conversations)


@messages.route('/<username>', methods=['GET', 'POST'])
@login_required
def conversation(username):
    partner = User.query.filter_by(username=username).first_or_404()

    if partner.id == current_user.id:
        flash('You cannot message yourself.', 'warning')
        return redirect(url_for('messages.inbox'))

    if request.method == 'POST':
        body = request.form.get('body', '').strip()
        if not body:
            flash('Message cannot be empty.', 'danger')
        elif len(body) > 2000:
            flash('Message too long (max 2000 characters).', 'danger')
        else:
            msg = Message(sender_id=current_user.id, receiver_id=partner.id, body=body)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('messages.conversation', username=username))

    # Mark received messages as read
    Message.query.filter_by(
        sender_id=partner.id, receiver_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()

    thread = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == partner.id),
            and_(Message.sender_id == partner.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    return render_template('messages/conversation.html', partner=partner, thread=thread)
