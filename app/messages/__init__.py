from flask import Blueprint

messages = Blueprint('messages', __name__, template_folder='../templates/messages')

from . import routes  # noqa
