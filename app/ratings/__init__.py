from flask import Blueprint

ratings = Blueprint('ratings', __name__, template_folder='../templates/ratings')

from . import routes  # noqa
