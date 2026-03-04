from flask import Blueprint

jobs = Blueprint('jobs', __name__, template_folder='../templates/jobs')

from . import routes  # noqa
